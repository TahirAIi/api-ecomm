from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.product import product_repository
from app.schemas.product import ProductCreate, ProductUpdate, Product
from app.models.product import Product as ProductModel
from app.models.category import Category as CategoryModel
from app.tasks.embedding_tasks import generate_product_embedding
from app.utils.product_text import prepare_product_text as prepare_product_text_util
import logging

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self) -> None:
        self.repository = product_repository
        self.model = ProductModel

    def get_by_uuid(self, db: Session, uuid: UUID) -> Optional[ProductModel]:
        return self.repository.get_by_uuid(db=db, uuid=uuid)

    def delete(self, db: Session, uuid: UUID) -> Optional[ProductModel]:
        return self.repository.delete(db=db, uuid=uuid)

    def get_products_by_category(
        self,
        db: Session,
        *,
        category_name: str,
        skip: int = 0,
        limit: int = 20,
        sort_by: Optional[str] = None,
    ) -> Tuple[List[ProductModel], int]:
        """
        Retrieve products by category name with pagination and optional sorting.
        """
        return self.repository.get_products_by_category(
            db,
            category_name=category_name,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
        )

    def get_products(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20,
        name: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: Optional[str] = None,
        in_stock: Optional[bool] = None,
    ) -> Tuple[List[ProductModel], int]:
        return self.repository.get_products(
            db,
            skip=skip,
            limit=limit,
            name=name,
            category=category,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            in_stock=in_stock,
        )

    def create(self, db: Session, *, obj_in: ProductCreate) -> ProductModel:
        """Create a new product with categories."""
        category_uuids = obj_in.category_uuids

        obj_dict = obj_in.model_dump(exclude={"category_uuids"})

        db_obj = ProductModel(**obj_dict)

        categories = (
            db.query(CategoryModel).filter(CategoryModel.uuid.in_(category_uuids)).all()
        )
        db_obj.categories = categories

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        try:
            generate_product_embedding.delay(db_obj.uuid)
            logger.info(
                f"Successfully queued embedding generation for product {db_obj.uuid}"
            )
        except Exception as e:
            logger.error(
                f"Failed to queue embedding generation for product {db_obj.uuid}: {str(e)}"
            )

        return db_obj

    def update(
        self, db: Session, *, uuid: UUID, obj_in: ProductUpdate
    ) -> Optional[ProductModel]:
        update_dict = obj_in.model_dump(exclude_unset=True, exclude={"category_uuids"})

        embedding_related_fields = {"name", "description", "price"}
        needs_embedding_update = any(
            field in update_dict for field in embedding_related_fields
        )

        db_obj = self.repository.get_by_uuid(db=db, uuid=uuid)
        if not db_obj:
            return None

        updated_product = self.repository.update(
            db=db,
            db_obj=db_obj,
            obj_in=obj_in,
        )
        if obj_in.category_uuids is not None:
            categories = (
                db.query(CategoryModel)
                .filter(CategoryModel.uuid.in_(obj_in.category_uuids))
                .all()
            )
            updated_product.categories = categories
            db.commit()
            db.refresh(updated_product)
            needs_embedding_update = True

        if needs_embedding_update:
            try:
                generate_product_embedding.delay(uuid)
                logger.info(
                    f"Successfully queued embedding regeneration for product {uuid}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to queue embedding regeneration for product {uuid}: {str(e)}"
                )

        return updated_product


def get_product_service() -> ProductService:
    return ProductService()
