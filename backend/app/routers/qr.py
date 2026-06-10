from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.analytics import AnalyticsEvent, QRCode
from app.models.business import Business
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.common import APIResponse
from app.schemas.qr import QRCodeOut
from app.services.qr_service import generate_qr_code

router = APIRouter(prefix="/qr", tags=["qr"])


async def _get_business(user: User, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.owner_id == user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="No business profile found")
    return business


@router.get("", response_model=APIResponse[QRCodeOut])
async def get_qr(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)

    result = await db.execute(select(QRCode).where(QRCode.business_id == business.id))
    qr = result.scalar_one_or_none()

    if not qr:
        # Auto-generate on first access
        qr = await generate_qr_code(business, db)

    return APIResponse.ok(QRCodeOut.model_validate(qr))


@router.post("/regenerate", response_model=APIResponse[QRCodeOut])
async def regenerate_qr(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business(current_user, db)
    qr = await generate_qr_code(business, db, force=True)
    return APIResponse.ok(QRCodeOut.model_validate(qr))


@router.get("/scan/{slug}")
async def track_qr_scan(slug: str, db: AsyncSession = Depends(get_db)):
    """
    Public endpoint — tracks a QR scan then 302-redirects to the clean URL.
    QR codes point here: /qr/scan/{slug}?ref=qr
    """
    result = await db.execute(
        select(Business).where(Business.slug == slug, Business.is_published == True)  # noqa: E712
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Log the scan
    db.add(
        AnalyticsEvent(
            business_id=business.id,
            event_type="qr_scan",
        )
    )

    # Increment denormalized counter
    qr_result = await db.execute(select(QRCode).where(QRCode.business_id == business.id))
    qr = qr_result.scalar_one_or_none()
    if qr:
        qr.scan_count += 1

    return Response(
        status_code=302,
        headers={"Location": f"/{slug}"},
    )
