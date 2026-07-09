"""FastAPI application entry point and global exception handling."""

import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.deps import init_cache, shutdown_cache
from app.api.v1 import api_router
from app.core.database import engine
from app.core.exceptions import CarrierError


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_cache()
    yield
    await shutdown_cache()
    await engine.dispose()


app = FastAPI(
    title="Carrier API",
    description="Shipping rate quotes API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(CarrierError)
async def carrier_error_handler(request: Request, exc: CarrierError):
    detail = {"code": exc.code, "message": exc.message}
    if exc.details is not None:
        detail["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


app.include_router(api_router)
