from typing import List
from sqlalchemy.orm import Session
from app.repositories.category import category_repository
from app.models.category import Category as CategoryModel
from app.schemas.category import Category


class CategoryService:
    def __init__(self) -> None:
        self.repository = category_repository
        self.model = CategoryModel

    def get_all(self, db: Session) -> List[Category]:
        return self.repository.get_all(db=db)


def get_category_service() -> CategoryService:
    return CategoryService()
