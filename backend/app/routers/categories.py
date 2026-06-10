import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.business import Business
from app.models.category import Category
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.category import (
    CategoryOut,
    CreateCategoryRequest,
    ReorderCategoriesRequest,
    UpdateCategoryRequest,
)
from app.schemas.common import APIResponse

router = APIRouter(prefix="/categories", tags=["categories"])


async def _get_business(user: User, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.owner_id == user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="No business profile found")
    return business


@router.get("", response_model=APIResponse[list[CategoryOut]])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    result = await db.execute(
        select(Category)
        .where(Category.business_id == business.id)
        .order_by(Category.sort_order)
    )
    categories = result.scalars().all()
    return APIResponse.ok([CategoryOut.model_validate(c) for c in categories])


@router.post("", response_model=APIResponse[CategoryOut], status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CreateCategoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    category = Category(business_id=business.id, **body.model_dump())
    db.add(category)
    await db.flush()
    return APIResponse.ok(CategoryOut.model_validate(category))


@router.patch("/{category_id}", response_model=APIResponse[CategoryOut])
async def update_category(
    category_id: uuid.UUID,
    body: UpdateCategoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    result = await db.execute(
        select(Category).where(Category.id == category_id, Category.business_id == business.id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    for field, val in body.model_dump(exclude_none=True).items():
        setattr(category, field, val)

    return APIResponse.ok(CategoryOut.model_validate(category))


@router.delete("/{category_id}", response_model=APIResponse[dict])
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    result = await db.execute(
        select(Category).where(Category.id == category_id, Category.business_id == business.id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    await db.delete(category)
    return APIResponse.ok({"message": "Category deleted"})


@router.post("/reorder", response_model=APIResponse[dict])
async def reorder_categories(
    body: ReorderCategoriesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    for item in body.items:
        result = await db.execute(
            select(Category).where(
                Category.id == item.id, Category.business_id == business.id
            )
        )
        category = result.scalar_one_or_none()
        if category:
            category.sort_order = item.sort_order
    return APIResponse.ok({"message": "Reordered successfully"})
