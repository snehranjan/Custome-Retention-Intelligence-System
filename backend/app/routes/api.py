"""
Indian E-Commerce Customer Retention Intelligence System
API v1 Main Router Aggregator
"""

from fastapi import APIRouter
from backend.app.routes import (
    admin,
    analytics,
    auth,
    customers,
    database,
    employee,
    health,
    ml,
    recommendations,
)

api_router = APIRouter()

# Mount health routes under /api/v1/health (Public)
api_router.include_router(health.router, prefix="", tags=["System Health"])

# Mount Authentication routes under /api/v1/auth (Phase 7.5)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Mount Employee Registration routes under /api/v1/employee (Phase 8.4.5)
api_router.include_router(employee.router, prefix="/employee", tags=["Employee Registration"])

# Mount Administrator Review routes under /api/v1/admin (Phase 8.4.5 - Protected by require_admin_user)
api_router.include_router(admin.router, prefix="", tags=["Administrator Operations"])

# Mount ML and Analytics routes under /api/v1 (Phase 7.3 - Protected by get_current_user)
api_router.include_router(ml.router, prefix="", tags=["Machine Learning & Analytics"])

# Mount Database Management routes under /api/v1/database (Phase 7.4 - Protected by get_current_user)
api_router.include_router(database.router, prefix="", tags=["Database & Storage Management"])

# Mount Customer Management routes under /api/v1/customers (Phase 8.4.8 - Protected by require_authorized_employee)
api_router.include_router(customers.router, prefix="/customers", tags=["Customer Management"])

# Mount Analytics & Intelligence routes under /api/v1/analytics (Phase 8.4.8 - Protected by require_authorized_employee)
api_router.include_router(analytics.router, prefix="", tags=["Analytics & Intelligence"])

# Mount Retention Recommendations routes under /api/v1/recommendations (Phase 8.4.8 - Protected by require_authorized_employee)
api_router.include_router(recommendations.router, prefix="", tags=["Retention Recommendations"])
