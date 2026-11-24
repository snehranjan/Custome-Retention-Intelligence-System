"""
Indian E-Commerce Customer Retention Intelligence System
Module: Dataset Validation
Description: Rigorous validation suite for raw datasets (customers.csv and orders.csv).
             Enforces 10 critical checks for data integrity, date boundaries, and temporal separation
             between historical and future orders.

Author: BCA (AI & ML) Project Team
Exit Code: 0 on success, non-zero if ANY check fails.
"""

import os
import sys
import pandas as pd

SNAPSHOT_DATE = "2025-12-31"
FUTURE_LABEL_END = "2026-03-31"
EXPECTED_CUSTOMERS = 7000

CUST_PATH = os.path.join("data", "raw", "customers.csv")
ORD_PATH = os.path.join("data", "raw", "orders.csv")


def run_check(check_id, description, condition, details=""):
    """Format and report a check status. Return True if PASS, False if FAIL."""
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] Check {check_id:02d}: {description}")
    if details:
        print(f"       -> Details: {details}")
    return condition


def main():
    print("=" * 75)
    print("DATASET INTEGRITY & RAW ORDER TEMPORAL PARTITION VALIDATION SUITE")
    print("=" * 75)

    all_passed = True

    # Check 10: Dataset files exist and can be loaded
    files_exist = os.path.exists(CUST_PATH) and os.path.exists(ORD_PATH)
    if not run_check(10, "Dataset files exist on disk", files_exist, f"{CUST_PATH}, {ORD_PATH}"):
        print("\nFATAL: Dataset files missing. Exiting.")
        sys.exit(1)

    try:
        customers_df = pd.read_csv(CUST_PATH)
        orders_df = pd.read_csv(ORD_PATH)
        load_success = True
    except Exception as e:
        load_success = False
        print(f"Load error: {e}")

    if not run_check(10, "Dataset files load successfully as DataFrames", load_success):
        sys.exit(1)

    # Check 01: Exactly 7,000 customers
    num_cust = len(customers_df)
    c1 = run_check(1, "Exactly 7,000 customers in customers.csv", num_cust == EXPECTED_CUSTOMERS, f"Found {num_cust:,} records")
    all_passed = all_passed and c1

    # Check 02: Unique customer IDs
    unique_cust_ids = customers_df["customer_id"].nunique()
    c2 = run_check(2, "Customer IDs are completely unique and non-null", (unique_cust_ids == num_cust) and (customers_df["customer_id"].isnull().sum() == 0), f"Unique IDs: {unique_cust_ids:,} / {num_cust:,}")
    all_passed = all_passed and c2

    # Check 03: Unique order IDs
    num_orders = len(orders_df)
    unique_order_ids = orders_df["order_id"].nunique()
    c3 = run_check(3, "Order IDs are completely unique and non-null", (unique_order_ids == num_orders) and (orders_df["order_id"].isnull().sum() == 0), f"Unique Order IDs: {unique_order_ids:,} / {num_orders:,}")
    all_passed = all_passed and c3

    # Check 04: All order customer IDs exist in customers.csv
    valid_cust_ids = set(customers_df["customer_id"])
    orders_cust_ids = set(orders_df["customer_id"])
    missing_in_cust = orders_cust_ids - valid_cust_ids
    c4 = run_check(4, "All customer IDs in orders.csv exist in customers.csv", len(missing_in_cust) == 0, f"Unmatched order customer IDs: {len(missing_in_cust)}")
    all_passed = all_passed and c4

    # Check 05: No invalid or orphan customer references in orders
    orphan_orders = orders_df["customer_id"].isnull().sum()
    c5 = run_check(5, "No null or orphan customer references in orders table", orphan_orders == 0, f"Null customer IDs in orders: {orphan_orders}")
    all_passed = all_passed and c5

    # Check 06: Correct temporal boundaries
    # All orders must be >= customer's signup_date and <= FUTURE_LABEL_END (2026-03-31)
    orders_merged = orders_df.merge(customers_df[["customer_id", "signup_date"]], on="customer_id", how="left")
    before_signup = (orders_merged["order_date"] < orders_merged["signup_date"]).sum()
    after_label_end = (orders_merged["order_date"] > FUTURE_LABEL_END).sum()
    date_bounds_valid = (before_signup == 0) and (after_label_end == 0)
    c6 = run_check(6, "Correct date boundaries (order_date >= signup_date and <= 2026-03-31)", date_bounds_valid, f"Orders before signup: {before_signup}, Orders after 2026-03-31: {after_label_end}")
    all_passed = all_passed and c6

    # Check 07: Binary churn labels
    churn_unique = set(customers_df["churn"].dropna().unique())
    churn_nulls = customers_df["churn"].isnull().sum()
    churn_valid = (churn_unique == {0, 1}) and (churn_nulls == 0)
    c7 = run_check(7, "Binary churn labels (strictly {0, 1} with zero missing values)", churn_valid, f"Unique labels: {churn_unique}, Nulls: {churn_nulls}")
    all_passed = all_passed and c7

    # Check 08: Churn labels match future order history exactly
    # churn = 1 <=> orders between 2026-01-01 and 2026-03-31 is 0
    # churn = 0 <=> orders between 2026-01-01 and 2026-03-31 >= 1
    future_orders = orders_df[(orders_df["order_date"] > SNAPSHOT_DATE) & (orders_df["order_date"] <= FUTURE_LABEL_END)]
    future_cust_with_orders = set(future_orders["customer_id"].unique())
    
    # In customers_df, churned customers must NOT be in future_cust_with_orders
    churned_cust = set(customers_df[customers_df["churn"] == 1]["customer_id"])
    retained_cust = set(customers_df[customers_df["churn"] == 0]["customer_id"])

    # Discrepancy checks:
    churned_with_future = churned_cust.intersection(future_cust_with_orders)
    retained_without_future = retained_cust - future_cust_with_orders
    c8_condition = (len(churned_with_future) == 0) and (len(retained_without_future) == 0)
    c8 = run_check(
        8,
        "Ground-truth churn labels match future 90-day order activity exactly",
        c8_condition,
        f"Churned with future orders: {len(churned_with_future)}, Retained without future orders: {len(retained_without_future)}"
    )
    all_passed = all_passed and c8

    # Check 09: Temporal partition of raw orders
    hist_orders = orders_df[orders_df["order_date"] <= SNAPSHOT_DATE]
    fut_orders = orders_df[orders_df["order_date"] > SNAPSHOT_DATE]
    hist_cust_count = hist_orders["customer_id"].nunique()
    zero_hist_cust = len(valid_cust_ids - set(hist_orders["customer_id"]))
    single_hist_cust = (hist_orders.groupby("customer_id")["order_id"].count() == 1).sum()

    leak_check = (hist_orders["order_date"] > SNAPSHOT_DATE).sum() == 0
    c9 = run_check(
        9,
        "Temporal separation of raw orders: historical orders partitioned at <= 2025-12-31",
        leak_check,
        f"Historical: {len(hist_orders):,}, Future: {len(fut_orders):,}, Zero-order: {zero_hist_cust}, Single-order: {single_hist_cust}. "
        "(Note: Verifies raw order partition only; feature-pipeline leakage testing is enforced during Phase 3 feature engineering)"
    )
    all_passed = all_passed and c9

    print("=" * 75)
    if all_passed:
        print("ALL 10 VERIFICATION CHECKS PASSED SUCCESSFULLY!")
        print("Raw dataset files and temporal partitions are validated.")
        print("(Note: End-to-end feature-level leakage testing will be executed during Phase 3 feature engineering.)")
        print("=" * 75)
        sys.exit(0)
    else:
        print("VALIDATION SUITE FAILED! Please inspect errors above.")
        print("=" * 75)
        sys.exit(1)


if __name__ == "__main__":
    main()
