import logging
import traceback
from contextlib import asynccontextmanager
from importlib.metadata import version as pkg_version
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.limiter import limiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.services.pochta import PochtaClient

APP_VERSION = pkg_version("ostrov-backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    pochta = PochtaClient(settings)
    await pochta.start()
    app.state.pochta_client = pochta
    yield
    await pochta.close()


app = FastAPI(
    title="Ostrov Vezeniya API",
    version=APP_VERSION,
    description="Customs clearance and delivery service for Kaliningrad e-commerce",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

app.include_router(api_v1_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health():
    return {"status": "ok", "version": APP_VERSION}


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/shop")
async def shop_emulator():
    return FileResponse(STATIC_DIR / "shop-emulator.html")
