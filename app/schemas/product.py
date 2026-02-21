from typing import List, Optional
from pydantic import BaseModel, UUID4, Field
from datetime import datetime


class CategoryInProduct(BaseModel):
    uuid: UUID4
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {UUID4: str}


class ProductImage(BaseModel):
    image_url: str

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)
    images: Optional[List[ProductImage]] = None


class ProductCreate(ProductBase):
    category_uuids: List[UUID4]


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    images: Optional[List[ProductImage]] = None
    category_uuids: Optional[List[UUID4]] = None


class ProductInDBBase(ProductBase):
    uuid: UUID4
    created_at: datetime
    updated_at: datetime
    categories: List[CategoryInProduct]

    class Config:
        from_attributes = True
        json_encoders = {UUID4: str}


class Product(ProductInDBBase):
    pass


class ProductList(BaseModel):
    total_products: int
    total_pages: int
    products: List[Product]
