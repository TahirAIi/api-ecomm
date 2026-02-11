from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.repositories.user import user_repository
from app.schemas.user import UserCreate, User
from app.models.user import User as UserModel


class UserService:
    def __init__(self) -> None:
        self.repository = user_repository
        self.model = UserModel

    def get_by_uuid(self, db: Session, uuid: UUID) -> Optional[UserModel]:
        return db.query(self.model).filter(self.model.uuid == uuid).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> UserModel:
        db_obj = UserModel(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[UserModel]:
        user = user_repository.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_email_taken(
        self, db: Session, email: str, exclude_uuid: Optional[UUID] = None
    ) -> bool:
        return user_repository.is_email_taken(
            db=db, email=email, exclude_uuid=exclude_uuid
        )

    def verify_user(self, db: Session, *, uuid: UUID) -> Optional[UserModel]:
        user = self.get_by_uuid(db=db, uuid=uuid)
        if user:
            user.is_verified = True
            db.commit()
            db.refresh(user)
        return user

    def update_password(self, db: Session, *, user: User, new_password: str) -> User:
        """
        Update user's password.
        """
        hashed_password = get_password_hash(new_password)
        db_obj = db.query(self.model).filter(self.model.uuid == user.uuid).first()
        db_obj.hashed_password = hashed_password
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


def get_user_service() -> UserService:
    return UserService()
