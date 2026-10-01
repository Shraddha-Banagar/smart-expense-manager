"""
Application entrypoint: creates the FastAPI app, configures CORS,
registers routers, and sets up centralized error handling and logging.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import Base, engine
from app.routers import auth_router, expenses_router, analytics_router, documents_router, ai_router, budgets_router, reports_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("expense_manager")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist (dev convenience; use Alembic migrations in production)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")
    yield
    # Shutdown: nothing to clean up yet


app = FastAPI(
    title="Smart Expense Manager API",
    description="AI-powered expense management platform API.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Lets the browser read the PDF filename on cross-origin report downloads.
    expose_headers=["Content-Disposition"],
)


# --- Centralized error handling ---------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid input.", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )


# --- Routers ------------------------------------------------------------
app.include_router(auth_router)
app.include_router(expenses_router)
app.include_router(analytics_router)
app.include_router(documents_router)
app.include_router(ai_router)
app.include_router(budgets_router)
app.include_router(reports_router)


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok"}
