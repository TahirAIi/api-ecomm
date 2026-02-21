from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from app.services.embedding import GeminiEmbeddingService
from app.services.vector_store import MilvusVectorStore
from app.services.price_parser import PriceQueryParser, PriceConstraints
from app.core.config import settings
from app.models.product import Product
import logging

logger = logging.getLogger(__name__)


class SemanticSearchService:
    def __init__(
        self,
        embedding_service: GeminiEmbeddingService,
        vector_store: MilvusVectorStore,
        price_parser: PriceQueryParser,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.price_parser = price_parser

    def search(
        self,
        db: Session,
        query: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
    ) -> Tuple[List[dict], int]:
        if not self.vector_store.collection_exists(self.collection_name):
            logger.warning(
                f"Collection {self.collection_name} does not exist. No embeddings available."
            )
            return [], 0

        cleaned_query, price_constraints = self._parse_price_constraints(query)

        query_embedding = self._generate_query_embedding(cleaned_query)
        expr = self._build_price_expr(price_constraints)

        search_results = self.vector_store.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold,
            expr=expr,
        )

        if not search_results:
            return [], 0

        product_uuids = [result["id"] for result in search_results]
        products = (
            db.query(Product)
            .options(joinedload(Product.categories), joinedload(Product.images))
            .filter(Product.uuid.in_(product_uuids))
            .all()
        )

        product_map = {product.uuid: product for product in products}

        score_map = {result["id"]: result["score"] for result in search_results}

        ordered_products: List[dict] = []
        for result in search_results:
            product_uuid = result["id"]
            if product_uuid in product_map:
                ordered_products.append(
                    {
                        "product": product_map[product_uuid],
                        "score": score_map[product_uuid],
                    }
                )
        return ordered_products, len(ordered_products)

    def _generate_query_embedding(self, query: str) -> List[float]:
        return self.embedding_service.generate_query_embedding(query)

    def _parse_price_constraints(self, query: str) -> Tuple[str, PriceConstraints]:
        try:
            cleaned_query, constraints = self.price_parser.parse(query)
            return cleaned_query, constraints
        except Exception as e:
            logger.error(f"Error parsing price constraints: {e}", exc_info=True)
            return query, PriceConstraints()

    def _build_price_expr(self, constraints: PriceConstraints) -> Optional[str]:
        clauses = []
        if constraints.min_price is not None:
            clauses.append(f"price >= {constraints.min_price}")
        if constraints.max_price is not None:
            clauses.append(f"price <= {constraints.max_price}")

        if not clauses:
            return None
        return " and ".join(clauses)

    def ensure_collection_initialized(self) -> None:
        if not self.vector_store.collection_exists(self.collection_name):
            dimension = self.embedding_service.get_embedding_dimension()
            self.vector_store.initialize_collection(self.collection_name, dimension)
            logger.info(
                f"Initialized collection {self.collection_name} with dimension {dimension}"
            )


def get_semantic_search_service() -> SemanticSearchService:
    return SemanticSearchService(
        embedding_service=GeminiEmbeddingService(),
        vector_store=MilvusVectorStore(),
        price_parser=PriceQueryParser(),
    )
