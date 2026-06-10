import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, SmallInteger, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.analytics import AnalyticsEvent, QRCode
    from app.models.category import Category
    from app.models.product import Product
    from app.models.subscription import Subscription
    from app.models.user import User


class Business(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "businesses"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(
        Enum(
            "restaurant", "cafe", "fastfood", "salon",
            "barbershop", "hotel", "other",
            name="business_category",
        ),
        nullable=False,
        default="restaurant",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    primary_color: Mapped[str] = mapped_column(
        String(7), default="#1B4F72", server_default="#1B4F72"
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="businesses")
    hours: Mapped[list["BusinessHours"]] = relationship(
        "BusinessHours", back_populates="business", cascade="all, delete-orphan"
    )
    categories: Mapped[list["Category"]] = relationship(
        "Category", back_populates="business", cascade="all, delete-orphan"
    )
    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="business", cascade="all, delete-orphan"
    )
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription", back_populates="business", uselist=False, cascade="all, delete-orphan"
    )
    analytics_events: Mapped[list["AnalyticsEvent"]] = relationship(
        "AnalyticsEvent", back_populates="business"
    )
    qr_code: Mapped["QRCode | None"] = relationship(
        "QRCode", back_populates="business", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Business id={self.id} slug={self.slug}>"


class BusinessHours(UUIDMixin, Base):
    __tablename__ = "business_hours"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0=Sun … 6=Sat
    open_time: Mapped[str | None] = mapped_column(String(5), nullable=True)   # "08:00"
    close_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "23:00"
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="hours")
