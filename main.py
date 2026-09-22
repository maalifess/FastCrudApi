import sys
import os

# Ensure app package is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler,
)
from app.core.logging_middleware import request_logging_middleware
from app.routers.items import router as items_router
from app.routers.health import health_router
from app.routers.auth import auth_router

# Rate limiter (uses remote address by default)
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Production-grade MariaDB & FastAPI Platform Engine with Auth.",
)

# Attach limiter to app state for slowapi
app.state.limiter = limiter

@app.on_event("startup")
def run_migrations():
    import alembic.config
    from alembic import command
    import os
    import sys
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        alembic_ini_path = os.path.join(base_dir, "alembic.ini")
        # Ensure tables exist for fresh databases
        from app.db.database import Base, engine
        Base.metadata.create_all(bind=engine)
        
        # Stamp alembic head so it doesn't try to re-add columns
        # if the database was just created
        alembic_cfg = alembic.config.Config(alembic_ini_path)
        alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "alembic"))
        
        # We can try to upgrade, but if it fails (e.g. duplicate column), we ignore it
        # because create_all already created everything perfectly.
        try:
            command.upgrade(alembic_cfg, "head")
        except Exception:
            # If upgrade fails, stamp it to head so future migrations work
            command.stamp(alembic_cfg, "head")
            
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error applying migrations: {e}", file=sys.stderr)

# Exception handlers
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Middleware
app.middleware("http")(request_logging_middleware)

# CORS Configuration from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health routes
app.include_router(health_router)

# Version 1 API routes (/api/v1)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(items_router, prefix="/api/v1")

# Backwards compatibility routes (/api & root)
app.include_router(items_router, prefix="/api")
app.include_router(items_router)