from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import (
    admin,
    analytics,
    auth,
    businesses,
    categories,
    products,
    qr,
    subscriptions,
)

STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure static dirs exist on startup
    (STATIC_DIR / "uploads").mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "qr").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Digital Menu & Business Presence Platform for Tunisia",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_origins = ["http://localhost:3000"]
if settings.FRONTEND_URL:
    _origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (local storage dev mode) ────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── Routers ───────────────────────────────────────────────────────────────────
PREFIX = "/v1"

app.include_router(admin.router, prefix=PREFIX)
app.include_router(auth.router, prefix=PREFIX)
app.include_router(businesses.router, prefix=PREFIX)
app.include_router(categories.router, prefix=PREFIX)
app.include_router(products.router, prefix=PREFIX)
app.include_router(qr.router, prefix=PREFIX)
app.include_router(analytics.router, prefix=PREFIX)
app.include_router(subscriptions.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
