from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.schemas.product import Product, ProductCreate, ProductUpdate, ProductList
from app.services.product import get_product_service
from uuid import UUID
import urllib.parse
from app.services.product import ProductService

router = APIRouter()


@router.get("/category/{category_name}", response_model=ProductList)
def get_products_by_category(
    category_name: str,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(
        None, regex="^(price_asc|price_desc|newest|top_rated)$"
    ),
    product_service: ProductService = Depends(get_product_service),
) -> Any:
    products, total = product_service.get_products_by_category(
        db,
        category_name=category_name,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
    )
    return {
        "total_products": total,
        "total_pages": (total + limit - 1) // limit,
        "products": products,
    }


@router.get("", response_model=ProductList)
def list_products(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    name: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    sort_by: Optional[str] = Query(
        None, regex="^(price_asc|price_desc|newest|top_rated)$"
    ),
    colors: Optional[List[str]] = Query(None),
    sizes: Optional[List[str]] = Query(None),
    in_stock: Optional[bool] = None,
    product_service: ProductService = Depends(get_product_service),
) -> Any:
    products, total = product_service.get_products(
        db,
        skip=skip,
        limit=limit,
        name=name,
        category=urllib.parse.unquote(category if category else ""),
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        colors=colors,
        sizes=sizes,
        in_stock=in_stock,
    )

    return {
        "total_products": total,
        "total_pages": (total + limit - 1) // limit,
        "products": products,
    }


@router.get("/{uuid}", response_model=Product)
def get_product(
    uuid: UUID,
    db: Session = Depends(get_db),
    product_service: ProductService = Depends(get_product_service),
) -> Any:
    product = product_service.get_by_uuid(db=db, uuid=uuid)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=Product)
def create_product(
    *,
    db: Session = Depends(get_db),
    product_in: ProductCreate,
    current_user: Any = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service)
) -> Any:
    product = product_service.create(db=db, obj_in=product_in)
    return product


@router.put("/{uuid}", response_model=Product)
def update_product(
    *,
    db: Session = Depends(get_db),
    uuid: UUID,
    product_in: ProductUpdate,
    current_user: Any = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service)
) -> Any:
    product = product_service.get_by_uuid(db=db, uuid=uuid)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product = product_service.update(db=db, uuid=uuid, obj_in=product_in)
    return product
