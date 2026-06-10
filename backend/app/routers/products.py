import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.business import Business
from app.models.product import Product
from app.models.subscription import Subscription
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.common import APIResponse
from app.schemas.product import (
    AvailabilityRequest,
    CreateProductRequest,
    ProductOut,
    UpdateProductRequest,
)
from app.services.storage_service import upload_file

router = APIRouter(prefix="/products", tags=["products"])


async def _get_business(user: User, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.owner_id == user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="No business profile found")
    return business


async def _check_plan_limit(business: Business, db: AsyncSession) -> None:
    """Raise 403 if free plan and at product limit."""
    sub_result = await db.execute(
        select(Subscription).where(Subscription.business_id == business.id)
    )
    sub = sub_result.scalar_one_or_none()
    is_premium = sub.is_premium if sub else False

    if not is_premium:
        count_result = await db.execute(
            select(func.count()).where(Product.business_id == business.id)
        )
        count = count_result.scalar_one()
        if count >= settings.FREE_PLAN_MAX_PRODUCTS:
            raise HTTPException(
                status_code=403,
                detail=f"Free plan limited to {settings.FREE_PLAN_MAX_PRODUCTS} products. Upgrade to add more.",
            )


@router.get("", response_model=APIResponse[list[ProductOut]])
async def list_products(
    category_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    query = select(Product).where(Product.business_id == business.id).order_by(Product.sort_order)
    if category_id:
        query = query.where(Product.category_id == category_id)
    result = await db.execute(query)
    products = result.scalars().all()
    return APIResponse.ok([ProductOut.model_validate(p) for p in products])


@router.post("", response_model=APIResponse[ProductOut], status_code=status.HTTP_201_CREATED)
async def create_product(
    body: CreateProductRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    await _check_plan_limit(business, db)

    product = Product(business_id=business.id, **body.model_dump())
    db.add(product)
    await db.flush()
    return APIResponse.ok(ProductOut.model_validate(product))


@router.patch("/{product_id}", response_model=APIResponse[ProductOut])
async def update_product(
    product_id: uuid.UUID,
    body: UpdateProductRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.business_id == business.id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, val in body.model_dump(exclude_none=True).items():
        setattr(product, field, val)

    return APIResponse.ok(ProductOut.model_validate(product))


@router.delete("/{product_id}", response_model=APIResponse[dict])
async def delete_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.business_id == business.id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(product)
    return APIResponse.ok({"message": "Product deleted"})


@router.patch("/{product_id}/availability", response_model=APIResponse[ProductOut])
async def toggle_availability(
    product_id: uuid.UUID,
    body: AvailabilityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.business_id == business.id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_available = body.is_available
    return APIResponse.ok(ProductOut.model_validate(product))


@router.post("/{product_id}/image", response_model=APIResponse[dict])
async def upload_product_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.business_id == business.id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    url = await upload_file(file, folder=f"products/{business.id}")
    product.image_url = url
    return APIResponse.ok({"image_url": url})
