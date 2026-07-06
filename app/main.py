"""FastAPI application entry point and global exception handling."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.database import init_db
from app.core.exceptions import CarrierError

# Create tables on startup (no Alembic migrations in this project).
init_db()

app = FastAPI(
    title="Carrier API",
    description="Shipping rate quotes API",
    version="1.0.0",
)


@app.exception_handler(CarrierError)
async def carrier_error_handler(request: Request, exc: CarrierError):
    # Services raise CarrierError subclasses; this converts them to standard
    # FastAPI JSON error responses without try/except in every endpoint.
    detail = {"code": exc.code, "message": exc.message}
    if exc.details is not None:
        detail["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


app.include_router(api_router)
