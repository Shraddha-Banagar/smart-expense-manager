from app.routers.auth import router as auth_router
from app.routers.expenses import router as expenses_router
from app.routers.analytics import router as analytics_router
from app.routers.documents import router as documents_router
from app.routers.ai import router as ai_router
from app.routers.budgets import router as budgets_router
from app.routers.reports import router as reports_router

__all__ = [
    "auth_router",
    "expenses_router",
    "analytics_router",
    "documents_router",
    "ai_router",
    "budgets_router",
    "reports_router",
]
