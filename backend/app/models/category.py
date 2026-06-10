import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.business import Business
    from app.models.product import Product


class Category(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="categories")
    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name}>"
