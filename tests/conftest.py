import os
import sys
from types import ModuleType
from unittest.mock import MagicMock

# Set env vars BEFORE any app imports so Settings() doesn't fail
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("FIRST_SUPERUSER", "admin@test.com")
os.environ.setdefault("FIRST_SUPERUSER_PASSWORD", "testpassword")

# Stub out heavy third-party modules that are unavailable in the test env
_mock_modules = [
    "google.genai", "google.genai.types",
    "pymilvus",
    "openai",
    "redis",
]
for _mod_name in _mock_modules:
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = MagicMock()

# Patch PostgreSQL UUID column type to work with SQLite
import sqlalchemy
import sqlalchemy.dialects.postgresql
from sqlalchemy import String, TypeDecorator

class _SQLiteUUID(TypeDecorator):
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        import uuid as _uuid
        if value is not None:
            return _uuid.UUID(value)
        return value

# Monkey-patch before models are imported
sqlalchemy.dialects.postgresql.UUID = _SQLiteUUID

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.base_class import Base
from app.api.deps import get_db
from app.main import app
from app.services.user import UserService
from app.schemas.user import UserCreate
from app.core.security import create_access_token

# Import all models so Base.metadata knows about them
from app.models.user import User  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.product_category import ProductCategory  # noqa: F401
from app.models.product_image import ProductImage  # noqa: F401

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

# SQLite needs explicitly enabled foreign keys
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def regular_user(db):
    svc = UserService()
    user = svc.create(
        db,
        obj_in=UserCreate(email="user@test.com", password="password123", full_name="Test User"),
    )
    return user


@pytest.fixture()
def superuser(db):
    svc = UserService()
    user = svc.create(
        db,
        obj_in=UserCreate(email="admin@test.com", password="password123", full_name="Admin User"),
        is_superuser=True,
    )
    return user


@pytest.fixture()
def auth_headers_regular(regular_user):
    token = create_access_token(regular_user.uuid)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers_superuser(superuser):
    token = create_access_token(superuser.uuid)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def test_category(db):
    from app.models.category import Category as CategoryModel
    cat = CategoryModel(name="Electronics", description="Electronic products")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat
