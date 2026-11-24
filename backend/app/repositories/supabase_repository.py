"""
Indian E-Commerce Customer Retention Intelligence System
Supabase PostgreSQL Repository Implementation (Phase 7.4)

Provides enterprise-grade, PostgREST-compliant storage integration for Supabase PostgreSQL
utilizing HTTP connection pooling via httpx. Implements BaseRepository with strict adherence
to the NO SILENT FALLBACK invariant, foreign key integrity, and sanitized exception handling.
"""

from datetime import datetime, timezone
import os
import re
from typing import Any, Dict, List, Optional, Set
import uuid

import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.repositories.base_repository import BaseRepository
from backend.app.repositories.exceptions import (
    ConfigurationError,
    ConstraintViolationError,
    CustomerNotFoundError,
    DatabaseUnavailableError,
    DuplicateRecordError,
    ForeignKeyViolationError,
    RepositoryError,
)


class SupabaseRepository(BaseRepository):
    """
    Direct PostgREST HTTP repository for Supabase PostgreSQL.
    Communicates synchronously with Supabase PostgREST endpoints (/rest/v1/*),
    ensuring identical semantics and data contracts with SQLiteRepository.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        timeout: float = 10.0,
        client: Optional[httpx.Client] = None,
    ):
        """
        Initializes Supabase repository with project URL and API key.
        Accepts optional injected httpx.Client for isolated unit testing.
        Raises ConfigurationError if required connection parameters are missing.
        """
        self.url = (url or settings.SUPABASE_URL or "").rstrip("/")
        # Strictly prefer privileged secret key for backend storage operations
        self.key = key or settings.get_supabase_secret_key() or settings.get_supabase_publishable_key()
        self.timeout = timeout

        if not self.url:
            raise ConfigurationError(
                "Supabase URL is missing. Set SUPABASE_URL in configuration or environment."
            )
        if not self.key:
            raise ConfigurationError(
                "Supabase API key is missing. Set SUPABASE_SECRET_KEY in local backend/.env."
            )

        self.rest_url = f"{self.url}/rest/v1"
        self._default_headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Use injected client (for tests) or create a new dedicated client
        self._client = client or httpx.Client(
            base_url=self.rest_url,
            headers=self._default_headers,
            timeout=self.timeout,
        )

    def close(self) -> None:
        """Closes the underlying HTTP client session."""
        try:
            self._client.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _handle_http_error(self, e: Exception, operation: str = "Supabase operation") -> None:
        """
        Translates HTTP status codes and PostgREST JSON errors into domain exceptions,
        strictly preventing leaking of secret keys, tokens, or raw credentials.
        """
        if isinstance(e, httpx.HTTPStatusError):
            status = e.response.status_code
            msg = ""
            details = ""
            code = ""
            try:
                err_json = e.response.json()
                if isinstance(err_json, dict):
                    msg = err_json.get("message", "")
                    details = err_json.get("details", "")
                    code = err_json.get("code", "")
            except Exception:
                msg = e.response.text[:200]

            combined = f"{msg} {details} {code}".lower()

            if status in (401, 403):
                raise ConfigurationError(
                    f"Authentication failed during {operation}. Verify Supabase credentials and permissions."
                ) from e
            elif status == 409 or "23505" in combined or "duplicate key" in combined:
                raise DuplicateRecordError(
                    f"Unique constraint violation during {operation}: record already exists."
                ) from e
            elif "23503" in combined or "foreign key" in combined:
                raise ForeignKeyViolationError(
                    f"Foreign key constraint violation during {operation}: referenced record does not exist."
                ) from e
            elif "23514" in combined or "check constraint" in combined:
                raise ConstraintViolationError(
                    f"Check constraint violation during {operation}: invalid data values."
                ) from e
            elif status == 400:
                raise ConstraintViolationError(
                    f"Data validation error during {operation}: {msg or 'Invalid payload'}"
                ) from e
            elif status == 404:
                raise DatabaseUnavailableError(
                    f"Resource or table not found in Supabase schema during {operation}."
                ) from e
            elif status >= 500:
                raise DatabaseUnavailableError(
                    f"Supabase remote database error ({status}) during {operation}."
                ) from e
            else:
                raise RepositoryError(
                    f"Supabase request failed ({status}) during {operation}."
                ) from e
        elif isinstance(e, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)):
            raise DatabaseUnavailableError(
                f"Failed to connect to Supabase remote database during {operation}: network timeout or connection refused."
            ) from e
        elif isinstance(e, RepositoryError):
            raise e
        else:
            raise RepositoryError(f"Unexpected error during {operation}: {type(e).__name__}") from e

    # --------------------------------------------------------------------------
    # Customer Operations
    # --------------------------------------------------------------------------
    def insert_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts a new customer profile via PostgREST.
        Raises DuplicateRecordError if customer_id already exists.
        """
        customer_id = customer_data.get("customer_id")
        if not customer_id or not isinstance(customer_id, str):
            raise ConstraintViolationError("customer_id must be a valid non-empty string.")

        now_utc = datetime.now(timezone.utc).isoformat()
        payload = {
            "customer_id": str(customer_id),
            "customer_name": str(customer_data.get("customer_name", f"Customer {customer_id}")),
            "signup_date": str(customer_data.get("signup_date", "2024-01-01")),
            "city": customer_data.get("city"),
            "state": customer_data.get("state"),
            "snapshot_date": str(customer_data.get("snapshot_date", "2025-12-31")),
            "churn": int(customer_data.get("churn", 0)),
            "created_at": str(customer_data.get("created_at", now_utc)),
            "updated_at": str(customer_data.get("updated_at", now_utc)),
        }

        try:
            response = self._client.post(
                "/customers",
                json=payload,
                headers={"Prefer": "return=representation"},
            )
            response.raise_for_status()
            records = response.json()
            return records[0] if isinstance(records, list) and records else payload
        except Exception as e:
            self._handle_http_error(e, f"inserting customer '{customer_id}'")

    def upsert_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upserts an existing customer profile using PostgREST merge-duplicates.
        """
        customer_id = customer_data.get("customer_id")
        if not customer_id or not isinstance(customer_id, str):
            raise ConstraintViolationError("customer_id must be a valid non-empty string.")

        now_utc = datetime.now(timezone.utc).isoformat()
        payload = {
            "customer_id": str(customer_id),
            "customer_name": str(customer_data.get("customer_name", f"Customer {customer_id}")),
            "signup_date": str(customer_data.get("signup_date", "2024-01-01")),
            "city": customer_data.get("city"),
            "state": customer_data.get("state"),
            "snapshot_date": str(customer_data.get("snapshot_date", "2025-12-31")),
            "churn": int(customer_data.get("churn", 0)),
            "created_at": str(customer_data.get("created_at", now_utc)),
            "updated_at": str(customer_data.get("updated_at", now_utc)),
        }

        try:
            response = self._client.post(
                "/customers?on_conflict=customer_id",
                json=payload,
                headers={"Prefer": "resolution=merge-duplicates,return=representation"},
            )
            response.raise_for_status()
            records = response.json()
            return records[0] if isinstance(records, list) and records else payload
        except Exception as e:
            self._handle_http_error(e, f"upserting customer '{customer_id}'")

    def upsert_customers_batch(self, customers_data: List[Dict[str, Any]]) -> int:
        """
        Inserts or updates a batch of customer profiles via PostgREST bulk merge-duplicates.
        Returns the count of successfully processed records.
        """
        if not customers_data:
            return 0

        now_utc = datetime.now(timezone.utc).isoformat()
        payloads = []
        for item in customers_data:
            cid = item.get("customer_id")
            if not cid or not isinstance(cid, str):
                raise ConstraintViolationError("customer_id must be a valid non-empty string.")
            payloads.append({
                "customer_id": str(cid),
                "customer_name": str(item.get("customer_name", f"Customer {cid}")),
                "signup_date": str(item.get("signup_date", "2024-01-01")),
                "city": item.get("city"),
                "state": item.get("state"),
                "snapshot_date": str(item.get("snapshot_date", "2025-12-31")),
                "churn": int(item.get("churn", 0)),
                "created_at": str(item.get("created_at", now_utc)),
                "updated_at": str(item.get("updated_at", now_utc)),
            })

        try:
            response = self._client.post(
                "/customers?on_conflict=customer_id",
                json=payloads,
                headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
            )
            response.raise_for_status()
            return len(payloads)
        except Exception as e:
            self._handle_http_error(e, f"batch upserting {len(payloads)} customers")

    def get_existing_customer_ids(self) -> Set[str]:
        """
        Returns set of all customer IDs currently stored in Supabase.
        """
        try:
            response = self._client.get(
                "/customers",
                params={"select": "customer_id"},
            )
            response.raise_for_status()
            records = response.json()
            if isinstance(records, list):
                return {r["customer_id"] for r in records if "customer_id" in r}
            return set()
        except Exception as e:
            self._handle_http_error(e, "fetching existing customer IDs")

    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a customer profile by string customer_id.
        """
        try:
            response = self._client.get(
                "/customers",
                params={"customer_id": f"eq.{customer_id}", "select": "*"},
            )
            response.raise_for_status()
            records = response.json()
            return records[0] if isinstance(records, list) and records else None
        except Exception as e:
            self._handle_http_error(e, f"retrieving customer '{customer_id}'")

    def get_customer_count(self) -> int:
        """
        Returns total number of customers via PostgREST exact count.
        """
        try:
            response = self._client.get(
                "/customers",
                params={"select": "customer_id"},
                headers={"Prefer": "count=exact", "Range": "0-0"},
            )
            response.raise_for_status()
            content_range = response.headers.get("Content-Range", "")
            if "/" in content_range:
                total_str = content_range.split("/")[-1]
                if total_str.isdigit():
                    return int(total_str)
            records = response.json()
            return len(records) if isinstance(records, list) else 0
        except Exception as e:
            self._handle_http_error(e, "counting customers")

    def list_customers(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Returns a paginated list of customers ordered by customer_id.
        """
        try:
            response = self._client.get(
                "/customers",
                params={
                    "select": "*",
                    "order": "customer_id.asc",
                    "limit": str(limit),
                    "offset": str(offset),
                },
            )
            response.raise_for_status()
            records = response.json()
            return records if isinstance(records, list) else []
        except Exception as e:
            self._handle_http_error(e, "listing customers")

    # --------------------------------------------------------------------------
    # Prediction Operations
    # --------------------------------------------------------------------------
    def insert_prediction(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Records a machine learning churn prediction result for a customer.
        """
        prediction_id = prediction_data.get("prediction_id") or str(uuid.uuid4())
        customer_id = prediction_data.get("customer_id")
        if not customer_id or not isinstance(customer_id, str):
            raise ConstraintViolationError("customer_id must be a valid non-empty string.")

        now_utc = datetime.now(timezone.utc).isoformat()
        payload = {
            "prediction_id": str(prediction_id),
            "customer_id": str(customer_id),
            "churn_probability": float(prediction_data.get("churn_probability", 0.0)),
            "retention_probability": float(prediction_data.get("retention_probability", 0.0)),
            "predicted_churn": int(prediction_data.get("predicted_churn", 0)),
            "decision_threshold": float(prediction_data.get("decision_threshold", 0.50)),
            "risk_tier": str(prediction_data.get("risk_tier", "LOW")),
            "model_name": str(prediction_data.get("model_name", "RandomForestClassifier_ConfigD")),
            "model_version": str(prediction_data.get("model_version", "1.0.0")),
            "model_hash": str(
                prediction_data.get("model_hash", "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301")
            ),
            "prediction_timestamp": str(prediction_data.get("prediction_timestamp", now_utc)),
            "created_at": str(prediction_data.get("created_at", now_utc)),
        }

        try:
            response = self._client.post(
                "/customer_predictions",
                json=payload,
                headers={"Prefer": "return=representation"},
            )
            response.raise_for_status()
            records = response.json()
            return records[0] if isinstance(records, list) and records else payload
        except Exception as e:
            self._handle_http_error(e, f"recording prediction for customer '{customer_id}'")

    def get_prediction_history(self, customer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves prediction history for a customer ordered newest first.
        """
        try:
            response = self._client.get(
                "/customer_predictions",
                params={
                    "customer_id": f"eq.{customer_id}",
                    "order": "prediction_timestamp.desc",
                    "limit": str(limit),
                    "select": "*",
                },
            )
            response.raise_for_status()
            records = response.json()
            return records if isinstance(records, list) else []
        except Exception as e:
            self._handle_http_error(e, f"fetching prediction history for customer '{customer_id}'")

    def get_latest_prediction(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the most recent prediction for a customer.
        """
        history = self.get_prediction_history(customer_id, limit=1)
        return history[0] if history else None

    # --------------------------------------------------------------------------
    # Segmentation Operations
    # --------------------------------------------------------------------------
    def upsert_customer_segment(self, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assigns or updates a customer's RFM segment.
        If is_current is set to True/1, prior active segments are archived (is_current=False).
        """
        segment_record_id = segment_data.get("segment_record_id") or str(uuid.uuid4())
        customer_id = segment_data.get("customer_id")
        if not customer_id or not isinstance(customer_id, str):
            raise ConstraintViolationError("customer_id must be a valid non-empty string.")

        now_utc = datetime.now(timezone.utc).isoformat()
        is_current = bool(segment_data.get("is_current", True))

        payload = {
            "segment_record_id": str(segment_record_id),
            "customer_id": str(customer_id),
            "cluster_id": int(segment_data.get("cluster_id", 0)),
            "segment_name": str(segment_data.get("segment_name", "Champions & High-Value Loyalists")),
            "recency_delivered_days": float(segment_data.get("recency_delivered_days", 0.0)),
            "hist_delivered_order_count": int(segment_data.get("hist_delivered_order_count", 0)),
            "hist_delivered_order_value_inr": float(segment_data.get("hist_delivered_order_value_inr", 0.0)),
            "segmentation_model": str(segment_data.get("segmentation_model", "KMeans_RFM_K5")),
            "is_current": is_current,
            "created_at": str(segment_data.get("created_at", now_utc)),
            "updated_at": str(segment_data.get("updated_at", now_utc)),
        }

        try:
            # 1. Archive previous current segment if new segment is current
            if is_current:
                self._client.patch(
                    "/customer_segments",
                    params={"customer_id": f"eq.{customer_id}", "is_current": "eq.true"},
                    json={"is_current": False, "updated_at": now_utc},
                )

            # 2. Insert new segment record
            response = self._client.post(
                "/customer_segments",
                json=payload,
                headers={"Prefer": "return=representation"},
            )
            response.raise_for_status()
            records = response.json()
            return records[0] if isinstance(records, list) and records else payload
        except Exception as e:
            self._handle_http_error(e, f"assigning segment for customer '{customer_id}'")

    def get_current_segment(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the active segment assignment for a customer.
        """
        try:
            response = self._client.get(
                "/customer_segments",
                params={
                    "customer_id": f"eq.{customer_id}",
                    "is_current": "eq.true",
                    "select": "*",
                    "limit": "1",
                },
            )
            response.raise_for_status()
            records = response.json()
            return records[0] if isinstance(records, list) and records else None
        except Exception as e:
            self._handle_http_error(e, f"fetching active segment for customer '{customer_id}'")

    def get_segment_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all historical and active segments for a customer ordered newest first.
        """
        try:
            response = self._client.get(
                "/customer_segments",
                params={
                    "customer_id": f"eq.{customer_id}",
                    "order": "created_at.desc",
                    "select": "*",
                },
            )
            response.raise_for_status()
            records = response.json()
            return records if isinstance(records, list) else []
        except Exception as e:
            self._handle_http_error(e, f"fetching segment history for customer '{customer_id}'")

    # --------------------------------------------------------------------------
    # Recommendation Operations
    # --------------------------------------------------------------------------
    def insert_recommendation(self, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persists a retention recommendation for a customer.
        """
        recommendation_id = recommendation_data.get("recommendation_id") or str(uuid.uuid4())
        customer_id = recommendation_data.get("customer_id")
        if not customer_id or not isinstance(customer_id, str):
            raise ConstraintViolationError("customer_id must be a valid non-empty string.")

        now_utc = datetime.now(timezone.utc).isoformat()
        payload = {
            "recommendation_id": str(recommendation_id),
            "customer_id": str(customer_id),
            "prediction_id": recommendation_data.get("prediction_id"),
            "recommendation_category": str(recommendation_data.get("recommendation_category", "Retention Action")),
            "recommendation_title": str(recommendation_data.get("recommendation_title", "Intervention Plan")),
            "recommendation_description": str(recommendation_data.get("recommendation_description", "")),
            "evidence": str(recommendation_data.get("evidence", "")),
            "priority": str(recommendation_data.get("priority", "MEDIUM")),
            "recommendation_status": str(recommendation_data.get("recommendation_status", "PENDING")),
            "generated_at": str(recommendation_data.get("generated_at", now_utc)),
            "created_at": str(recommendation_data.get("created_at", now_utc)),
            "updated_at": str(recommendation_data.get("updated_at", now_utc)),
        }

        try:
            response = self._client.post(
                "/retention_recommendations",
                json=payload,
                headers={"Prefer": "return=representation"},
            )
            response.raise_for_status()
            records = response.json()
            return records[0] if isinstance(records, list) and records else payload
        except Exception as e:
            self._handle_http_error(e, f"persisting recommendation for customer '{customer_id}'")

    def get_recommendations(
        self, customer_id: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves recommendations for a customer, optionally filtered by status.
        """
        params = {
            "customer_id": f"eq.{customer_id}",
            "order": "created_at.desc",
            "select": "*",
        }
        if status:
            params["recommendation_status"] = f"eq.{status}"

        try:
            response = self._client.get("/retention_recommendations", params=params)
            response.raise_for_status()
            records = response.json()
            return records if isinstance(records, list) else []
        except Exception as e:
            self._handle_http_error(e, f"fetching recommendations for customer '{customer_id}'")

    def update_recommendation_status(
        self, recommendation_id: str, status: str
    ) -> Optional[Dict[str, Any]]:
        """
        Updates recommendation execution status.
        """
        valid_statuses = ("PENDING", "IN_PROGRESS", "APPLIED", "DISMISSED", "EXPIRED")
        if status not in valid_statuses:
            raise ConstraintViolationError(
                f"Invalid recommendation status '{status}'. Must be one of {valid_statuses}."
            )

        now_utc = datetime.now(timezone.utc).isoformat()
        try:
            response = self._client.patch(
                "/retention_recommendations",
                params={"recommendation_id": f"eq.{recommendation_id}"},
                json={"recommendation_status": status, "updated_at": now_utc},
                headers={"Prefer": "return=representation"},
            )
            response.raise_for_status()
            records = response.json()
            return records[0] if isinstance(records, list) and records else None
        except Exception as e:
            self._handle_http_error(e, f"updating status of recommendation '{recommendation_id}'")

    # --------------------------------------------------------------------------
    # Health Status
    # --------------------------------------------------------------------------
    def get_health_status(self) -> Dict[str, Any]:
        """
        Returns health and diagnostic connectivity status for Supabase storage.
        """
        try:
            # Probe customers table with 1-record limit
            response = self._client.get(
                "/customers",
                params={"select": "customer_id", "limit": "1"},
                headers={"Prefer": "count=exact"},
            )
            response.raise_for_status()
            content_range = response.headers.get("Content-Range", "")
            c_count = 0
            if "/" in content_range:
                tot = content_range.split("/")[-1]
                if tot.isdigit():
                    c_count = int(tot)

            return {
                "status": "healthy",
                "backend": "supabase",
                "is_connected": True,
                "project_url": self.url,
                "customer_count": c_count,
            }
        except Exception as e:
            logger.warning("Supabase health probe failed: %s", str(e))
            return {
                "status": "unavailable",
                "backend": "supabase",
                "is_connected": False,
                "project_url": self.url,
                "error": "Failed to connect to remote Supabase instance or schema not present.",
            }

    def get_storage_status(self) -> Dict[str, Any]:
        """
        Returns comprehensive storage diagnostic status for Supabase.
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        health = self.get_health_status()
        is_conn = health.get("is_connected", False)

        tables_found = []
        if is_conn:
            tables_found = ["customers"]

        return {
            "status": "healthy" if is_conn else "unavailable",
            "storage_mode": "supabase",
            "backend": "supabase",
            "is_connected": is_conn,
            "schema_ready": is_conn,
            "applied_migrations": [],
            "tables_available": tables_found,
            "table_counts": {"customers": health.get("customer_count", 0)} if is_conn else {},
            "database_version": "PostgreSQL (Supabase PostgREST)",
            "project_url": self.url,
            "error": health.get("error") if not is_conn else None,
            "timestamp": now_utc,
        }

    def get_customer_metrics(self) -> Dict[str, int]:
        """
        Returns aggregate customer counts from Supabase: total, churned, retained, and null city/state.
        """
        try:
            response = self._client.get(
                "/customers",
                params={"select": "churn,city,state"},
            )
            response.raise_for_status()
            rows = response.json()
            if not isinstance(rows, list):
                rows = []

            total = len(rows)
            churned = sum(1 for r in rows if r.get("churn") == 1)
            retained = sum(1 for r in rows if r.get("churn") == 0)
            null_city = sum(1 for r in rows if r.get("city") is None)
            null_state = sum(1 for r in rows if r.get("state") is None)

            return {
                "total_customers": total,
                "churned_customers": churned,
                "retained_customers": retained,
                "null_city_count": null_city,
                "null_state_count": null_state,
            }
        except Exception as e:
            self._handle_http_error(e, "querying customer metrics")

    # --------------------------------------------------------------------------
    # Employee Registry & Administration (Phase 8.4.5)
    # --------------------------------------------------------------------------
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves employee record by administrator-issued employee_id via PostgREST.
        """
        try:
            response = self._client.get(
                "/employee_registry",
                params={"employee_id": f"eq.{str(employee_id).strip()}", "select": "*"},
            )
            response.raise_for_status()
            records = response.json()
            return records[0] if records and isinstance(records, list) else None
        except Exception as e:
            self._handle_http_error(e, f"retrieving employee '{employee_id}'")

    def get_employee_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves employee record by work_email (case-insensitive).
        """
        try:
            response = self._client.get(
                "/employee_registry",
                params={"work_email": f"ilike.{str(email).strip().lower()}", "select": "*"},
            )
            response.raise_for_status()
            records = response.json()
            return records[0] if records and isinstance(records, list) else None
        except Exception as e:
            self._handle_http_error(e, f"retrieving employee by email '{email}'")

    def get_employee_by_supabase_user_id(self, supabase_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves employee record by Supabase Auth user UUID.
        """
        try:
            response = self._client.get(
                "/employee_registry",
                params={"supabase_user_id": f"eq.{str(supabase_user_id).strip()}", "select": "*"},
            )
            response.raise_for_status()
            records = response.json()
            return records[0] if records and isinstance(records, list) else None
        except Exception as e:
            self._handle_http_error(e, f"retrieving employee by supabase_user_id '{supabase_user_id}'")

    def create_employee_invitation(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates an administrator-issued employee invitation in the registry with status 'INVITED'.
        """
        emp_id = str(employee_data.get("employee_id", "")).strip()
        work_email = str(employee_data.get("work_email", "")).strip().lower()
        if not emp_id or not work_email:
            raise ConstraintViolationError("employee_id and work_email are required.")

        now_utc = datetime.now(timezone.utc).isoformat()
        record = {
            "employee_id": emp_id,
            "work_email": work_email,
            "full_name": employee_data.get("full_name"),
            "department": employee_data.get("department", "Customer Success"),
            "supabase_user_id": employee_data.get("supabase_user_id"),
            "status": employee_data.get("status", "INVITED"),
            "created_at": employee_data.get("created_at", now_utc),
            "registered_at": employee_data.get("registered_at"),
            "approved_at": employee_data.get("approved_at"),
            "approved_by": employee_data.get("approved_by"),
            "rejection_reason": employee_data.get("rejection_reason"),
            "notes": employee_data.get("notes"),
        }
        try:
            response = self._client.post("/employee_registry", json=record)
            response.raise_for_status()
            return record
        except Exception as e:
            self._handle_http_error(e, f"creating employee invitation '{emp_id}'")

    def register_employee(self, employee_id: str, supabase_user_id: str, work_email: str) -> Dict[str, Any]:
        """
        Updates an invited employee record upon applicant registration, setting status to 'PENDING'.
        """
        clean_id = str(employee_id).strip()
        clean_uid = str(supabase_user_id).strip()
        now_utc = datetime.now(timezone.utc).isoformat()
        payload = {
            "supabase_user_id": clean_uid,
            "status": "PENDING",
            "registered_at": now_utc,
        }
        try:
            response = self._client.patch(
                "/employee_registry",
                params={"employee_id": f"eq.{clean_id}"},
                json=payload,
            )
            response.raise_for_status()
            return self.get_employee_by_id(clean_id)
        except Exception as e:
            self._handle_http_error(e, f"registering employee '{clean_id}'")

    def update_employee_status(
        self,
        employee_id: str,
        status: str,
        admin_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates the approval/suspension status of an employee.
        """
        clean_id = str(employee_id).strip()
        clean_status = str(status).strip().upper()
        now_utc = datetime.now(timezone.utc).isoformat()

        payload = {"status": clean_status}
        if clean_status == "APPROVED":
            payload["approved_at"] = now_utc
            payload["approved_by"] = admin_id
        elif clean_status == "REJECTED":
            payload["rejection_reason"] = reason

        try:
            response = self._client.patch(
                "/employee_registry",
                params={"employee_id": f"eq.{clean_id}"},
                json=payload,
            )
            response.raise_for_status()
            return self.get_employee_by_id(clean_id)
        except Exception as e:
            self._handle_http_error(e, f"updating status for employee '{clean_id}'")

    def get_employee_stats(self) -> Dict[str, int]:
        """
        Returns aggregated counts of employees by status (total, pending, approved, rejected, suspended, invited).
        """
        try:
            response = self._client.get("/employee_registry", params={"select": "status"})
            response.raise_for_status()
            rows = response.json()
            stats = {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "suspended": 0, "invited": 0}
            if isinstance(rows, list):
                stats["total"] = len(rows)
                for r in rows:
                    st = str(r.get("status", "")).upper()
                    if st == "PENDING":
                        stats["pending"] += 1
                    elif st == "APPROVED":
                        stats["approved"] += 1
                    elif st == "REJECTED":
                        stats["rejected"] += 1
                    elif st == "SUSPENDED":
                        stats["suspended"] += 1
                    elif st == "INVITED":
                        stats["invited"] += 1
            return stats
        except Exception as e:
            self._handle_http_error(e, "fetching employee stats")

    def list_employees_by_status(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Lists employee records optionally filtered by status with pagination.
        """
        params = {
            "select": "*",
            "order": "created_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        }
        if status and status.strip().upper() not in ("ALL", ""):
            params["status"] = f"eq.{str(status).strip().upper()}"
        if search and search.strip():
            s = search.strip()
            params["or"] = f"(employee_id.ilike.%{s}%,work_email.ilike.%{s}%,full_name.ilike.%{s}%)"

        try:
            response = self._client.get("/employee_registry", params=params)
            response.raise_for_status()
            rows = response.json()
            return rows if isinstance(rows, list) else []
        except Exception as e:
            self._handle_http_error(e, "listing employee records")
