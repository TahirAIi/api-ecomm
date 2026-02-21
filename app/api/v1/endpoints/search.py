from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.semantic_search import (
    SemanticSearchService,
    get_semantic_search_service,
)
from app.schemas.search import SearchResponse, SearchResult
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=SearchResponse)
def semantic_search(
    query: str = Query(..., min_length=1, description="Search query text"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    score_threshold: float = Query(
        None, ge=0.0, le=1.0, description="Minimum similarity score threshold"
    ),
    db: Session = Depends(get_db),
    semantic_search_service: SemanticSearchService = Depends(
        get_semantic_search_service
    ),
) -> Any:
    try:
        search_results, total = semantic_search_service.search(
            db=db, query=query, limit=limit, score_threshold=score_threshold
        )

        formatted_results = [
            SearchResult(
                product=result["product"],
                score=result["score"],
            )
            for result in search_results
        ]
        return SearchResponse(
            query=query, total_results=total, results=formatted_results
        )

    except Exception as e:
        logger.error(f"Error in semantic search endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed")
