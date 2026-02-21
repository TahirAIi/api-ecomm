from typing import List
from sqlalchemy.orm import Session
from app.repositories.category import category_repository
from app.models.category import Category as CategoryModel
from app.schemas.category import Category, CategoryCreate


class CategoryService:
    def __init__(self) -> None:
        self.repository = category_repository
        self.model = CategoryModel

    def get_all(self, db: Session) -> List[Category]:
        return self.repository.get_all(db=db)

    def create(self, db: Session, *, obj_in: CategoryCreate) -> CategoryModel:
        db_obj = CategoryModel(name=obj_in.name, description=obj_in.description)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


def get_category_service() -> CategoryService:
    return CategoryService()
