"""QR code generation service."""
import io
import os
import uuid
from pathlib import Path

import qrcode
import qrcode.image.svg
from qrcode.image.pure import PyPNGImage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.analytics import QRCode
from app.models.business import Business


STATIC_DIR = Path(__file__).parent.parent.parent / "static" / "qr"


def _qr_url(business: Business) -> str:
    """The URL embedded in the QR code — routes through the scan tracker."""
    return f"{settings.BASE_URL}/v1/qr/scan/{business.slug}"


def _generate_png(url: str) -> bytes:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def _generate_svg(url: str) -> str:
    factory = qrcode.image.svg.SvgImage
    qr = qrcode.make(url, image_factory=factory)
    buffer = io.BytesIO()
    qr.save(buffer)
    return buffer.getvalue().decode("utf-8")


async def generate_qr_code(
    business: Business,
    db: AsyncSession,
    force: bool = False,
) -> QRCode:
    """Generate (or regenerate) QR code for a business. Saves files locally."""
    redirect_url = _qr_url(business)

    # Check existing
    result = await db.execute(select(QRCode).where(QRCode.business_id == business.id))
    existing = result.scalar_one_or_none()

    if existing and not force:
        return existing

    # Generate files
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    png_bytes = _generate_png(redirect_url)
    svg_str = _generate_svg(redirect_url)

    bid = str(business.id)
    png_path = STATIC_DIR / f"{bid}.png"
    svg_path = STATIC_DIR / f"{bid}.svg"

    png_path.write_bytes(png_bytes)
    svg_path.write_text(svg_str, encoding="utf-8")

    png_url = f"{settings.CDN_BASE_URL}/qr/{bid}.png"
    svg_url = f"{settings.CDN_BASE_URL}/qr/{bid}.svg"

    if existing:
        existing.redirect_url = redirect_url
        existing.png_url = png_url
        existing.svg_url = svg_url
        return existing

    qr = QRCode(
        business_id=business.id,
        redirect_url=redirect_url,
        png_url=png_url,
        svg_url=svg_url,
    )
    db.add(qr)
    await db.flush()
    return qr
