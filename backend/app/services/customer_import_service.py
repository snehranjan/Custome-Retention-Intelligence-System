"""
Indian E-Commerce Customer Retention Intelligence System
Customer Data Import & Reconciliation Service (Phase 7.4 Checkpoint 5)

Provides robust, idempotent, auditable, and non-destructive customer data ingestion
from CSV sources into persistent storage (SQLite or Supabase) using BaseRepository.
Enforces strict pre-import schema validation, batching, and exact mathematical reconciliation:
source_records == inserted + updated + rejected + skipped + failed.
"""

import csv
from dataclasses import dataclass, field
from datetime import datetime
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.core.logging import logger
from backend.app.repositories.base_repository import BaseRepository
from backend.app.repositories import get_repository
from backend.app.repositories.exceptions import (
    ConstraintViolationError,
    DatabaseUnavailableError,
    RepositoryError,
)

EXPECTED_COLUMNS = {
    "customer_id",
    "customer_name",
    "signup_date",
    "city",
    "state",
    "snapshot_date",
    "churn",
}


@dataclass
class CustomerImportResult:
    """Detailed reconciliation report for customer import operations."""
    source_records: int
    validated_records: int
    inserted_records: int
    updated_records: int
    rejected_records: int
    skipped_records: int
    failed_records: int
    final_database_customer_count: int
    missing_city_count: int
    missing_state_count: int
    duplicate_source_ids: List[str] = field(default_factory=list)
    rejected_details: List[Dict[str, Any]] = field(default_factory=list)
    failed_details: List[Dict[str, Any]] = field(default_factory=list)
    backend: str = "sqlite"
    execution_time_seconds: float = 0.0

    @property
    def is_reconciled(self) -> bool:
        """Verifies exact source partition equality."""
        return self.source_records == (
            self.inserted_records
            + self.updated_records
            + self.rejected_records
            + self.skipped_records
            + self.failed_records
        )

    def to_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable dictionary representation."""
        return {
            "source_records": self.source_records,
            "validated_records": self.validated_records,
            "inserted_records": self.inserted_records,
            "updated_records": self.updated_records,
            "rejected_records": self.rejected_records,
            "skipped_records": self.skipped_records,
            "failed_records": self.failed_records,
            "final_database_customer_count": self.final_database_customer_count,
            "missing_city_count": self.missing_city_count,
            "missing_state_count": self.missing_state_count,
            "duplicate_source_ids": self.duplicate_source_ids,
            "is_reconciled": self.is_reconciled,
            "backend": self.backend,
            "execution_time_seconds": round(self.execution_time_seconds, 3),
        }


class CustomerImportService:
    """
    Enterprise customer data import service handling validation, batch processing,
    deduplication, and idempotent upserting into the repository abstraction.
    """

    def __init__(
        self,
        repository: Optional[BaseRepository] = None,
        batch_size: int = 500,
    ):
        """
        Initializes the service with the active repository and configurable batch size.
        """
        self.repository = repository or get_repository()
        self.batch_size = max(1, batch_size)

    def validate_csv(
        self, file_path: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """
        Reads and validates source CSV rows.
        Returns:
            - validated_records: Cleaned rows ready for persistence
            - rejected_records: Malformed rows with error diagnostics
            - duplicate_source_ids: Duplicate customer_ids found within the source CSV
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Customer source CSV not found at: {file_path}")

        validated: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        seen_ids: Set[str] = set()
        duplicate_ids: List[str] = []

        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("Source CSV file is completely empty or has no header.")

            headers = set(reader.fieldnames)
            missing_cols = EXPECTED_COLUMNS - headers
            if missing_cols:
                raise ValueError(f"Source CSV is missing required columns: {missing_cols}")

            for row_idx, row in enumerate(reader, start=2):  # Line 2 is first data row
                cid = (row.get("customer_id") or "").strip()
                cname = (row.get("customer_name") or "").strip()
                signup = (row.get("signup_date") or "").strip()
                snapshot = (row.get("snapshot_date") or "").strip() or "2025-12-31"
                churn_raw = (row.get("churn") or "").strip()
                city_raw = (row.get("city") or "").strip()
                state_raw = (row.get("state") or "").strip()

                # 1. Validate customer_id presence
                if not cid:
                    rejected.append({
                        "row": row_idx,
                        "customer_id": cid,
                        "reason": "Missing customer_id",
                    })
                    continue

                # 2. Check for duplicate IDs within CSV
                if cid in seen_ids:
                    duplicate_ids.append(cid)
                    rejected.append({
                        "row": row_idx,
                        "customer_id": cid,
                        "reason": f"Duplicate customer_id '{cid}' in source file",
                    })
                    continue
                seen_ids.add(cid)

                # 3. Validate customer_name
                if not cname:
                    rejected.append({
                        "row": row_idx,
                        "customer_id": cid,
                        "reason": "Missing customer_name",
                    })
                    continue

                # 4. Validate signup_date format
                try:
                    datetime.strptime(signup, "%Y-%m-%d")
                except ValueError:
                    rejected.append({
                        "row": row_idx,
                        "customer_id": cid,
                        "reason": f"Invalid signup_date '{signup}'. Expected YYYY-MM-DD",
                    })
                    continue

                # 5. Validate snapshot_date format
                try:
                    datetime.strptime(snapshot, "%Y-%m-%d")
                except ValueError:
                    rejected.append({
                        "row": row_idx,
                        "customer_id": cid,
                        "reason": f"Invalid snapshot_date '{snapshot}'. Expected YYYY-MM-DD",
                    })
                    continue

                # 6. Validate churn value
                if churn_raw not in ("0", "1"):
                    rejected.append({
                        "row": row_idx,
                        "customer_id": cid,
                        "reason": f"Invalid churn '{churn_raw}'. Expected 0 or 1",
                    })
                    continue
                churn_val = int(churn_raw)

                # 7. Normalize nullable city & state
                city = None if city_raw.lower() in ("", "nan", "null", "none") else city_raw
                state = None if state_raw.lower() in ("", "nan", "null", "none") else state_raw

                validated.append({
                    "customer_id": cid,
                    "customer_name": cname,
                    "signup_date": signup,
                    "city": city,
                    "state": state,
                    "snapshot_date": snapshot,
                    "churn": churn_val,
                })

        return validated, rejected, duplicate_ids

    def import_customers(
        self, file_path: str = os.path.join("data", "raw", "customers.csv")
    ) -> CustomerImportResult:
        """
        Executes pre-import validation, database reconciliation, batch upserting,
        and post-import verification.
        """
        start_time = time.perf_counter()

        # Step 1: Pre-import database readiness check
        health = self.repository.get_health_status()
        backend_name = health.get("backend", "unknown")
        if not health.get("is_connected", False):
            raise DatabaseUnavailableError(
                f"Selected database storage backend ({backend_name}) is unavailable or offline: "
                f"{health.get('error', 'Health check failed')}"
            )

        # Step 2: Validate source CSV
        validated_records, rejected_records, duplicate_ids = self.validate_csv(file_path)
        source_count = len(validated_records) + len(rejected_records)

        # Step 3: Pre-import comparison against existing IDs
        existing_ids = self.repository.get_existing_customer_ids()

        inserted_count = 0
        updated_count = 0
        failed_records: List[Dict[str, Any]] = []

        # Step 4: Batch processing
        for i in range(0, len(validated_records), self.batch_size):
            batch = validated_records[i : i + self.batch_size]
            batch_existing = [r for r in batch if r["customer_id"] in existing_ids]
            batch_new = [r for r in batch if r["customer_id"] not in existing_ids]

            try:
                # Attempt fast bulk batch upsert
                self.repository.upsert_customers_batch(batch)
                inserted_count += len(batch_new)
                updated_count += len(batch_existing)
            except Exception as batch_err:
                logger.warning(
                    "Batch upsert failed on slice [%d:%d], falling back to row-by-row isolation: %s",
                    i,
                    i + len(batch),
                    str(batch_err),
                )
                # Fallback to row-by-row within the failed batch to isolate bad records
                for record in batch:
                    cid = record["customer_id"]
                    try:
                        self.repository.upsert_customer(record)
                        if cid in existing_ids:
                            updated_count += 1
                        else:
                            inserted_count += 1
                    except Exception as row_err:
                        failed_records.append({
                            "customer_id": cid,
                            "error": str(row_err),
                        })

        # Step 5: Post-import verification & metrics
        final_customer_count = self.repository.get_customer_count()
        missing_city_count = sum(1 for r in validated_records if r["city"] is None)
        missing_state_count = sum(1 for r in validated_records if r["state"] is None)
        exec_time = time.perf_counter() - start_time

        result = CustomerImportResult(
            source_records=source_count,
            validated_records=len(validated_records),
            inserted_records=inserted_count,
            updated_records=updated_count,
            rejected_records=len(rejected_records),
            skipped_records=0,
            failed_records=len(failed_records),
            final_database_customer_count=final_customer_count,
            missing_city_count=missing_city_count,
            missing_state_count=missing_state_count,
            duplicate_source_ids=duplicate_ids,
            rejected_details=rejected_records,
            failed_details=failed_records,
            backend=backend_name,
            execution_time_seconds=exec_time,
        )

        logger.info(
            "Customer import finished: %d source, %d inserted, %d updated, %d rejected, %d failed. Reconciled: %s",
            result.source_records,
            result.inserted_records,
            result.updated_records,
            result.rejected_records,
            result.failed_records,
            result.is_reconciled,
        )

        return result
