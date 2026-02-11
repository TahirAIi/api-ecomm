from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class ProductImage(Base):
    __tablename__ = "product_images"

    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    image_url = Column(String, nullable=False)

    product = relationship("Product", back_populates="images")
