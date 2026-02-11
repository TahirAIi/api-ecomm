from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )

    product = relationship("Product", overlaps="categories")
    category = relationship("Category", overlaps="categories")
