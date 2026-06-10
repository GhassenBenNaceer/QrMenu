import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


BUSINESS_CATEGORIES = Literal[
    "restaurant", "cafe", "fastfood", "salon", "barbershop", "hotel", "other"
]


class BusinessHoursIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    open_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    close_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    is_closed: bool = False


class BusinessHoursOut(BusinessHoursIn):
    id: uuid.UUID
    model_config = {"from_attributes": True}


class CreateBusinessRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    name_ar: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    category: BUSINESS_CATEGORIES = "restaurant"
    city: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    whatsapp: str | None = Field(default=None, max_length=20)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        if v is None:
            return v
        import re
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug may only contain lowercase letters, numbers, and hyphens")
        return v


class UpdateBusinessRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    name_ar: str | None = None
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    category: BUSINESS_CATEGORIES | None = None
    description: str | None = None
    description_ar: str | None = None
    phone: str | None = Field(default=None, max_length=20)
    whatsapp: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=100)
    primary_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    hours: list[BusinessHoursIn] | None = None


class BusinessOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    slug: str
    name: str
    name_ar: str | None
    category: str
    description: str | None
    description_ar: str | None
    logo_url: str | None
    cover_url: str | None
    phone: str | None
    whatsapp: str | None
    address: str | None
    city: str | None
    is_published: bool
    primary_color: str
    hours: list[BusinessHoursOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class PublicProductOut(BaseModel):
    id: uuid.UUID
    name: str
    name_ar: str | None
    description: str | None
    description_ar: str | None
    price: float
    image_url: str | None
    is_available: bool
    is_featured: bool
    sort_order: int

    model_config = {"from_attributes": True}


class PublicCategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    name_ar: str | None
    sort_order: int
    products: list[PublicProductOut] = []

    model_config = {"from_attributes": True}


class PublicBusinessOut(BaseModel):
    """Full public page payload — no auth required."""

    id: uuid.UUID
    slug: str
    name: str
    name_ar: str | None
    category: str
    description: str | None
    description_ar: str | None
    logo_url: str | None
    cover_url: str | None
    phone: str | None
    whatsapp: str | None
    address: str | None
    city: str | None
    primary_color: str
    hours: list[BusinessHoursOut] = []
    categories: list[PublicCategoryOut] = []

    model_config = {"from_attributes": True}
