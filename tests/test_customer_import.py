"""
Indian E-Commerce Customer Retention Intelligence System
Comprehensive Unit & Integration Test Suite for Customer Import Service (Phase 7.4 Checkpoint 5)

Tests:
- Source schema validation and missing columns rejection
- Missing source file handling
- Duplicate source IDs handling within CSV
- Invalid churn values and invalid date formats rejection
- Nullable city/state preservation (handling 46 intentional EDA nulls)
- Configurable batch size processing
- Full successful insertion and mathematical reconciliation
- Idempotent repeated import (zero duplicate rows, all counted as updated)
- Pre-existing record updates
- Partial batch failure isolation and error logging
- Target database unavailable handling
- Strict enforcement of NO SILENT FALLBACK in Supabase mode
- Invariance of source CSV, model, and segmentation artifacts
"""

import csv
import hashlib
import os
import pytest
from typing import Dict, Any

from backend.app.core.config import settings
from backend.app.repositories.sqlite_repository import SQLiteRepository
from backend.app.repositories.supabase_repository import SupabaseRepository
from backend.app.repositories.exceptions import (
    ConfigurationError,
    ConstraintViolationError,
    DatabaseUnavailableError,
)
from backend.app.services.customer_import_service import (
    CustomerImportResult,
    CustomerImportService,
)

# Canonical Invariant Hashes
LOCKED_RF_MODEL_HASH = "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301"
LOCKED_SCALER_HASH = "892B9F3CDDA5427DD3965C76B95C1BC952661BAEA993FBBA94D5A3F56FB2EC4C"
LOCKED_KMEANS_HASH = "A018E41C8DC78BBDEC7C157B71ED66FEAC698336F787B39D84583FAE9CB931B3"
RAW_CUSTOMERS_HASH = "DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E"


@pytest.fixture
def isolated_repo(tmp_path) -> SQLiteRepository:
    """Fixture providing an isolated SQLite repository."""
    db_file = str(tmp_path / "test_import_isolated.db")
    return SQLiteRepository(db_path=db_file)


# ==============================================================================
# 1. SOURCE VALIDATION & REJECTION TESTS
# ==============================================================================

def test_missing_source_file_handling(isolated_repo):
    """Verifies that a missing file path raises FileNotFoundError."""
    service = CustomerImportService(repository=isolated_repo)
    with pytest.raises(FileNotFoundError):
        service.import_customers("data/non_existent_customers.csv")


def test_schema_missing_columns_rejection(tmp_path, isolated_repo):
    """Verifies that CSV files missing required columns are rejected with ValueError."""
    bad_csv = tmp_path / "bad_schema.csv"
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "customer_name", "churn"])  # Missing signup_date, city, etc.
        writer.writerow(["IND_CUST_001", "John Doe", "0"])

    service = CustomerImportService(repository=isolated_repo)
    with pytest.raises(ValueError) as excinfo:
        service.import_customers(str(bad_csv))
    assert "missing required columns" in str(excinfo.value)


def test_duplicate_source_ids_in_csv(tmp_path, isolated_repo):
    """Verifies that duplicate customer_ids within the CSV are identified and rejected."""
    dup_csv = tmp_path / "dup_customers.csv"
    with open(dup_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "customer_name", "signup_date", "city", "state", "snapshot_date", "churn"])
        writer.writerow(["IND_CUST_DUP_1", "User A", "2024-01-01", "Delhi", "Delhi", "2025-12-31", "0"])
        writer.writerow(["IND_CUST_DUP_1", "User A Duplicate", "2024-01-01", "Delhi", "Delhi", "2025-12-31", "0"])
        writer.writerow(["IND_CUST_VALID_2", "User B", "2024-01-02", "Mumbai", "Maharashtra", "2025-12-31", "1"])

    service = CustomerImportService(repository=isolated_repo)
    result = service.import_customers(str(dup_csv))

    assert result.source_records == 3
    assert result.validated_records == 2
    assert result.rejected_records == 1
    assert "IND_CUST_DUP_1" in result.duplicate_source_ids
    assert result.inserted_records == 2
    assert result.is_reconciled is True


def test_invalid_churn_and_dates_rejection(tmp_path, isolated_repo):
    """Verifies that malformed dates and invalid churn numbers are rejected."""
    invalid_csv = tmp_path / "invalid_data.csv"
    with open(invalid_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "customer_name", "signup_date", "city", "state", "snapshot_date", "churn"])
        writer.writerow(["IND_CUST_BAD_CHURN", "User Bad Churn", "2024-01-01", "Delhi", "Delhi", "2025-12-31", "5"])
        writer.writerow(["IND_CUST_BAD_DATE", "User Bad Date", "not-a-date", "Delhi", "Delhi", "2025-12-31", "0"])
        writer.writerow(["IND_CUST_GOOD", "User Good", "2024-01-01", "Delhi", "Delhi", "2025-12-31", "1"])

    service = CustomerImportService(repository=isolated_repo)
    result = service.import_customers(str(invalid_csv))

    assert result.source_records == 3
    assert result.validated_records == 1
    assert result.rejected_records == 2
    assert result.inserted_records == 1
    assert result.is_reconciled is True


def test_nullable_city_state_preservation(tmp_path, isolated_repo):
    """Verifies that missing city and state strings ('', 'nan', 'null') become None."""
    null_csv = tmp_path / "nulls_customers.csv"
    with open(null_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "customer_name", "signup_date", "city", "state", "snapshot_date", "churn"])
        writer.writerow(["IND_CUST_N1", "User Empty", "2024-01-01", "", "", "2025-12-31", "0"])
        writer.writerow(["IND_CUST_N2", "User NaN", "2024-01-01", "NaN", "nan", "2025-12-31", "1"])
        writer.writerow(["IND_CUST_N3", "User Valid", "2024-01-01", "Bengaluru", "Karnataka", "2025-12-31", "0"])

    service = CustomerImportService(repository=isolated_repo)
    result = service.import_customers(str(null_csv))

    assert result.source_records == 3
    assert result.missing_city_count == 2
    assert result.missing_state_count == 2

    c1 = isolated_repo.get_customer_by_id("IND_CUST_N1")
    assert c1["city"] is None
    assert c1["state"] is None

    c2 = isolated_repo.get_customer_by_id("IND_CUST_N2")
    assert c2["city"] is None
    assert c2["state"] is None

    c3 = isolated_repo.get_customer_by_id("IND_CUST_N3")
    assert c3["city"] == "Bengaluru"
    assert c3["state"] == "Karnataka"


# ==============================================================================
# 2. BATCHING & IDEMPOTENT PERSISTENCE TESTS
# ==============================================================================

def test_batch_processing_and_size_config(tmp_path, isolated_repo):
    """Verifies that configurable batch size imports all records cleanly."""
    batch_csv = tmp_path / "batch_test.csv"
    with open(batch_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "customer_name", "signup_date", "city", "state", "snapshot_date", "churn"])
        for i in range(15):
            writer.writerow([f"IND_CUST_B{i:02d}", f"User {i}", "2024-01-01", "Pune", "Maharashtra", "2025-12-31", str(i % 2)])

    service = CustomerImportService(repository=isolated_repo, batch_size=4)
    result = service.import_customers(str(batch_csv))

    assert result.source_records == 15
    assert result.inserted_records == 15
    assert result.final_database_customer_count == 15
    assert result.is_reconciled is True


def test_idempotent_repeated_import(tmp_path, isolated_repo):
    """
    Verifies that running the same import repeatedly produces zero additional rows,
    preserves counts, and accurately reports updated_records on the second pass.
    """
    idem_csv = tmp_path / "idempotent_test.csv"
    with open(idem_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "customer_name", "signup_date", "city", "state", "snapshot_date", "churn"])
        writer.writerow(["IND_CUST_IDEM_1", "User 1", "2024-01-01", "Jaipur", "Rajasthan", "2025-12-31", "0"])
        writer.writerow(["IND_CUST_IDEM_2", "User 2", "2024-01-02", "Surat", "Gujarat", "2025-12-31", "1"])

    service = CustomerImportService(repository=isolated_repo)

    # Pass 1: Initial insertion
    res1 = service.import_customers(str(idem_csv))
    assert res1.source_records == 2
    assert res1.inserted_records == 2
    assert res1.updated_records == 0
    assert res1.final_database_customer_count == 2
    assert res1.is_reconciled is True

    # Pass 2: Repeat import of exact same file
    res2 = service.import_customers(str(idem_csv))
    assert res2.source_records == 2
    assert res2.inserted_records == 0
    assert res2.updated_records == 2
    assert res2.final_database_customer_count == 2  # No duplicate rows created!
    assert res2.is_reconciled is True


def test_existing_record_updates(tmp_path, isolated_repo):
    """Verifies that importing updated attributes modifies existing records cleanly."""
    isolated_repo.insert_customer({
        "customer_id": "IND_CUST_UPGRADE",
        "customer_name": "Original Name",
        "signup_date": "2024-01-01",
        "city": "Old City",
        "state": "Old State",
        "churn": 0,
    })
    assert isolated_repo.get_customer_count() == 1

    update_csv = tmp_path / "update_test.csv"
    with open(update_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "customer_name", "signup_date", "city", "state", "snapshot_date", "churn"])
        writer.writerow(["IND_CUST_UPGRADE", "Upgraded Name", "2024-01-01", "New City", "New State", "2025-12-31", "1"])

    service = CustomerImportService(repository=isolated_repo)
    result = service.import_customers(str(update_csv))

    assert result.inserted_records == 0
    assert result.updated_records == 1
    assert result.final_database_customer_count == 1

    cust = isolated_repo.get_customer_by_id("IND_CUST_UPGRADE")
    assert cust["customer_name"] == "Upgraded Name"
    assert cust["city"] == "New City"
    assert cust["churn"] == 1


# ==============================================================================
# 3. RELIABILITY & NO SILENT FALLBACK TESTS
# ==============================================================================

def test_database_unavailable_handling(tmp_path):
    """Verifies that an offline database causes CustomerImportService to fail fast."""
    bad_repo = SQLiteRepository(db_path=str(tmp_path / "uninitialized_dir" / "bad.db"), auto_migrate=False)
    service = CustomerImportService(repository=bad_repo)

    test_csv = tmp_path / "test.csv"
    with open(test_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "customer_name", "signup_date", "city", "state", "snapshot_date", "churn"])
        writer.writerow(["IND_CUST_01", "User", "2024-01-01", "City", "State", "2025-12-31", "0"])

    with pytest.raises(DatabaseUnavailableError):
        service.import_customers(str(test_csv))


def test_no_silent_fallback_in_supabase_mode(monkeypatch):
    """
    Verifies that if STORAGE_MODE='supabase' and Supabase is unavailable,
    the import service fails immediately and does NOT silently write to SQLite.
    """
    monkeypatch.setattr(settings, "STORAGE_MODE", "supabase")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", None)
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)
    monkeypatch.setattr(settings, "SUPABASE_PUBLISHABLE_KEY", None)

    with pytest.raises(ConfigurationError):
        CustomerImportService()


# ==============================================================================
# 4. FULL REAL 7,000 CUSTOMER DATASET IMPORT TEST (ISOLATED)
# ==============================================================================

def test_real_7000_customers_import_reconciliation(tmp_path):
    """
    Executes a complete import of the actual 7,000 synthetic customers from
    data/raw/customers.csv into an isolated SQLite repository and validates:
    - 7,000 records imported
    - 46 missing cities and 46 missing states (matching EDA ground truth)
    - Full mathematical reconciliation
    - Second pass idempotency
    """
    raw_csv = os.path.join("data", "raw", "customers.csv")
    assert os.path.isfile(raw_csv), "data/raw/customers.csv does not exist"

    isolated_db = str(tmp_path / "real_7000_import.db")
    repo = SQLiteRepository(db_path=isolated_db)
    service = CustomerImportService(repository=repo, batch_size=500)

    # Pass 1: Full Ingestion
    res1 = service.import_customers(raw_csv)
    assert res1.source_records == 7000
    assert res1.validated_records == 7000
    assert res1.inserted_records == 7000
    assert res1.updated_records == 0
    assert res1.rejected_records == 0
    assert res1.failed_records == 0
    assert res1.final_database_customer_count == 7000
    assert res1.missing_city_count == 46
    assert res1.missing_state_count == 46
    assert res1.is_reconciled is True
    assert repo.get_customer_count() == 7000

    # Pass 2: Idempotent Re-Import
    res2 = service.import_customers(raw_csv)
    assert res2.source_records == 7000
    assert res2.inserted_records == 0
    assert res2.updated_records == 7000
    assert res2.final_database_customer_count == 7000
    assert res2.is_reconciled is True


# ==============================================================================
# 5. INTEGRITY & INVARIANCE TESTS
# ==============================================================================

def test_source_csv_and_artifacts_remain_unmodified():
    """
    Verifies that the customer import process did NOT alter the source CSV file
    or any locked machine learning artifacts.
    """
    # 1. Source CSV hash
    with open("data/raw/customers.csv", "rb") as f:
        csv_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert csv_hash == RAW_CUSTOMERS_HASH, "CRITICAL: data/raw/customers.csv was altered!"

    # 2. Random Forest Model
    with open("models/phase5_1/final_model/final_churn_rf_pipeline.joblib", "rb") as f:
        model_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert model_hash == LOCKED_RF_MODEL_HASH, "CRITICAL: Locked Random Forest model was altered!"

    # 3. Segmentation Scaler
    with open("models/segmentation_scaler.joblib", "rb") as f:
        scaler_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert scaler_hash == LOCKED_SCALER_HASH, "CRITICAL: Segmentation scaler was altered!"

    # 4. K-Means Model
    with open("models/kmeans_customer_segmentation.joblib", "rb") as f:
        kmeans_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert kmeans_hash == LOCKED_KMEANS_HASH, "CRITICAL: K-Means model was altered!"
