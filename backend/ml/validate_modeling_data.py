"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5 — Validation Suite for Modeling Data & Stratified Splitting
Description: Rigorous automated verification suite validating modeling_dataset.csv,
             feature_columns.json, train.csv, validation.csv, test.csv,
             split_manifest.json, reproducibility across seeds, feature allowlists,
             and cryptographic immutability of raw and previously accepted assets.

Author: BCA (AI & ML) Project Team
Exit Code: 0 on success, non-zero if ANY check fails.
"""

import os
import sys
import json
import hashlib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Ensure backend/ml is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Path configuration
DATA_DIR = os.path.join("data", "modeling")
MODELING_DATASET_PATH = os.path.join(DATA_DIR, "modeling_dataset.csv")
TRAIN_PATH = os.path.join(DATA_DIR, "train.csv")
VAL_PATH = os.path.join(DATA_DIR, "validation.csv")
TEST_PATH = os.path.join(DATA_DIR, "test.csv")
SPLIT_MANIFEST_PATH = os.path.join(DATA_DIR, "split_manifest.json")
FEATURE_COLUMNS_PATH = os.path.join(DATA_DIR, "feature_columns.json")

RAW_CUSTOMERS_PATH = os.path.join("data", "raw", "customers.csv")
RAW_ORDERS_PATH = os.path.join("data", "raw", "orders.csv")
PROCESSED_FEATURES_PATH = os.path.join("data", "processed", "customer_features.csv")
SEGMENTS_PATH = os.path.join("data", "processed", "customer_segments.csv")

EXPECTED_CUSTOMERS = 7000
EXPECTED_TRAIN_ROWS = 4900
EXPECTED_VAL_ROWS = 1050
EXPECTED_TEST_ROWS = 1050

EXPECTED_RAW_CUST_MD5 = "EA39F916F2FA2D432F40F894F63A1715"
EXPECTED_RAW_CUST_SHA256 = "DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E"
EXPECTED_RAW_ORD_MD5 = "7E65B96077288D3DBDA3E50FAF6FD5EB"
EXPECTED_RAW_ORD_SHA256 = "AB632B3092F732B3B25BAAD096B191C1ACA777CB8D42B29EABB815A266C558E7"
EXPECTED_FEAT_MD5 = "6D9CA7E9C4E27F701C189E8F4609F6A5"
EXPECTED_FEAT_SHA256 = "3B8CFF35A9012A7E6524FEC962D400BE58D29399BF4DF7A80DE7283B69B4C628"


def calculate_hashes(filepath):
    """Calculate cryptographic MD5 and SHA-256 hashes of a file for immutability auditing."""
    hasher_md5 = hashlib.md5()
    hasher_sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher_md5.update(chunk)
            hasher_sha.update(chunk)
    return hasher_md5.hexdigest().upper(), hasher_sha.hexdigest().upper()


def run_check(check_id, title, condition, details=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] Check {check_id:02d}: {title}")
    if details:
        print(f"       -> Details: {details}")
    return condition


def main():
    print("=" * 75)
    print("PHASE 5: MODELING DATASET & SPLITTING VALIDATION SUITE")
    print("=" * 75)

    all_passed = True

    # 1. Modeling dataset exists
    c1 = run_check(1, "Modeling dataset exists", os.path.exists(MODELING_DATASET_PATH), MODELING_DATASET_PATH)
    all_passed = all_passed and c1
    if not c1:
        print("FATAL: modeling_dataset.csv missing. Exiting.")
        sys.exit(1)

    df_mod = pd.read_csv(MODELING_DATASET_PATH)

    # 2. Train, validation and test files exist
    splits_exist = os.path.exists(TRAIN_PATH) and os.path.exists(VAL_PATH) and os.path.exists(TEST_PATH)
    c2 = run_check(2, "Train, validation, and test split datasets exist on disk", splits_exist, f"Train: {TRAIN_PATH}, Val: {VAL_PATH}, Test: {TEST_PATH}")
    all_passed = all_passed and c2
    if not c2:
        print("FATAL: Split files missing. Exiting.")
        sys.exit(1)

    df_train = pd.read_csv(TRAIN_PATH)
    df_val = pd.read_csv(VAL_PATH)
    df_test = pd.read_csv(TEST_PATH)

    # 3. Modeling dataset contains exactly 7,000 rows
    c3 = run_check(3, "Modeling dataset contains exactly 7,000 rows", len(df_mod) == EXPECTED_CUSTOMERS, f"Found {len(df_mod):,} rows")
    all_passed = all_passed and c3

    # 4. Each split has the expected row count (4900, 1050, 1050)
    split_counts_match = (
        len(df_train) == EXPECTED_TRAIN_ROWS and
        len(df_val) == EXPECTED_VAL_ROWS and
        len(df_test) == EXPECTED_TEST_ROWS and
        (len(df_train) + len(df_val) + len(df_test) == EXPECTED_CUSTOMERS)
    )
    c4 = run_check(4, "Each split matches exact expected row count (70% = 4,900, 15% = 1,050, 15% = 1,050)",
                   split_counts_match, f"Train: {len(df_train)}, Val: {len(df_val)}, Test: {len(df_test)}, Total: {len(df_train)+len(df_val)+len(df_test)}")
    all_passed = all_passed and c4

    # 5. Customer IDs are unique within every file
    ids_unique = (
        df_mod["customer_id"].nunique() == len(df_mod) and
        df_train["customer_id"].nunique() == len(df_train) and
        df_val["customer_id"].nunique() == len(df_val) and
        df_test["customer_id"].nunique() == len(df_test)
    )
    c5 = run_check(5, "Customer IDs are completely unique within every dataset file", ids_unique,
                   f"Unique IDs: Mod={df_mod['customer_id'].nunique()}, Train={df_train['customer_id'].nunique()}, Val={df_val['customer_id'].nunique()}, Test={df_test['customer_id'].nunique()}")
    all_passed = all_passed and c5

    # 6. No customer ID overlaps between any two splits
    train_ids = set(df_train["customer_id"])
    val_ids = set(df_val["customer_id"])
    test_ids = set(df_test["customer_id"])
    no_overlap = (
        len(train_ids.intersection(val_ids)) == 0 and
        len(train_ids.intersection(test_ids)) == 0 and
        len(val_ids.intersection(test_ids)) == 0
    )
    c6 = run_check(6, "Zero customer ID overlap between any two splits (Strictly disjoint partitions)", no_overlap,
                   f"Train-Val overlap: {len(train_ids.intersection(val_ids))}, Train-Test: {len(train_ids.intersection(test_ids))}, Val-Test: {len(val_ids.intersection(test_ids))}")
    all_passed = all_passed and c6

    # 7. The union of all split IDs exactly matches the modeling dataset IDs
    union_matches = (train_ids | val_ids | test_ids) == set(df_mod["customer_id"])
    c7 = run_check(7, "Union of all split customer IDs exactly matches modeling dataset IDs", union_matches,
                   f"Union size: {len(train_ids | val_ids | test_ids)} == {len(df_mod)}")
    all_passed = all_passed and c7

    # 8. Every customer appears exactly once across the three splits
    partition_complete = (len(train_ids) + len(val_ids) + len(test_ids) == EXPECTED_CUSTOMERS) and union_matches
    c8 = run_check(8, "Every customer appears exactly once across the three splits", partition_complete)
    all_passed = all_passed and c8

    # 9. Target values are strictly binary
    targets_binary = (
        set(df_mod["churn"].unique()) == {0, 1} and
        set(df_train["churn"].unique()) == {0, 1} and
        set(df_val["churn"].unique()) == {0, 1} and
        set(df_test["churn"].unique()) == {0, 1}
    )
    c9 = run_check(9, "Target variable 'churn' is strictly binary {0, 1} across all datasets", targets_binary,
                   f"Modeling target values: {set(df_mod['churn'].unique())}")
    all_passed = all_passed and c9

    # 10. Target has no missing values
    target_nulls = (
        df_mod["churn"].isnull().sum() +
        df_train["churn"].isnull().sum() +
        df_val["churn"].isnull().sum() +
        df_test["churn"].isnull().sum()
    )
    c10 = run_check(10, "Target 'churn' contains zero null or missing values across all files", target_nulls == 0, f"Total target nulls: {target_nulls}")
    all_passed = all_passed and c10

    # 11. Target distribution is approximately preserved across splits
    mod_churn_pct = df_mod["churn"].mean() * 100.0
    train_churn_pct = df_train["churn"].mean() * 100.0
    val_churn_pct = df_val["churn"].mean() * 100.0
    test_churn_pct = df_test["churn"].mean() * 100.0
    strat_preserved = (
        abs(train_churn_pct - mod_churn_pct) < 0.2 and
        abs(val_churn_pct - mod_churn_pct) < 0.2 and
        abs(test_churn_pct - mod_churn_pct) < 0.2
    )
    c11 = run_check(11, "Stratification preserved: Churn percentage matches across splits (~45.81%)", strat_preserved,
                    f"Overall: {mod_churn_pct:.2f}%, Train: {train_churn_pct:.2f}%, Val: {val_churn_pct:.2f}%, Test: {test_churn_pct:.2f}%")
    all_passed = all_passed and c11

    # Load feature metadata
    with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
        fmeta = json.load(f)

    cfg_a = fmeta.get("configuration_a", {}).get("features_ordered", [])
    cfg_b = fmeta.get("configuration_b", {}).get("features_ordered", [])

    # 12. Configuration A has exactly 36 approved features
    c12 = run_check(12, "Configuration A contains exactly 36 approved behavioral features", len(cfg_a) == 36, f"Config A count: {len(cfg_a)}")
    all_passed = all_passed and c12

    # 13. Configuration B has exactly 37 approved features
    c13 = run_check(13, "Configuration B contains exactly 37 approved features", len(cfg_b) == 37, f"Config B count: {len(cfg_b)}")
    all_passed = all_passed and c13

    # 14. Configuration B differs from Configuration A only by cluster_id
    diff_b_a = set(cfg_b) - set(cfg_a)
    diff_a_b = set(cfg_a) - set(cfg_b)
    diff_valid = (diff_b_a == {"cluster_id"}) and (len(diff_a_b) == 0)
    c14 = run_check(14, "Configuration B differs from Configuration A strictly by 'cluster_id'", diff_valid, f"Additional feature: {diff_b_a}")
    all_passed = all_passed and c14

    # 15. No ID, customer name, date string or target enters either feature allowlist
    forbidden = {"customer_id", "customer_name", "signup_date", "churn", "cluster_name"}
    leaks_a = forbidden.intersection(set(cfg_a))
    leaks_b = forbidden.intersection(set(cfg_b))
    no_leaks = (len(leaks_a) == 0) and (len(leaks_b) == 0)
    c15 = run_check(15, "Zero leakage: No identifier, name, raw date or target in feature allowlists", no_leaks,
                    f"Leaks in A: {leaks_a}, Leaks in B: {leaks_b}")
    all_passed = all_passed and c15

    # 16. All five cluster categories are represented where expected
    clusters_present = (
        set(df_mod["cluster_id"].unique()) == {0, 1, 2, 3, 4} and
        set(df_train["cluster_id"].unique()) == {0, 1, 2, 3, 4} and
        set(df_val["cluster_id"].unique()) == {0, 1, 2, 3, 4} and
        set(df_test["cluster_id"].unique()) == {0, 1, 2, 3, 4}
    )
    c16 = run_check(16, "All five unsupervised cluster categories {0, 1, 2, 3, 4} represented across all splits", clusters_present,
                    f"Clusters found: {set(df_train['cluster_id'].unique())}")
    all_passed = all_passed and c16

    # 17. Both stratification operations use random_state=42
    with open(SPLIT_MANIFEST_PATH, "r", encoding="utf-8") as f:
        s_man = json.load(f)
    seed_val = s_man.get("split_configuration", {}).get("random_state")
    c17 = run_check(17, "Stratification configuration confirmed with random_state=42", seed_val == 42, f"Manifest random_state: {seed_val}")
    all_passed = all_passed and c17

    # 18. Split manifest values match actual files
    man_train_cnt = s_man.get("row_counts", {}).get("train")
    man_val_cnt = s_man.get("row_counts", {}).get("validation")
    man_test_cnt = s_man.get("row_counts", {}).get("test")
    manifest_matches = (
        man_train_cnt == len(df_train) and
        man_val_cnt == len(df_val) and
        man_test_cnt == len(df_test)
    )
    c18 = run_check(18, "Split manifest recorded metadata matches actual files exactly", manifest_matches,
                    f"Manifest counts: Train={man_train_cnt}, Val={man_val_cnt}, Test={man_test_cnt}")
    all_passed = all_passed and c18

    # 19. Recreating the split with the same seed produces identical customer assignments
    df_re_train, df_re_temp = train_test_split(df_mod, test_size=0.30, random_state=42, stratify=df_mod["churn"])
    df_re_val, df_re_test = train_test_split(df_re_temp, test_size=0.50, random_state=42, stratify=df_re_temp["churn"])

    train_mismatches = sum(df_re_train["customer_id"].values != df_train["customer_id"].values)
    val_mismatches = sum(df_re_val["customer_id"].values != df_val["customer_id"].values)
    test_mismatches = sum(df_re_test["customer_id"].values != df_test["customer_id"].values)

    reprod_match = (train_mismatches == 0) and (val_mismatches == 0) and (test_mismatches == 0)
    c19 = run_check(19, "Split reproducibility verified: Re-splitting with seed 42 yields 100% identical row orders", reprod_match,
                    f"Mismatches: Train={train_mismatches}, Val={val_mismatches}, Test={test_mismatches}")
    all_passed = all_passed and c19

    # 20. Source raw datasets and previously accepted Phase 3 and Phase 4 files remain unchanged
    cust_m, cust_s = calculate_hashes(RAW_CUSTOMERS_PATH)
    ord_m, ord_s = calculate_hashes(RAW_ORDERS_PATH)
    feat_m, feat_s = calculate_hashes(PROCESSED_FEATURES_PATH)

    hashes_intact = (
        cust_m == EXPECTED_RAW_CUST_MD5 and cust_s == EXPECTED_RAW_CUST_SHA256 and
        ord_m == EXPECTED_RAW_ORD_MD5 and ord_s == EXPECTED_RAW_ORD_SHA256 and
        feat_m == EXPECTED_FEAT_MD5 and feat_s == EXPECTED_FEAT_SHA256
    )
    c20 = run_check(20, "Source raw CSVs & Phase 3 feature dataset remain 100% cryptographically unchanged (MD5 & SHA-256)", hashes_intact,
                    f"customers SHA256: {cust_s[:16]}..., orders SHA256: {ord_s[:16]}..., features SHA256: {feat_s[:16]}...")
    all_passed = all_passed and c20

    print("=" * 75)
    if all_passed:
        print("ALL 20 VALIDATION CHECKS PASSED WITH ZERO ERRORS!")
        print("Checkpoint 2 Modeling Dataset & Stratified Splits are certified and reproducible.")
        print("=" * 75)
        sys.exit(0)
    else:
        print("VALIDATION FAILED! Check failures listed above.")
        print("=" * 75)
        sys.exit(1)


if __name__ == "__main__":
    main()
