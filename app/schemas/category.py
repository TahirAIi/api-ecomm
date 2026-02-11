from typing import Optional
from pydantic import BaseModel, UUID4
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryInDBBase(CategoryBase):
    uuid: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {UUID4: str}


class Category(CategoryInDBBase):
    pass
