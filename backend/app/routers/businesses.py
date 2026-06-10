import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.business import Business, BusinessHours
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.business import (
    BusinessOut,
    CreateBusinessRequest,
    PublicBusinessOut,
    UpdateBusinessRequest,
)
from app.schemas.common import APIResponse
from app.services.auth_service import generate_slug_from_name
from app.services.storage_service import upload_file

router = APIRouter(prefix="/businesses", tags=["businesses"])

# ── Slugs that cannot be registered ──────────────────────────────────────────
RESERVED_SLUGS = {
    "admin", "api", "www", "login", "register", "blog",
    "about", "contact", "help", "support", "terms", "privacy",
    "dashboard", "settings", "static", "media",
}


async def _resolve_unique_slug(base_slug: str, db: AsyncSession, exclude_id: uuid.UUID | None = None) -> str:
    slug = base_slug
    counter = 2
    while True:
        query = select(Business).where(Business.slug == slug)
        if exclude_id:
            query = query.where(Business.id != exclude_id)
        result = await db.execute(query)
        if result.scalar_one_or_none() is None and slug not in RESERVED_SLUGS:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


@router.post("", response_model=APIResponse[BusinessOut], status_code=status.HTTP_201_CREATED)
async def create_business(
    body: CreateBusinessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # One business per owner (free/premium)
    result = await db.execute(select(Business).where(Business.owner_id == current_user.id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already have a business profile")

    base_slug = body.slug or generate_slug_from_name(body.name)
    slug = await _resolve_unique_slug(base_slug, db)

    business = Business(
        owner_id=current_user.id,
        slug=slug,
        name=body.name,
        name_ar=body.name_ar,
        category=body.category,
        city=body.city,
        phone=body.phone,
        whatsapp=body.whatsapp,
    )
    db.add(business)
    await db.flush()

    # Re-fetch with relationships to avoid async lazy-load error
    result2 = await db.execute(
        select(Business)
        .where(Business.id == business.id)
        .options(selectinload(Business.hours))
    )
    business = result2.scalar_one()
    return APIResponse.ok(BusinessOut.model_validate(business))


@router.get("/me", response_model=APIResponse[BusinessOut])
async def get_my_business(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Business)
        .where(Business.owner_id == current_user.id)
        .options(selectinload(Business.hours))
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="No business profile found")
    return APIResponse.ok(BusinessOut.model_validate(business))


@router.patch("/me", response_model=APIResponse[BusinessOut])
async def update_my_business(
    body: UpdateBusinessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Business)
        .where(Business.owner_id == current_user.id)
        .options(selectinload(Business.hours))
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="No business profile found")

    for field in ["name", "name_ar", "category", "description", "description_ar",
                  "phone", "whatsapp", "address", "city", "primary_color"]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(business, field, val)

    if body.slug is not None and body.slug != business.slug:
        new_slug = await _resolve_unique_slug(body.slug, db, exclude_id=business.id)
        business.slug = new_slug

    if body.hours is not None:
        # Replace all hours
        for h in business.hours:
            await db.delete(h)
        for h_in in body.hours:
            db.add(BusinessHours(business_id=business.id, **h_in.model_dump()))

    return APIResponse.ok(BusinessOut.model_validate(business))


@router.delete("/me", response_model=APIResponse[dict])
async def delete_my_business(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Business).where(Business.owner_id == current_user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="No business profile found")
    await db.delete(business)
    return APIResponse.ok({"message": "Business deleted"})


@router.post("/me/logo", response_model=APIResponse[dict])
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Business).where(Business.owner_id == current_user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="No business profile found")

    url = await upload_file(file, folder=f"logos/{business.id}")
    business.logo_url = url
    await db.commit()
    await db.refresh(business)
    return APIResponse.ok({"logo_url": url})


@router.post("/me/cover", response_model=APIResponse[dict])
async def upload_cover(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Business).where(Business.owner_id == current_user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="No business profile found")

    url = await upload_file(file, folder=f"covers/{business.id}")
    business.cover_url = url
    await db.commit()
    await db.refresh(business)
    return APIResponse.ok({"cover_url": url})


@router.get("/{slug}/public", response_model=APIResponse[PublicBusinessOut])
async def get_public_page(slug: str, db: AsyncSession = Depends(get_db)):
    """No auth required — serves the public menu page."""
    result = await db.execute(
        select(Business)
        .where(Business.slug == slug, Business.is_published == True)  # noqa: E712
        .options(
            selectinload(Business.hours),
            selectinload(Business.categories).selectinload(Category.products),
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Build public payload — filter inactive categories and unavailable products
    out = PublicBusinessOut.model_validate(business)
    out.categories = [
        c for c in out.categories
        if c  # selectinload already populated via relationship
    ]
    return APIResponse.ok(out)


@router.post("/me/publish", response_model=APIResponse[BusinessOut])
async def publish_business(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Business)
        .where(Business.owner_id == current_user.id)
        .options(selectinload(Business.hours))
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="No business profile found")
    business.is_published = True
    return APIResponse.ok(BusinessOut.model_validate(business))
