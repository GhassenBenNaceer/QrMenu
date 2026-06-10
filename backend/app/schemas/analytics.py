import uuid
from datetime import date, datetime

from pydantic import BaseModel


class TrackEventRequest(BaseModel):
    business_id: uuid.UUID
    event_type: str  # page_view | qr_scan | product_view | contact_click | share_click
    product_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None
    referrer: str | None = None


class DailyStats(BaseModel):
    date: date
    page_views: int
    qr_scans: int


class TopProduct(BaseModel):
    product_id: uuid.UUID
    name: str
    view_count: int


class AnalyticsOverview(BaseModel):
    total_scans: int
    total_views: int
    unique_sessions: int
    avg_daily_views: float
    daily_trend: list[DailyStats]
    top_products: list[TopProduct]
    device_breakdown: dict[str, int]  # {"mobile": N, "tablet": N, "desktop": N}
