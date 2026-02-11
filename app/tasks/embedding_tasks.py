from uuid import UUID
from celery import Task
from sqlalchemy.orm import Session
from app.celery_worker import celery
from app.db.session import SessionLocal
from app.services.embedding import GeminiEmbeddingService
from app.services.vector_store import MilvusVectorStore
from app.core.config import settings
from app.models.product import Product
from app.repositories.product import product_repository
from app.utils.product_text import prepare_product_text
import logging

logger = logging.getLogger(__name__)


@celery.task(bind=True, name="generate_product_embedding")
def generate_product_embedding(self: Task, product_uuid: str) -> dict:
    db: Session = SessionLocal()
    try:
        product = product_repository.get_by_uuid(db, uuid=UUID(product_uuid))
        if not product:
            logger.error(f"Product not found: {product_uuid}")
            return {"status": "error", "message": f"Product {product_uuid} not found"}

        product_text = prepare_product_text(product)

        embedding_service = GeminiEmbeddingService()
        embedding = embedding_service.generate_embedding(product_text)

        vector_store = MilvusVectorStore()

        vector_store.insert_vectors(
            collection_name=settings.MILVUS_COLLECTION_NAME,
            vectors=[embedding],
            ids=[product.uuid],
            metadatas=[{"price": float(product.price)}],
        )

        product.version += 1
        product.embedding_status = Product.EMBEDDING_STATUS_GENERATED

        db.commit()

        logger.info(f"Successfully generated embedding for product {product_uuid}")
        return {
            "status": "success",
            "message": f"Embedding generated for product {product_uuid}",
            "version": product.version,
        }

    except Exception as e:
        logger.error(
            f"Error generating embedding for product {product_uuid}: {str(e)}",
            exc_info=True,
        )
        db.rollback()
        raise self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        db.close()
