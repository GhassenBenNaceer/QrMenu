import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin

if TYPE_CHECKING:
    from app.models.business import Business
    from app.models.product import Product


class AnalyticsEvent(Base):
    """High-volume event table — uses BigSerial PK for performance."""

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(
        Enum(
            "page_view", "qr_scan", "product_view", "contact_click", "share_click",
            name="analytics_event_type",
        ),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    device_type: Mapped[str | None] = mapped_column(
        Enum("mobile", "tablet", "desktop", name="device_type"),
        nullable=True,
    )
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="analytics_events")


class QRCode(UUIDMixin, Base):
    __tablename__ = "qr_codes"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    redirect_url: Mapped[str] = mapped_column(String(500), nullable=False)
    svg_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    png_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scan_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="qr_code")
