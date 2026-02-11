from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from app.models.user import User


class UserRepository:
    def __init__(self) -> None:
        self.model = User

    def update(
        self,
        db: Session,
        *,
        db_obj: User,
        obj_in: Union[Dict[str, Any], User],
    ) -> User:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, uuid: UUID) -> User:
        obj = db.query(self.model).filter(self.model.uuid == uuid).first()
        db.delete(obj)
        db.commit()
        return obj

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(self.model).filter(self.model.email == email).first()

    def is_email_taken(
        self, db: Session, *, email: str, exclude_uuid: Optional[UUID] = None
    ) -> bool:
        query = db.query(self.model).filter(self.model.email == email)
        if exclude_uuid:
            query = query.filter(self.model.uuid != exclude_uuid)
        return db.query(query.exists()).scalar()


user_repository = UserRepository()
