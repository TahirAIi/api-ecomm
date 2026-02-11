from sqlalchemy import Column, SmallInteger, String, Float, Integer
from sqlalchemy.orm import relationship
from app.db.base_class import Base

from app.models.product_image import ProductImage


class Product(Base):
    __tablename__ = "products"

    EMBEDDING_STATUS_PENDING = 0
    EMBEDDING_STATUS_GENERATED = 1
    EMBEDDING_STATUS_FAILED = 2

    name = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)
    embedding_status = Column(
        SmallInteger, nullable=False, default=EMBEDDING_STATUS_PENDING
    )

    images = relationship("ProductImage", back_populates="product")

    categories = relationship(
        "Category", secondary="product_categories", back_populates="products"
    )
