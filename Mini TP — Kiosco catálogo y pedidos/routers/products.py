from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from models.product_schemas import ProductRead, PaginatedProductResponse, ProductCreate, ProductUpdate
from repositories.product_repository import ProductRepository
from dependencies import get_product_repository
from models.common_schemas import ErrorResponse

router = APIRouter(prefix="/productos", tags=["Productos"])

@router.get("", response_model=PaginatedProductResponse)
async def list_products(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
    repo: ProductRepository = Depends(get_product_repository)
):
    items, total = await repo.get_all(offset=offset, limit=limit)
    return PaginatedProductResponse(items=items, total=total)

@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    repo: ProductRepository = Depends(get_product_repository)
):
    return await repo.create(product)

@router.patch("/{product_id}", response_model=ProductRead, responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}})
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    repo: ProductRepository = Depends(get_product_repository)
):
    try:
        updated = await repo.update(product_id, product_update)
        if not updated:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "PRODUCT_NOT_FOUND", "message": f"El producto con id {product_id} no existe."}}
            )
        return updated
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "INVALID_PRODUCT_DATA", "message": str(e)}}
        )
