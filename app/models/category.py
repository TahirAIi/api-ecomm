from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models.product_category import ProductCategory


class Category(Base):
    __tablename__ = "categories"

    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)

    products = relationship(
        "Product",
        secondary="product_categories",
        back_populates="categories",
        overlaps="category,product",
    )
