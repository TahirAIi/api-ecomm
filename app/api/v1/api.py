from fastapi import APIRouter
from app.api.v1.endpoints import products, categories, auth, search

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
