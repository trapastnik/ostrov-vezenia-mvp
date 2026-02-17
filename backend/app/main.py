import logging
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.services.pochta import PochtaClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    pochta = PochtaClient(settings)
    await pochta.start()
    app.state.pochta_client = pochta
    yield
    await pochta.close()


app = FastAPI(
    title="Ostrov Vezeniya API",
    version="1.0.0",
    description="Customs clearance and delivery service for Kaliningrad e-commerce",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/health")
async def health():
    return {"status": "ok"}


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/shop")
async def shop_emulator():
    return FileResponse(STATIC_DIR / "shop-emulator.html")
