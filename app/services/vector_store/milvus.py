from typing import List, Dict, Optional
from uuid import UUID

from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)

from app.services.vector_store.base import VectorStore
from app.core.config import settings


EXPECTED_DIM = 768


def validate_vector(vec: List[float]) -> None:
    if len(vec) != EXPECTED_DIM:
        raise ValueError(
            f"Invalid embedding dimension: {len(vec)}. "
            f"Expected {EXPECTED_DIM} for gemini embeddings."
        )


class MilvusVectorStore(VectorStore):
    def __init__(self):
        self.collection_name = settings.MILVUS_COLLECTION_NAME

        connections.connect(
            alias="default",
            uri=settings.MILVUS_URI,
            token=settings.MILVUS_TOKEN,
        )

    def initialize_collection(self, collection_name: str, dimension: int) -> None:
        if utility.has_collection(collection_name):
            return

        if dimension != EXPECTED_DIM:
            raise ValueError(
                f"Collection dimension {dimension} does not match EXPECTED_DIM {EXPECTED_DIM}"
            )

        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                is_primary=True,
                max_length=100,
            ),
            FieldSchema(
                name="price",
                dtype=DataType.FLOAT,
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=dimension,
            ),
        ]

        schema = CollectionSchema(fields, description="Product embeddings with price")

        collection = Collection(name=collection_name, schema=schema)

        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 2048},
        }
        collection.create_index(field_name="embedding", index_params=index_params)

    def insert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        ids: List[UUID],
        metadatas: Optional[List[Dict]] = None,
    ) -> None:
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have the same length")

        if metadatas is None or len(metadatas) != len(vectors):
            raise ValueError("metadatas with 'price' is required for each vector")

        prices: List[float] = []
        for md in metadatas:
            if md is None or "price" not in md:
                raise ValueError("metadata must include 'price' for each vector")
            prices.append(float(md["price"]))

        for vec in vectors:
            validate_vector(vec)

        collection = Collection(collection_name)

        id_strings = [str(uid) for uid in ids]

        data = [id_strings, prices, vectors]

        collection.insert(data)
        collection.flush()

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        expr: Optional[str] = None,
    ) -> List[Dict]:
        validate_vector(query_vector)

        collection = Collection(collection_name)

        try:
            collection.load()
        except Exception:
            pass

        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 32},
        }

        search_kwargs: Dict = {
            "data": [query_vector],
            "anns_field": "embedding",
            "param": search_params,
            "limit": limit,
            "output_fields": ["id", "price"],
        }
        if expr:
            search_kwargs["expr"] = expr

        results = collection.search(**search_kwargs)

        formatted_results = []
        for hit in results[0]:
            if score_threshold is None or hit.score >= score_threshold:
                formatted_results.append(
                    {
                        "id": UUID(hit.id),
                        "score": hit.score,
                    }
                )

        return formatted_results

    def delete_vectors(
        self,
        collection_name: str,
        ids: List[UUID],
    ) -> None:
        if not ids:
            return

        collection = Collection(collection_name)

        id_strings = [str(uid) for uid in ids]

        expr = f"id in {id_strings}"
        collection.delete(expr=expr)
        collection.flush()

    def update_vector(
        self,
        collection_name: str,
        vector_id: UUID,
        vector: List[float],
        metadata: Optional[Dict] = None,
    ) -> None:
        validate_vector(vector)

        self.delete_vectors(collection_name, [vector_id])

        self.insert_vectors(
            collection_name=collection_name,
            vectors=[vector],
            ids=[vector_id],
            metadatas=[metadata] if metadata else None,
        )

    def collection_exists(self, collection_name: str) -> bool:
        return utility.has_collection(collection_name)
