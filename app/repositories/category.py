from typing import List
from sqlalchemy.orm import Session
from app.models.category import Category


class CategoryRepository:
    def __init__(self) -> None:
        self.model = Category

    def get_all(self, db: Session) -> List[Category]:
        return db.query(self.model).all()


category_repository = CategoryRepository()
