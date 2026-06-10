import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SubscriptionOut(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    plan: str
    status: str
    started_at: datetime | None
    expires_at: datetime | None
    grace_period_ends_at: datetime | None
    payment_method: str | None
    amount_paid: Decimal | None
    is_active: bool
    is_premium: bool

    model_config = {"from_attributes": True}


class UpgradeRequest(BaseModel):
    plan: str  # "premium" | "business"
    payment_method: str  # "card" | "virement" | "cash"


class InvoiceOut(BaseModel):
    id: uuid.UUID
    plan: str
    amount_paid: Decimal | None
    payment_method: str | None
    payment_reference: str | None
    started_at: datetime | None

    model_config = {"from_attributes": True}


class PlanLimits(BaseModel):
    """Returns current plan limits for the business."""
    plan: str
    max_products: int
    current_products: int
    can_add_product: bool
    has_analytics: bool
    has_custom_domain: bool
    has_staff_accounts: bool
