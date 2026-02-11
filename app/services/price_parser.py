from typing import Optional, Tuple
import re
import json
from openai import OpenAI
from app.schemas.price_extractor import PriceExtractionResult
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PriceConstraints:
    def __init__(
        self,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> None:
        self.min_price = min_price
        self.max_price = max_price


class PriceQueryParser:
    def __init__(self) -> None:
        self._client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
        )

    def parse(self, query: str) -> Tuple[str, PriceConstraints]:
        try:
            cleaned, constraints = self._parse_with_deepseek(query)
            return cleaned, constraints
        except Exception as e:
            logger.error(f"DeepSeek price parsing failed: {e}, falling back to regex")
        return self._parse_with_regex(query)

    def _parse_with_deepseek(self, query: str) -> Tuple[str, PriceConstraints]:
        prompt = f"""
You are a price extraction engine for an e-commerce search bar.

Task:
- Extract price constraints from the user query.
- Return ONLY a single JSON object that matches this schema:
  {json.dumps(PriceExtractionResult.model_json_schema(), indent=2)}

User query: "{query}"

Interpretation rules:
- Detect phrases like "under 500", "below 500", "less than 500" → max_price.
- Detect phrases like "over 2000", "above 2000", "more than 2000" → min_price.
- Detect ranges like "between 200 and 400" or "from 200 to 400" → min_price and max_price.
- Remove price-specific words and numbers from cleaned_query but keep the core intent.

If no price is mentioned:
- Set both min_price and max_price to null.
- cleaned_query should be the original query unchanged.
"""

        response = self._client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON-only price constraint extraction service.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        result = PriceExtractionResult.model_validate_json(content)

        constraints = PriceConstraints(
            min_price=result.min_price,
            max_price=result.max_price,
        )

        return result.cleaned_query.strip(), constraints

    def _parse_with_regex(self, query: str) -> Tuple[str, PriceConstraints]:
        text = query.lower()
        min_price: Optional[float] = None
        max_price: Optional[float] = None

        m = re.search(r"(between|from)\s+(\d+)\s+(and|to)\s+(\d+)", text)
        if m:
            min_price = float(m.group(2))
            max_price = float(m.group(4))
        else:
            m = re.search(r"(under|below|less than)\s+(\d+)", text)
            if m:
                max_price = float(m.group(2))
            m2 = re.search(r"(over|above|more than)\s+(\d+)", text)
            if m2:
                min_price = float(m2.group(2))

        constraints = PriceConstraints(min_price=min_price, max_price=max_price)

        cleaned = re.sub(
            r"(under|below|less than|over|above|more than|between|from)\s+\d+(\s+(and|to)\s+\d+)?",
            "",
            text,
        )
        cleaned = cleaned.strip()
        if not cleaned:
            cleaned = query

        return cleaned, constraints
