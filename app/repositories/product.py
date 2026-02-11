from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from app.models.product import Product
from app.models.category import Category


class ProductRepository:
    def __init__(self) -> None:
        self.model = Product

    def get_by_uuid(self, db: Session, *, uuid: UUID) -> Optional[Product]:
        return db.query(self.model).filter(self.model.uuid == uuid).first()

    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> Product:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Product,
        obj_in: Union[Dict[str, Any], Product],
    ) -> Product:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, uuid: UUID) -> Product:
        obj = db.query(self.model).filter(self.model.uuid == uuid).first()
        db.delete(obj)
        db.commit()
        return obj

    def get_products_by_category(
        self,
        db: Session,
        *,
        category_name: str,
        skip: int = 0,
        limit: int = 20,
        sort_by: Optional[str] = None,
    ) -> Tuple[List[Product], int]:
        query = (
            db.query(Product)
            .join(Product.categories)
            .filter(Category.name == category_name)
        )

        # Apply sorting
        if sort_by:
            if sort_by == "price_asc":
                query = query.order_by(Product.price.asc())
            elif sort_by == "price_desc":
                query = query.order_by(Product.price.desc())
            elif sort_by == "newest":
                query = query.order_by(Product.created_at.desc())
            elif sort_by == "top_rated":
                query = query.order_by(Product.average_rating.desc())

        total = query.count()
        products = query.offset(skip).limit(limit).all()

        return products, total

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
        colors: Optional[List[str]] = None,
        sizes: Optional[List[str]] = None,
        in_stock: Optional[bool] = None,
    ) -> Tuple[List[Product], int]:
        query = db.query(self.model)

        # Apply filters
        if name:
            query = query.filter(self.model.name.ilike(f"%{name}%"))
        if category:
            query = query.join(self.model.categories).filter(Category.name == category)
        if min_price is not None:
            query = query.filter(self.model.price >= min_price)
        if max_price is not None:
            query = query.filter(self.model.price <= max_price)
        if colors:
            query = query.filter(self.model.colors.contains(colors))
        if sizes:
            query = query.filter(self.model.sizes.contains(sizes))
        if in_stock:
            query = query.filter(self.model.stock_quantity > 0)

        # Apply sorting
        if sort_by == "price_asc":
            query = query.order_by(self.model.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(self.model.price.desc())
        elif sort_by == "newest":
            query = query.order_by(self.model.created_at.desc())
        elif sort_by == "top_rated":
            query = query.order_by(self.model.rating.desc())

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        query = query.offset(skip).limit(limit)

        return query.all(), total


product_repository = ProductRepository()
