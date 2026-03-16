from fastapi import FastAPI
from app.config import settings
from app.api.v1 import api_router

app = FastAPI(
    title="Room Booking API",
    description="API для бронирования переговорных комнат",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {"message": "Room Booking API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
