from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.services.category import get_category_service
from app.schemas.category import Category
from app.services.category import CategoryService

router = APIRouter()


@router.get("/", response_model=List[Category])
def list_categories(
    db: Session = Depends(deps.get_db),
    category_service: CategoryService = Depends(get_category_service),
):
    return category_service.get_all(db=db)
