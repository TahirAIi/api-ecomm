from pydantic import BaseModel
from typing import Optional
from pydantic import Field


class PriceExtractionResult(BaseModel):
    cleaned_query: str = Field(
        description="The search query with price-related phrases removed, preserving semantic intent."
    )
    min_price: Optional[float] = Field(
        default=None,
        description="Minimum price constraint if mentioned (e.g., 'over 2000', 'above 1000'). Null if not specified.",
    )
    max_price: Optional[float] = Field(
        default=None,
        description="Maximum price constraint if mentioned (e.g., 'under 500', 'below 1000'). Null if not specified.",
    )
