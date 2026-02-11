from typing import List
from pydantic import BaseModel
from app.schemas.product import Product


class SearchResult(BaseModel):
    product: Product


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResult]

    class Config:
        from_attributes = True
