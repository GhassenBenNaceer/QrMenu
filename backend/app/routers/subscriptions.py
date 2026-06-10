from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.business import Business
from app.models.product import Product
from app.models.subscription import Subscription
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.common import APIResponse
from app.schemas.subscription import (
    InvoiceOut,
    PlanLimits,
    SubscriptionOut,
    UpgradeRequest,
)
from sqlalchemy import func

router = APIRouter(prefix="/subscription", tags=["subscription"])


async def _get_business(user: User, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.owner_id == user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="No business profile found")
    return business


async def _get_or_create_subscription(business: Business, db: AsyncSession) -> Subscription:
    result = await db.execute(
        select(Subscription).where(Subscription.business_id == business.id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        sub = Subscription(business_id=business.id, plan="free", status="active")
        db.add(sub)
        await db.flush()
    return sub


@router.get("", response_model=APIResponse[SubscriptionOut])
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    sub = await _get_or_create_subscription(business, db)
    return APIResponse.ok(SubscriptionOut.model_validate(sub))


@router.get("/limits", response_model=APIResponse[PlanLimits])
async def get_plan_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    sub = await _get_or_create_subscription(business, db)

    count_result = await db.execute(
        select(func.count()).where(Product.business_id == business.id)
    )
    current_products = count_result.scalar_one() or 0

    is_premium = sub.is_premium
    max_products = 999 if is_premium else settings.FREE_PLAN_MAX_PRODUCTS

    return APIResponse.ok(
        PlanLimits(
            plan=sub.plan,
            max_products=max_products,
            current_products=current_products,
            can_add_product=current_products < max_products,
            has_analytics=is_premium,
            has_custom_domain=sub.plan == "business" and sub.is_active,
            has_staff_accounts=sub.plan == "business" and sub.is_active,
        )
    )


@router.post("/upgrade", response_model=APIResponse[SubscriptionOut])
async def upgrade_subscription(
    body: UpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.plan not in ("premium", "business"):
        raise HTTPException(status_code=400, detail="Invalid plan")

    business = await _get_business(current_user, db)
    sub = await _get_or_create_subscription(business, db)

    # TODO: integrate with payment gateway (Flouci / Konnect / Paymee)
    # For now, simulate a successful upgrade for development
    price = settings.PREMIUM_PRICE_TND if body.plan == "premium" else settings.BUSINESS_PRICE_TND
    sub.plan = body.plan
    sub.status = "active"
    sub.started_at = datetime.now(timezone.utc)
    sub.expires_at = datetime.now(timezone.utc) + timedelta(days=365)
    sub.payment_method = body.payment_method
    sub.amount_paid = price  # type: ignore[assignment]

    return APIResponse.ok(SubscriptionOut.model_validate(sub))


@router.post("/cancel", response_model=APIResponse[SubscriptionOut])
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    sub = await _get_or_create_subscription(business, db)
    sub.status = "cancelled"
    return APIResponse.ok(SubscriptionOut.model_validate(sub))


@router.get("/invoices", response_model=APIResponse[list[InvoiceOut]])
async def list_invoices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    result = await db.execute(
        select(Subscription).where(Subscription.business_id == business.id)
    )
    sub = result.scalar_one_or_none()
    invoices = [InvoiceOut.model_validate(sub)] if sub and sub.amount_paid else []
    return APIResponse.ok(invoices)
