from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.business import Business
from app.models.product import Product
from app.models.user import User
from app.routers.deps import get_current_superadmin
from app.schemas.common import APIResponse

router = APIRouter(prefix="/admin", tags=["admin"])


class DailySignup(BaseModel):
    date: str
    count: int


class AdminStats(BaseModel):
    total_users: int
    total_businesses: int
    published_businesses: int
    total_products: int
    signups_last_7_days: list[DailySignup]
    recent_businesses: list[dict]


@router.get("/stats", response_model=APIResponse[AdminStats])
async def get_admin_stats(
    _: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    # Totals
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    total_businesses = (await db.execute(select(func.count()).select_from(Business))).scalar_one()
    published_businesses = (await db.execute(
        select(func.count()).select_from(Business).where(Business.is_published == True)  # noqa: E712
    )).scalar_one()
    total_products = (await db.execute(select(func.count()).select_from(Product))).scalar_one()

    # Signups per day for last 7 days
    signups_last_7_days: list[DailySignup] = []
    for i in range(6, -1, -1):
        day_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        count = (await db.execute(
            select(func.count()).select_from(User).where(
                User.created_at >= day_start,
                User.created_at < day_end,
            )
        )).scalar_one()
        signups_last_7_days.append(DailySignup(date=day_start.strftime("%d/%m"), count=count))

    # 5 most recent businesses
    result = await db.execute(
        select(Business, User.email, User.full_name)
        .join(User, Business.owner_id == User.id)
        .order_by(Business.created_at.desc())
        .limit(5)
    )
    recent_businesses = [
        {
            "id": str(b.id),
            "name": b.name,
            "slug": b.slug,
            "category": b.category,
            "is_published": b.is_published,
            "owner_email": email,
            "owner_name": full_name,
            "created_at": b.created_at.strftime("%d/%m/%Y"),
        }
        for b, email, full_name in result.all()
    ]

    return APIResponse.ok(AdminStats(
        total_users=total_users,
        total_businesses=total_businesses,
        published_businesses=published_businesses,
        total_products=total_products,
        signups_last_7_days=signups_last_7_days,
        recent_businesses=recent_businesses,
    ))
