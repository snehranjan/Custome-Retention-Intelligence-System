"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5 — Leakage-Free Stratified Train/Validation/Test Dataset Splitting
Description: Performs a two-stage stratified split of modeling_dataset.csv into
             disjoint Training (70%), Validation (15%), and Test (15%) subsets.
             Preserves natural class distribution (random_state=42).
             Generates train.csv, validation.csv, test.csv, and split_manifest.json.

Author: BCA (AI & ML) Project Team
"""

import os
import sys
import json
import datetime
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

RANDOM_STATE = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15


def split_modeling_dataset():
    print("=" * 75)
    print("PHASE 5: TWO-STAGE STRATIFIED TRAIN / VALIDATION / TEST SPLITTING")
    print("=" * 75)

    if not os.path.exists(MODELING_DATASET_PATH):
        raise FileNotFoundError(f"Modeling dataset not found at {MODELING_DATASET_PATH}. Run prepare_modeling_data.py first.")

    df = pd.read_csv(MODELING_DATASET_PATH)
    n_total = len(df)
    print(f"Loaded modeling dataset: {n_total:,} rows, {len(df.columns)} columns")
    assert n_total == 7000, f"Expected 7,000 customers, found {n_total}"

    # Verify target distribution in full dataset
    target_counts = df["churn"].value_counts().to_dict()
    target_pcts = (df["churn"].value_counts(normalize=True) * 100).to_dict()
    print(f"Overall Class Distribution:")
    print(f"  - Retained (0): {target_counts[0]:,} ({target_pcts[0]:.2f}%)")
    print(f"  - Churned  (1): {target_counts[1]:,} ({target_pcts[1]:.2f}%)")

    # STAGE 1: Split into Train (70%) and Temporary (30%)
    print(f"\nStage 1: Stratified split into Train (70%) and Temp (30%)...")
    df_train, df_temp = train_test_split(
        df,
        test_size=0.30,
        random_state=RANDOM_STATE,
        stratify=df["churn"]
    )
    print(f"  -> Train count: {len(df_train):,} ({len(df_train)/n_total*100:.1f}%)")
    print(f"  -> Temp count:  {len(df_temp):,} ({len(df_temp)/n_total*100:.1f}%)")

    # STAGE 2: Split Temporary equally into Validation (15%) and Test (15%)
    print(f"\nStage 2: Stratified split of Temp into Validation (50% of temp = 15%) and Test (50% of temp = 15%)...")
    df_val, df_test = train_test_split(
        df_temp,
        test_size=0.50,
        random_state=RANDOM_STATE,
        stratify=df_temp["churn"]
    )
    print(f"  -> Validation count: {len(df_val):,} ({len(df_val)/n_total*100:.1f}%)")
    print(f"  -> Test count:       {len(df_test):,} ({len(df_test)/n_total*100:.1f}%)")

    # Validation of disjoint partition
    train_ids = set(df_train["customer_id"])
    val_ids = set(df_val["customer_id"])
    test_ids = set(df_test["customer_id"])

    assert len(train_ids) == 4900, f"Expected 4,900 train customers, got {len(train_ids)}"
    assert len(val_ids) == 1050, f"Expected 1,050 validation customers, got {len(val_ids)}"
    assert len(test_ids) == 1050, f"Expected 1,050 test customers, got {len(test_ids)}"

    assert len(train_ids.intersection(val_ids)) == 0, "Overlap detected between Train and Validation!"
    assert len(train_ids.intersection(test_ids)) == 0, "Overlap detected between Train and Test!"
    assert len(val_ids.intersection(test_ids)) == 0, "Overlap detected between Validation and Test!"
    assert (train_ids | val_ids | test_ids) == set(df["customer_id"]), "Partition union does not match original customers!"
    print("\nVerified partition disjointness: Exactly 0 overlapping customers across splits.")

    # Save splits
    df_train.to_csv(TRAIN_PATH, index=False)
    df_val.to_csv(VAL_PATH, index=False)
    df_test.to_csv(TEST_PATH, index=False)

    print(f"\nSaved split datasets:")
    print(f"  - Train:      {TRAIN_PATH} ({len(df_train):,} rows, {len(df_train.columns)} cols)")
    print(f"  - Validation: {VAL_PATH} ({len(df_val):,} rows, {len(df_val.columns)} cols)")
    print(f"  - Test:       {TEST_PATH} ({len(df_test):,} rows, {len(df_test.columns)} cols)")

    # Compute actual class metrics across splits
    def get_class_info(split_df):
        counts = split_df["churn"].value_counts().to_dict()
        pcts = (split_df["churn"].value_counts(normalize=True) * 100).to_dict()
        return {
            "0_retained_count": int(counts.get(0, 0)),
            "1_churned_count": int(counts.get(1, 0)),
            "0_retained_pct": round(pcts.get(0, 0.0), 2),
            "1_churned_pct": round(pcts.get(1, 0.0), 2)
        }

    train_class_info = get_class_info(df_train)
    val_class_info = get_class_info(df_val)
    test_class_info = get_class_info(df_test)

    print(f"\nActual Class Distributions across Splits:")
    print(f"  - Train:      0={train_class_info['0_retained_count']:,} ({train_class_info['0_retained_pct']}%), 1={train_class_info['1_churned_count']:,} ({train_class_info['1_churned_pct']}%)")
    print(f"  - Validation: 0={val_class_info['0_retained_count']:,} ({val_class_info['0_retained_pct']}%), 1={val_class_info['1_churned_count']:,} ({val_class_info['1_churned_pct']}%)")
    print(f"  - Test:       0={test_class_info['0_retained_count']:,} ({test_class_info['0_retained_pct']}%), 1={test_class_info['1_churned_count']:,} ({test_class_info['1_churned_pct']}%)")

    # Load feature metadata if available
    cfg_a_count = 36
    cfg_b_count = 37
    if os.path.exists(FEATURE_COLUMNS_PATH):
        with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
            fmeta = json.load(f)
            cfg_a_count = fmeta.get("configuration_a", {}).get("feature_count", 36)
            cfg_b_count = fmeta.get("configuration_b", {}).get("feature_count", 37)

    # Generate split manifest
    manifest_data = {
        "metadata": {
            "title": "Phase 5 Dataset Splitting Manifest",
            "generation_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_dataset_path": MODELING_DATASET_PATH,
            "target_name": "churn",
            "identifier_name": "customer_id",
            "snapshot_date": "2025-12-31",
            "label_window": "2026-01-01 through 2026-03-31, inclusive"
        },
        "split_configuration": {
            "random_state": RANDOM_STATE,
            "split_method": "Two-stage stratified splitting using sklearn.model_selection.train_test_split",
            "requested_split_proportions": {
                "train": TRAIN_RATIO,
                "validation": VAL_RATIO,
                "test": TEST_RATIO
            },
            "actual_split_proportions": {
                "train": round(len(df_train) / n_total, 4),
                "validation": round(len(df_val) / n_total, 4),
                "test": round(len(df_test) / n_total, 4)
            },
            "total_customer_count": n_total
        },
        "row_counts": {
            "train": len(df_train),
            "validation": len(df_val),
            "test": len(df_test)
        },
        "class_distributions": {
            "train": train_class_info,
            "validation": val_class_info,
            "test": test_class_info
        },
        "feature_counts": {
            "configuration_a_feature_count": cfg_a_count,
            "configuration_b_feature_count": cfg_b_count,
            "total_columns_per_split_file": len(df_train.columns)
        },
        "disjointness_verification": {
            "train_val_overlap": len(train_ids.intersection(val_ids)),
            "train_test_overlap": len(train_ids.intersection(test_ids)),
            "val_test_overlap": len(val_ids.intersection(test_ids)),
            "union_matches_total": (train_ids | val_ids | test_ids) == set(df["customer_id"])
        }
    }

    with open(SPLIT_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"\nSaved split manifest to: {SPLIT_MANIFEST_PATH}")
    print("=" * 75)
    print("STRATIFIED DATASET SPLITTING COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    split_modeling_dataset()
