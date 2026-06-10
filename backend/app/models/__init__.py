# Import all models so Alembic can detect them during autogenerate
from app.models.analytics import AnalyticsEvent, QRCode
from app.models.business import Business, BusinessHours
from app.models.category import Category
from app.models.product import Product
from app.models.subscription import Subscription
from app.models.user import User

__all__ = [
    "User",
    "Business",
    "BusinessHours",
    "Category",
    "Product",
    "Subscription",
    "AnalyticsEvent",
    "QRCode",
]
