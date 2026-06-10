import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.analytics import AnalyticsEvent
from app.models.business import Business
from app.models.product import Product
from app.models.subscription import Subscription
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.analytics import AnalyticsOverview, TrackEventRequest
from app.schemas.common import APIResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def _get_business(user: User, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.owner_id == user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="No business profile found")
    return business


async def _require_premium(business: Business, db: AsyncSession) -> None:
    result = await db.execute(
        select(Subscription).where(Subscription.business_id == business.id)
    )
    sub = result.scalar_one_or_none()
    if not sub or not sub.is_premium:
        raise HTTPException(
            status_code=403,
            detail="Analytics requires a Premium or Business plan",
        )


@router.get("/overview", response_model=APIResponse[AnalyticsOverview])
async def get_overview(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    await _require_premium(business, db)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Total scans
    scans_result = await db.execute(
        select(func.count()).where(
            AnalyticsEvent.business_id == business.id,
            AnalyticsEvent.event_type == "qr_scan",
            AnalyticsEvent.created_at >= since,
        )
    )
    total_scans = scans_result.scalar_one() or 0

    # Total views
    views_result = await db.execute(
        select(func.count()).where(
            AnalyticsEvent.business_id == business.id,
            AnalyticsEvent.event_type == "page_view",
            AnalyticsEvent.created_at >= since,
        )
    )
    total_views = views_result.scalar_one() or 0

    # Unique sessions
    sessions_result = await db.execute(
        select(func.count(func.distinct(AnalyticsEvent.session_id))).where(
            AnalyticsEvent.business_id == business.id,
            AnalyticsEvent.created_at >= since,
            AnalyticsEvent.session_id.isnot(None),
        )
    )
    unique_sessions = sessions_result.scalar_one() or 0

    avg_daily = round(total_views / days, 1) if days > 0 else 0.0

    return APIResponse.ok(
        AnalyticsOverview(
            total_scans=total_scans,
            total_views=total_views,
            unique_sessions=unique_sessions,
            avg_daily_views=avg_daily,
            daily_trend=[],      # TODO: aggregate by day
            top_products=[],     # TODO: aggregate product_view events
            device_breakdown={}, # TODO: aggregate device_type
        )
    )


@router.post("/track", response_model=APIResponse[dict])
async def track_event(body: TrackEventRequest, db: AsyncSession = Depends(get_db)):
    """Public, no-auth event tracking endpoint. Rate-limited at the proxy level."""
    result = await db.execute(
        select(Business).where(
            Business.id == body.business_id, Business.is_published == True  # noqa: E712
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    allowed_types = {"page_view", "qr_scan", "product_view", "contact_click", "share_click"}
    if body.event_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid event type")

    db.add(
        AnalyticsEvent(
            business_id=body.business_id,
            product_id=body.product_id,
            event_type=body.event_type,
            session_id=body.session_id,
            referrer=body.referrer,
        )
    )
    return APIResponse.ok({"tracked": True})
