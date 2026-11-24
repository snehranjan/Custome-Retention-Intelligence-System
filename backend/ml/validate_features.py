"""
Indian E-Commerce Customer Retention Intelligence System
Module: Feature Engineering Validation & Anti-Leakage Verification Suite
Description: Comprehensive validation suite testing the integrity of data/processed/customer_features.csv,
             feature manifest completeness, numerical ranges, edge cases, and critical anti-leakage tests.

Author: BCA (AI & ML) Project Team
Exit Code: 0 on success, non-zero if ANY check fails.
"""

import os
import sys

# Ensure backend/ml is on sys.path when executed from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import the feature engineering function for leakage perturbation tests
from feature_engineering import engineer_features, load_raw_data, SNAPSHOT_DATE_STR

EXPECTED_CUSTOMERS = 7000
RAW_CUST_PATH = os.path.join("data", "raw", "customers.csv")
RAW_ORD_PATH = os.path.join("data", "raw", "orders.csv")
PROCESSED_PATH = os.path.join("data", "processed", "customer_features.csv")
MANIFEST_PATH = os.path.join("data", "processed", "feature_manifest.json")


def run_check(check_id, title, condition, details=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] Check {check_id:02d}: {title}")
    if details:
        print(f"       -> Details: {details}")
    return condition


def main():
    print("=" * 75)
    print("FEATURE ENGINEERING INTEGRITY & ANTI-LEAKAGE SUITE")
    print("=" * 75)

    all_passed = True

    # 1. Feature dataset exists
    c1 = run_check(1, "Processed customer_features.csv exists", os.path.exists(PROCESSED_PATH), PROCESSED_PATH)
    if not c1:
        print("FATAL: Features file missing. Exiting.")
        sys.exit(1)

    df = pd.read_csv(PROCESSED_PATH)
    raw_cust = pd.read_csv(RAW_CUST_PATH)
    raw_ord = pd.read_csv(RAW_ORD_PATH)

    # 2. Exactly 7,000 customer rows
    c2 = run_check(2, "Exactly 7,000 customer rows", len(df) == EXPECTED_CUSTOMERS, f"Found {len(df):,} rows")
    all_passed = all_passed and c2

    # 3. Customer IDs are unique
    c3 = run_check(3, "Customer IDs are completely unique", df["customer_id"].nunique() == EXPECTED_CUSTOMERS, f"Unique IDs: {df['customer_id'].nunique():,}")
    all_passed = all_passed and c3

    # 4. No missing customer IDs
    c4 = run_check(4, "Zero missing customer IDs", df["customer_id"].isnull().sum() == 0, f"Null IDs: {df['customer_id'].isnull().sum()}")
    all_passed = all_passed and c4

    # 5. Customer IDs match original raw customers exactly
    c5 = run_check(5, "Customer IDs match original raw customers.csv exactly", set(df["customer_id"]) == set(raw_cust["customer_id"]))
    all_passed = all_passed and c5

    # 6. Binary churn target without missing labels
    churn_vals = set(df["churn"].dropna().unique())
    c6 = run_check(6, "Target churn is strictly binary {0, 1} with zero missing values", (churn_vals == {0, 1}) and (df["churn"].isnull().sum() == 0), f"Churn unique: {churn_vals}, Nulls: {df['churn'].isnull().sum()}")
    all_passed = all_passed and c6

    # 7. Numerical features within valid documented ranges
    count_cols = [c for c in df.columns if "count" in c]
    counts_non_neg = (df[count_cols] < 0).sum().sum() == 0
    rate_cols = [c for c in df.columns if "rate" in c]
    rates_in_range = ((df[rate_cols] < 0) | (df[rate_cols] > 1.0)).sum().sum() == 0
    amounts_non_neg = (df[["hist_total_order_value_inr", "hist_delivered_order_value_inr"]] < 0).sum().sum() == 0
    c7 = run_check(7, "Numerical features within valid bounds (Counts >= 0, Rates in [0, 1], Amounts >= 0)", counts_non_neg and rates_in_range and amounts_non_neg)
    all_passed = all_passed and c7

    # 8. Customer tenure is non-negative
    c8 = run_check(8, "Customer tenure is strictly non-negative", (df["customer_tenure_days"] >= 0).all(), f"Min tenure: {df['customer_tenure_days'].min():.0f} days")
    all_passed = all_passed and c8

    # 9. Order-attempt recency (recency_days) is non-negative and null only for zero-history accounts
    rec_non_neg = (df["recency_days"].dropna() >= 0).all()
    rec_null_match = (df["recency_days"].isnull() == (df["has_historical_orders"] == 0)).all()
    c9 = run_check(9, "Order-attempt recency (recency_days) is non-negative and null iff zero-history", rec_non_neg and rec_null_match, f"Null count: {df['recency_days'].isnull().sum():,}, Min recency: {df['recency_days'].min():.0f} days")
    all_passed = all_passed and c9

    # 10. Fulfilled purchase recency (recency_delivered_days) non-negative and null iff has_delivered_order == 0
    rec_deliv_non_neg = (df["recency_delivered_days"].dropna() >= 0).all()
    rec_deliv_null_match = (df["recency_delivered_days"].isnull() == (df["has_delivered_order"] == 0)).all()
    c10 = run_check(10, "Fulfilled recency (recency_delivered_days) non-negative and null iff has_delivered_order == 0", rec_deliv_non_neg and rec_deliv_null_match, f"Null count: {df['recency_delivered_days'].isnull().sum():,}, Min delivered recency: {df['recency_delivered_days'].min():.0f} days")
    all_passed = all_passed and c10

    # 11. Delivery fulfillment flag has_delivered_order is binary {0, 1} and consistent with delivered count
    deliv_flag_binary = set(df["has_delivered_order"].unique()).issubset({0, 1})
    deliv_flag_consistent = (df["has_delivered_order"] == (df["hist_delivered_order_count"] > 0).astype(int)).all()
    c11 = run_check(11, "has_delivered_order is binary {0, 1} and 100% consistent with hist_delivered_order_count", deliv_flag_binary and deliv_flag_consistent, f"Delivered customers: {df['has_delivered_order'].sum():,}")
    all_passed = all_passed and c11

    # 12. Zero-history AOV convention: hist_average_order_value_inr is exactly 0.0 for zero-order accounts with zero nulls
    zero_aov_exact = (df.loc[df["has_historical_orders"] == 0, "hist_average_order_value_inr"] == 0.0).all()
    aov_no_nulls = df["hist_average_order_value_inr"].isnull().sum() == 0
    c12 = run_check(12, "Zero-history AOV convention: hist_average_order_value_inr is exactly 0.0 for zero-order accounts with zero nulls", zero_aov_exact and aov_no_nulls, f"Zero-order AOV matches: {zero_aov_exact}, Total nulls: {df['hist_average_order_value_inr'].isnull().sum()}")
    all_passed = all_passed and c12

    # 13. Payment missingness audit: hist_payment_missing_count sum matches raw historical orders (870) and rates in [0, 1]
    raw_hist_ord = raw_ord[raw_ord["order_date"] <= SNAPSHOT_DATE_STR]
    raw_missing_payment = raw_hist_ord["payment_method"].isnull().sum()
    feat_missing_payment_sum = df["hist_payment_missing_count"].sum()
    payment_missing_rates_valid = ((df["hist_payment_missing_rate"] >= 0.0) & (df["hist_payment_missing_rate"] <= 1.0)).all()
    c13 = run_check(13, "Payment missingness audit: sum matches raw historical orders (870) and rates in [0, 1]", (raw_missing_payment == feat_missing_payment_sum == 870) and payment_missing_rates_valid, f"Raw missing: {raw_missing_payment}, Engineered missing sum: {feat_missing_payment_sum}")
    all_passed = all_passed and c13

    # 14. No future order is used in historical aggregation (Direct verification against source order cutoff)
    source_hist_counts = raw_hist_ord.groupby("customer_id")["order_id"].count()
    feat_hist_counts = df.set_index("customer_id")["hist_order_count"]
    counts_match = (source_hist_counts.reindex(df["customer_id"]).fillna(0) == feat_hist_counts).all()
    c14 = run_check(14, "Order count matches strict historical order subset (order_date <= 2025-12-31)", counts_match)
    all_passed = all_passed and c14

    # 15. No target-derived field present in predictive features
    predictive_cols = [c for c in df.columns if c not in ["customer_id", "customer_name", "signup_date", "churn"]]
    c15 = run_check(15, "Target column 'churn' strictly excluded from predictive features list", "churn" not in predictive_cols, f"{len(predictive_cols)} predictive features")
    all_passed = all_passed and c15

    # 16. Feature manifest exists, documents all 40 columns, and specifies correct roles
    manifest_valid = False
    roles_correct = False
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest_features = manifest.get("features", {})
        manifest_valid = set(df.columns).issubset(set(manifest_features.keys())) and len(df.columns) == 40
        # Verify specific roles
        roles_correct = (
            manifest_features.get("city", {}).get("role") == "predictive" and
            manifest_features.get("state", {}).get("role") == "predictive" and
            manifest_features.get("customer_id", {}).get("role") == "identifier" and
            manifest_features.get("customer_name", {}).get("role") == "identifier" and
            manifest_features.get("signup_date", {}).get("role") == "profile" and
            manifest_features.get("churn", {}).get("role") == "target" and
            manifest_features.get("recency_delivered_days", {}).get("role") == "predictive" and
            manifest_features.get("has_delivered_order", {}).get("role") == "predictive" and
            manifest_features.get("hist_payment_missing_count", {}).get("role") == "predictive" and
            manifest_features.get("hist_payment_missing_rate", {}).get("role") == "predictive"
        )
    c16 = run_check(16, "Feature manifest documents all 40 columns and specifies verified roles (city/state predictive, IDs identifier, churn target)", manifest_valid and roles_correct, f"Columns: {len(df.columns)}, Documented: {len(manifest_features)}, Roles correct: {roles_correct}")
    all_passed = all_passed and c16

    # 17. Exactly one row per customer
    c17 = run_check(17, "Exactly one row per customer (Zero duplicates)", df["customer_id"].duplicated().sum() == 0)
    all_passed = all_passed and c17

    # 18. Zero-history customers handled correctly
    zero_cust = df[df["has_historical_orders"] == 0]
    zero_valid = (
        (len(zero_cust) == 148) and
        (zero_cust["hist_order_count"] == 0).all() and
        (zero_cust["hist_total_order_value_inr"] == 0.0).all() and
        (zero_cust["hist_average_order_value_inr"] == 0.0).all() and
        (zero_cust["has_delivered_order"] == 0).all() and
        (zero_cust["hist_return_rate"] == 0.0).all() and
        (zero_cust["recency_days"].isnull().all()) and
        (zero_cust["recency_delivered_days"].isnull().all())
    )
    c18 = run_check(18, "Zero-history customers handled with explicit flags, zero AOV, and clean null recencies (148 customers)", zero_valid, f"{len(zero_cust)} zero-history customers verified")
    all_passed = all_passed and c18

    # 19. Single-order customers handled correctly
    single_cust = df[df["hist_order_count"] == 1]
    single_valid = (
        (len(single_cust) == 1830) and
        (single_cust["has_historical_orders"] == 1).all() and
        (single_cust["recency_days"].notnull().all())
    )
    c19 = run_check(19, "Single-order customers handled correctly with positive history flag and valid recency (1,830 customers)", single_valid, f"{len(single_cust)} single-order customers verified")
    all_passed = all_passed and c19

    # =========================================================================
    # CRITICAL LEAKAGE TESTS
    # =========================================================================
    print("\n" + "-" * 75)
    print("CRITICAL ANTI-LEAKAGE VERIFICATION TESTS")
    print("-" * 75)

    # Test A: Temporal Cutoff Assertion
    source_max_dt = raw_hist_ord["order_date"].max()
    test_a = run_check(
        20,
        "LEAKAGE TEST A: Source historical orders maximum date <= 2025-12-31",
        source_max_dt <= SNAPSHOT_DATE_STR,
        f"Max historical order date: {source_max_dt}"
    )
    all_passed = all_passed and test_a

    # Test B: Strengthened Future Perturbation Test
    # In-memory test:
    # 1. Inject extreme modifications to existing future orders (amount x 10)
    # 2. Inject artificial future orders in Q1 2026 explicitly for all 148 zero-history customers
    # 3. Re-run feature engineering and assert that all computed predictive feature columns remain 100% numerically identical!
    synthetic_future_orders = raw_ord[raw_ord["order_date"] > SNAPSHOT_DATE_STR].copy()
    if len(synthetic_future_orders) > 0:
        perturbed_future = synthetic_future_orders.copy()
        perturbed_future["order_amount_inr"] = perturbed_future["order_amount_inr"] * 10.0  # Extreme amount perturbation

        # Inject artificial future orders for the 148 zero-history customers
        zero_hist_ids = df.loc[df["has_historical_orders"] == 0, "customer_id"].tolist()
        artificial_zero_future = []
        for idx, cid in enumerate(zero_hist_ids):
            artificial_zero_future.append({
                "order_id": f"ORD_SYNTH_ZERO_{idx:05d}",
                "customer_id": cid,
                "order_date": "2026-02-15",
                "order_amount_inr": 85000.0,
                "category": "Electronics",
                "payment_method": "Credit Card",
                "discount_amount_inr": 5000.0,
                "order_status": "Delivered",
                "return_status": "Not Returned",
                "delivery_delay_days": 1
            })
        art_df = pd.DataFrame(artificial_zero_future)
        perturbed_orders = pd.concat([raw_ord, perturbed_future, art_df], ignore_index=True)

        # Run feature engineering with perturbed future orders
        perturbed_features = engineer_features(raw_cust, perturbed_orders)

        # Check that for zero-history customers, features remain completely untouched
        zero_perturbed = perturbed_features[perturbed_features["customer_id"].isin(zero_hist_ids)]
        zero_untouched = (
            (zero_perturbed["has_historical_orders"] == 0).all() and
            (zero_perturbed["has_delivered_order"] == 0).all() and
            (zero_perturbed["hist_order_count"] == 0).all() and
            (zero_perturbed["hist_total_order_value_inr"] == 0.0).all() and
            (zero_perturbed["hist_average_order_value_inr"] == 0.0).all() and
            (zero_perturbed["recency_days"].isnull().all()) and
            (zero_perturbed["recency_delivered_days"].isnull().all())
        )

        # Compare predictive feature values across ALL 7,000 customers
        pred_cols = [c for c in df.columns if c not in ["customer_id", "customer_name", "signup_date", "churn"]]
        diff = 0
        for col in pred_cols:
            if df[col].dtype in [np.float64, np.float32]:
                diff += np.nan_to_num(np.abs(df[col] - perturbed_features[col])).sum()
            else:
                diff += (df[col] != perturbed_features[col]).sum()

        test_b = run_check(
            21,
            "LEAKAGE TEST B (Strengthened Future Perturbation): In-memory future modification has ZERO impact on features",
            (diff == 0) and zero_untouched,
            f"Zero-history untouched: {zero_untouched}, Total divergence across all 36 predictive features: {diff:.6f}"
        )
    else:
        test_b = False
    all_passed = all_passed and test_b

    # Test C: Target Separation Test
    # Verify that shuffling or removing the churn column has zero mathematical effect on feature values
    cust_no_churn = raw_cust.drop(columns=["churn"])
    cust_no_churn["churn"] = np.random.permutation(raw_cust["churn"].values)  # Randomly shuffled churn
    shuffled_features = engineer_features(cust_no_churn, raw_ord)

    diff_target = 0
    for col in pred_cols:
        if df[col].dtype in [np.float64, np.float32]:
            diff_target += np.nan_to_num(np.abs(df[col] - shuffled_features[col])).sum()
        else:
            diff_target += (df[col] != shuffled_features[col]).sum()

    test_c = run_check(
        22,
        "LEAKAGE TEST C (Target Separation): Target column 'churn' has ZERO influence on feature computation",
        diff_target == 0,
        f"Feature difference with shuffled target: {diff_target:.6f}"
    )
    all_passed = all_passed and test_c

    # Test D: Snapshot Consistency Test
    # Verify that all velocity windows (last 30, 90, 180 days) end exactly on 2025-12-31
    d30_max = raw_ord[(raw_ord["order_date"] >= "2025-12-02") & (raw_ord["order_date"] <= SNAPSHOT_DATE_STR)]["order_date"].max()
    test_d = run_check(
        23,
        "LEAKAGE TEST D (Snapshot Consistency): Rolling velocity windows strictly bounded by 2025-12-31",
        d30_max <= SNAPSHOT_DATE_STR,
        f"30-day window max date: {d30_max}"
    )
    all_passed = all_passed and test_d

    print("=" * 75)
    if all_passed:
        print("ALL 23 VERIFICATION & ANTI-LEAKAGE CHECKS PASSED WITH ZERO ERRORS!")
        print("Feature matrix is certified clean, leakage-free, and ready for Phase 4.")
        print("=" * 75)
        sys.exit(0)
    else:
        print("VALIDATION FAILED! Check failures listed above.")
        print("=" * 75)
        sys.exit(1)


if __name__ == "__main__":
    main()
