import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateCategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    name_ar: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0)


class UpdateCategoryRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    name_ar: str | None = None
    sort_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ReorderItem(BaseModel):
    id: uuid.UUID
    sort_order: int = Field(ge=0)


class ReorderCategoriesRequest(BaseModel):
    items: list[ReorderItem]


class CategoryOut(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    name: str
    name_ar: str | None
    sort_order: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
