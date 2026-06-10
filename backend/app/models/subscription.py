import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.business import Business


class Subscription(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # one subscription per business
        index=True,
    )
    plan: Mapped[str] = mapped_column(
        Enum("free", "premium", "business", name="subscription_plan"),
        nullable=False,
        default="free",
        server_default="free",
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "grace_period", "suspended", "cancelled", name="subscription_status"),
        nullable=False,
        default="active",
        server_default="active",
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_period_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    amount_paid: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="subscription")

    @property
    def is_active(self) -> bool:
        return self.status in ("active", "grace_period")

    @property
    def is_premium(self) -> bool:
        return self.plan in ("premium", "business") and self.is_active

    def __repr__(self) -> str:
        return f"<Subscription plan={self.plan} status={self.status}>"
