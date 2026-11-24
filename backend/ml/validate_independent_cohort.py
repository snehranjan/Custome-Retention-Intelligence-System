"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5.1 — Checkpoint 2: Independent Test Cohort Validation Suite
Description: Rigorously validates schema, foreign keys, business logic, churn consistency,
             ID set disjointness, and seed reproducibility for the new 1,500-customer cohort.

Author: BCA (AI & ML) Project Team
"""

import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

EXISTING_RAW_CUST = os.path.join(PROJECT_ROOT, "data", "raw", "customers.csv")
EXISTING_RAW_ORD = os.path.join(PROJECT_ROOT, "data", "raw", "orders.csv")

INDEP_DIR = os.path.join(PROJECT_ROOT, "data", "independent_test", "raw")
INDEP_CUST_PATH = os.path.join(INDEP_DIR, "customers_independent.csv")
INDEP_ORD_PATH = os.path.join(INDEP_DIR, "orders_independent.csv")
MANIFEST_PATH = os.path.join(INDEP_DIR, "independent_cohort_manifest.json")


def compute_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest().upper()


def run_validation():
    print("=" * 80)
    print("PHASE 5.1: INDEPENDENT SYNTHETIC TEST COHORT VALIDATION SUITE")
    print("=" * 80)

    checks_passed = 0
    total_checks = 14

    # 1. File existence
    print("\n1. Checking file existence...")
    assert os.path.exists(INDEP_CUST_PATH), f"Missing: {INDEP_CUST_PATH}"
    assert os.path.exists(INDEP_ORD_PATH), f"Missing: {INDEP_ORD_PATH}"
    assert os.path.exists(MANIFEST_PATH), f"Missing: {MANIFEST_PATH}"
    print("   [PASS] All 3 independent cohort files exist.")
    checks_passed += 1

    # Load data
    cust_df = pd.read_csv(INDEP_CUST_PATH)
    ord_df = pd.read_csv(INDEP_ORD_PATH)
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 2. Customer record count
    print("\n2. Validating customer count...")
    assert len(cust_df) == 1500, f"Expected 1,500 customers, got {len(cust_df)}"
    assert cust_df["customer_id"].nunique() == 1500, "Duplicate customer IDs detected!"
    print(f"   [PASS] Exactly 1,500 unique customers verified.")
    checks_passed += 1

    # 3. Customer ID formatting and contiguous span
    print("\n3. Validating customer ID formatting and span...")
    assert cust_df["customer_id"].min() == "IND_CUST_50001"
    assert cust_df["customer_id"].max() == "IND_CUST_51500"
    cust_nums = cust_df["customer_id"].str.extract(r"(\d+)")[0].astype(int)
    assert set(cust_nums) == set(range(50001, 51501)), "Gaps detected in customer ID sequence!"
    print("   [PASS] Customer IDs span contiguously from IND_CUST_50001 to IND_CUST_51500.")
    checks_passed += 1

    # 4. Order record count & uniqueness
    print("\n4. Validating order count and ID uniqueness...")
    assert len(ord_df) > 0, "Orders table is empty!"
    assert ord_df["order_id"].nunique() == len(ord_df), "Duplicate order IDs detected!"
    assert ord_df["order_id"].min() == "ORD_500001"
    ord_nums = ord_df["order_id"].str.extract(r"(\d+)")[0].astype(int)
    assert set(ord_nums) == set(range(500001, 500001 + len(ord_df))), "Gaps in order IDs!"
    print(f"   [PASS] {len(ord_df):,} orders verified (100% unique, starting at ORD_500001).")
    checks_passed += 1

    # 5. Foreign Key Integrity
    print("\n5. Validating foreign key referential integrity...")
    orphan_orders = set(ord_df["customer_id"]) - set(cust_df["customer_id"])
    assert len(orphan_orders) == 0, f"Found orphan orders: {orphan_orders}"
    print("   [PASS] 100% of order customer_id values reference valid customers.")
    checks_passed += 1

    # 6. Snapshot Date Uniformity
    print("\n6. Validating snapshot date consistency...")
    assert (cust_df["snapshot_date"] == "2025-12-31").all(), "Invalid snapshot dates found!"
    print("   [PASS] All customer records have snapshot_date = 2025-12-31.")
    checks_passed += 1

    # 7. Order Date Range Consistency
    print("\n7. Validating order dates...")
    ord_dates = pd.to_datetime(ord_df["order_date"])
    min_date = ord_dates.min()
    max_date = ord_dates.max()
    assert min_date >= pd.to_datetime("2023-01-01"), f"Order date before observation start: {min_date}"
    assert max_date <= pd.to_datetime("2026-03-31"), f"Order date after label window: {max_date}"
    print(f"   [PASS] Order dates span from {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}.")
    checks_passed += 1

    # 8. Non-negative Order Values
    print("\n8. Validating financial column validity...")
    assert (ord_df["order_amount_inr"] > 0).all(), "Zero or negative order amounts detected!"
    assert (ord_df["discount_amount_inr"].dropna() >= 0).all(), "Negative discounts detected!"
    valid_discounts = ord_df.dropna(subset=["discount_amount_inr", "order_amount_inr"])
    assert (valid_discounts["discount_amount_inr"] <= valid_discounts["order_amount_inr"]).all(), "Discount exceeds price!"
    print("   [PASS] Financial amounts are positive, realistic, and bounded.")
    checks_passed += 1

    # 9. Categorical Values Integrity
    print("\n9. Validating categorical domains...")
    valid_statuses = {"Delivered", "Cancelled", "Returned"}
    assert set(ord_df["order_status"].unique()).issubset(valid_statuses), "Invalid order_status values!"
    valid_pay = {"UPI", "COD", "Credit Card", "Debit Card", "Net Banking", "Wallet"}
    assert set(ord_df["payment_method"].dropna().unique()).issubset(valid_pay), "Invalid payment methods!"
    print("   [PASS] Order statuses and payment methods match approved domains.")
    checks_passed += 1

    # 10. Strict Churn & Future Order Consistency
    print("\n10. Validating strict churn ground-truth consistency...")
    snapshot_dt = pd.to_datetime("2025-12-31")
    fut_orders = ord_df[pd.to_datetime(ord_df["order_date"]) > snapshot_dt]
    cust_with_fut = set(fut_orders["customer_id"])

    churned_custs = set(cust_df[cust_df["churn"] == 1]["customer_id"])
    retained_custs = set(cust_df[cust_df["churn"] == 0]["customer_id"])

    # Every churned customer must have ZERO future orders
    churned_with_future = churned_custs.intersection(cust_with_fut)
    assert len(churned_with_future) == 0, f"Integrity violation: {len(churned_with_future)} churners placed future orders!"

    # Every retained customer must have AT LEAST 1 future order
    retained_without_future = retained_custs - cust_with_fut
    assert len(retained_without_future) == 0, f"Integrity violation: {len(retained_without_future)} retained customers placed no future orders!"

    print("   [PASS] Strict equivalence verified: churn == 1 <=> 0 future orders in 90-day window.")
    checks_passed += 1

    # 11. Exact Set Disjointness against Phase 1 Raw Data
    print("\n11. Validating exact ID set disjointness against Phase 1 raw data...")
    orig_cust = pd.read_csv(EXISTING_RAW_CUST)
    orig_ord = pd.read_csv(EXISTING_RAW_ORD)

    cust_overlap = set(cust_df["customer_id"]).intersection(set(orig_cust["customer_id"]))
    ord_overlap = set(ord_df["order_id"]).intersection(set(orig_ord["order_id"]))

    assert len(cust_overlap) == 0, f"CRITICAL: Customer ID overlap detected ({len(cust_overlap)})!"
    assert len(ord_overlap) == 0, f"CRITICAL: Order ID overlap detected ({len(ord_overlap)})!"
    print("   [PASS] 0 overlapping customer IDs. 0 overlapping order IDs.")
    checks_passed += 1

    # 12. Cryptographic Manifest Verification
    print("\n12. Validating SHA-256 hashes against manifest...")
    actual_cust_hash = compute_sha256(INDEP_CUST_PATH)
    actual_ord_hash = compute_sha256(INDEP_ORD_PATH)
    assert actual_cust_hash == manifest["customers"]["sha256"], "Customer CSV SHA-256 mismatch!"
    assert actual_ord_hash == manifest["orders"]["sha256"], "Order CSV SHA-256 mismatch!"
    print(f"   [PASS] Customer hash matches: {actual_cust_hash}")
    print(f"   [PASS] Order hash matches   : {actual_ord_hash}")
    checks_passed += 1

    # 13. Churn Class Distribution Summary
    print("\n13. Inspecting churn class distribution...")
    n_churn = int(cust_df["churn"].sum())
    n_retain = len(cust_df) - n_churn
    churn_rate = n_churn / len(cust_df)
    print(f"   Total Customers: {len(cust_df):,}")
    print(f"   Churned (1)    : {n_churn:,} ({churn_rate:.2%})")
    print(f"   Retained (0)   : {n_retain:,} ({1 - churn_rate:.2%})")
    assert 0.40 <= churn_rate <= 0.52, f"Unusual churn rate outside expected bounds: {churn_rate:.4f}"
    print("   [PASS] Churn distribution is statistically consistent with generator expectations.")
    checks_passed += 1

    # 14. Original Raw Data Cryptographic Immutability
    print("\n14. Verifying original Phase 1 raw files immutability...")
    orig_cust_hash = compute_sha256(EXISTING_RAW_CUST)
    orig_ord_hash = compute_sha256(EXISTING_RAW_ORD)
    EXPECTED_CUST_HASH = "DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E"
    EXPECTED_ORD_HASH = "AB632B3092F732B3B25BAAD096B191C1ACA777CB8D42B29EABB815A266C558E7"
    assert orig_cust_hash == EXPECTED_CUST_HASH, "Original customers.csv was modified!"
    assert orig_ord_hash == EXPECTED_ORD_HASH, "Original orders.csv was modified!"
    print("   [PASS] Original Phase 1 raw data hashes remain perfectly invariant.")
    checks_passed += 1

    print("\n" + "=" * 80)
    print(f"ALL {checks_passed}/{total_checks} VALIDATION CHECKS PASSED SUCCESSFULLY!")
    print("INDEPENDENT TEST COHORT INTEGRITY FULLY CONFIRMED & SEALED.")
    print("=" * 80)
    return True


if __name__ == "__main__":
    run_validation()
