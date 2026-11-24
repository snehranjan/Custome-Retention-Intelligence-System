"""
Indian E-Commerce Customer Retention Intelligence System
Customer Management Routes (Phase 8.4.8 - Customer Retention Explorer & Advanced Analytics)

Endpoints:
- GET /api/v1/customers: Paginated customer directory with multi-dimensional filtering, search, and sorting
- GET /api/v1/customers/{customer_id}: Single customer profile with historical predictions, segments, recommendations, and 43 behavioral features
- POST /api/v1/customers/{customer_id}/predict: Live churn prediction inference using locked Random Forest pipeline

Security:
- All routes strictly protected by require_authorized_employee dependency.
- Rejects unauthenticated requests with HTTP 401 UNAUTHORIZED.
- Rejects authenticated but unapproved accounts with HTTP 403 FORBIDDEN.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Path, Query, status

from backend.app.core.config import settings
from backend.app.core.dependencies import require_authorized_employee
from backend.app.core.errors import NotFoundException
from backend.app.core.logging import logger
from backend.app.repositories import get_repository
from backend.app.schemas.auth import AuthenticatedUser
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.customer import (
    CustomerDetail,
    CustomerListResponse,
    CustomerSummary,
)
from backend.app.schemas.ml import ChurnPredictionResponse, RawCustomerFeatures
from backend.app.services.churn_service import ChurnPredictionService
from backend.app.services.customer_feature_service import CustomerFeatureService

router = APIRouter(
    tags=["Customer Management"],
    dependencies=[Depends(require_authorized_employee)],
)


@router.get(
    "",
    response_model=ApiResponse[CustomerListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Customers (Paginated & Filterable)",
    description=(
        "Retrieves a paginated list of customers with search, segment, risk tier, "
        "geographic filters, and sorting. Requires authorized employee permissions."
    ),
)
async def list_customers(
    limit: int = Query(default=50, ge=1, le=100, description="Page size (1 to 100 records)"),
    offset: int = Query(default=0, ge=0, description="Page offset (>= 0)"),
    search: Optional[str] = Query(default=None, max_length=100, description="Optional search by customer ID or name"),
    segment: Optional[int] = Query(default=None, ge=0, le=4, description="Filter by cluster ID (0 to 4)"),
    risk_tier: Optional[str] = Query(default=None, description="Filter by risk tier: LOW, MODERATE, HIGH"),
    state: Optional[str] = Query(default=None, description="Filter by state name"),
    city: Optional[str] = Query(default=None, description="Filter by city name"),
    sort_by: str = Query(default="customer_id", description="Field to sort by"),
    sort_dir: str = Query(default="ASC", pattern="^(ASC|DESC|asc|desc)$", description="Sort direction: ASC or DESC"),
    current_employee: AuthenticatedUser = Depends(require_authorized_employee),
) -> ApiResponse[CustomerListResponse]:
    """Returns paginated customer records matching search and filtering criteria."""
    storage_mode = settings.STORAGE_MODE.lower()
    repo = get_repository(storage_mode)

    try:
        raw_records, total = repo.query_customers(
            limit=limit,
            offset=offset,
            search=search,
            segment=segment,
            risk_tier=risk_tier,
            state=state,
            city=city,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    except NotImplementedError:
        # Fallback for repositories without advanced query support
        clean_search = search.strip() if search and search.strip() else None
        if clean_search:
            single_cust = repo.get_customer_by_id(clean_search)
            if single_cust:
                raw_records = [single_cust]
                total = 1
            else:
                raw_records = []
                total = 0
        else:
            total = repo.get_customer_count()
            raw_records = repo.list_customers(limit=limit, offset=offset)

    items = [CustomerSummary(**r) for r in raw_records]
    has_more = (offset + len(items)) < total

    return ApiResponse[CustomerListResponse](
        success=True,
        data=CustomerListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        ),
    )


@router.get(
    "/{customer_id}",
    response_model=ApiResponse[CustomerDetail],
    status_code=status.HTTP_200_OK,
    summary="Get Customer Detail Profile",
    description=(
        "Retrieves a single customer profile by customer_id along with associated "
        "ML churn predictions, RFM segmentation, retention recommendations, and raw 43 features. "
        "Returns HTTP 404 if the customer does not exist. Requires authorized employee permissions."
    ),
)
async def get_customer_by_id(
    customer_id: str = Path(..., min_length=1, max_length=64, description="Customer identifier (e.g. IND_CUST_10001)"),
    current_employee: AuthenticatedUser = Depends(require_authorized_employee),
) -> ApiResponse[CustomerDetail]:
    """Retrieves full customer profile, ML intelligence, and authoritative behavioral features."""
    clean_id = customer_id.strip()
    storage_mode = settings.STORAGE_MODE.lower()
    repo = get_repository(storage_mode)

    cust = repo.get_customer_by_id(clean_id)
    if not cust:
        logger.info("Customer lookup 404: '%s' not found in %s storage", clean_id, storage_mode)
        raise NotFoundException(f"Customer '{clean_id}' was not found.")

    # Retrieve related intelligence records if stored
    latest_pred = repo.get_latest_prediction(clean_id)
    current_seg = repo.get_current_segment(clean_id)
    recommendations = repo.get_recommendations(clean_id)
    features = CustomerFeatureService.get_features(clean_id)

    detail_data = dict(cust)
    detail_data["latest_prediction"] = latest_pred
    detail_data["current_segment"] = current_seg
    detail_data["recommendations"] = recommendations or []
    detail_data["features"] = features

    return ApiResponse[CustomerDetail](
        success=True,
        data=CustomerDetail(**detail_data),
    )


@router.post(
    "/{customer_id}/predict",
    response_model=ApiResponse[ChurnPredictionResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute Live Churn Prediction Inference",
    description=(
        "Executes real-time inference using the locked Random Forest pipeline (tau = 0.50) "
        "on the customer's authoritative 43 behavioral features. "
        "Requires authorized employee permissions."
    ),
)
async def predict_customer_churn(
    customer_id: str = Path(..., min_length=1, max_length=64, description="Customer identifier (e.g. IND_CUST_10001)"),
    current_employee: AuthenticatedUser = Depends(require_authorized_employee),
) -> ApiResponse[ChurnPredictionResponse]:
    """Runs live model inference for a single customer and returns probabilities, label, and risk tier."""
    clean_id = customer_id.strip()
    storage_mode = settings.STORAGE_MODE.lower()
    repo = get_repository(storage_mode)

    cust = repo.get_customer_by_id(clean_id)
    if not cust:
        raise NotFoundException(f"Customer '{clean_id}' was not found.")

    features_obj = CustomerFeatureService.get_raw_customer_features(clean_id)
    if not features_obj:
        raise NotFoundException(f"Behavioral features for customer '{clean_id}' were not found.")

    # Perform live inference via locked Random Forest pipeline
    prediction = ChurnPredictionService.predict(features_obj)

    # Persist the newly generated prediction for audit trail
    try:
        repo.insert_prediction({
            "customer_id": clean_id,
            "churn_probability": prediction.churn_probability,
            "predicted_churn": prediction.predicted_class,
            "decision_threshold": prediction.decision_threshold,
            "risk_tier": prediction.risk_tier,
            "model_version": getattr(prediction, "model_version", "phase5_1_rf"),
        })
    except Exception as e:
        logger.warning("Could not persist live prediction to storage: %s", e)

    return ApiResponse[ChurnPredictionResponse](
        success=True,
        data=prediction,
    )
