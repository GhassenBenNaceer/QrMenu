import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    name_ar: str | None = Field(default=None, max_length=255)
    description: str | None = None
    description_ar: str | None = None
    price: Decimal = Field(gt=0, decimal_places=3)
    category_id: uuid.UUID | None = None
    is_available: bool = True
    is_featured: bool = False
    sort_order: int = Field(default=0, ge=0)


class UpdateProductRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    name_ar: str | None = None
    description: str | None = None
    description_ar: str | None = None
    price: Decimal | None = Field(default=None, gt=0, decimal_places=3)
    category_id: uuid.UUID | None = None
    is_available: bool | None = None
    is_featured: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)


class AvailabilityRequest(BaseModel):
    is_available: bool


class ProductOut(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    category_id: uuid.UUID | None
    name: str
    name_ar: str | None
    description: str | None
    description_ar: str | None
    price: Decimal
    image_url: str | None
    is_available: bool
    is_featured: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
