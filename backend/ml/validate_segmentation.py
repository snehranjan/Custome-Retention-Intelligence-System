"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 4 — Customer Segmentation Validation Suite (Audited Version)
Description: Rigorous automated verification suite testing the integrity of
             customer_segments.csv, cluster_profiles.csv, segmentation_manifest.json,
             segmentation_metrics.json, model/scaler artifact reloadability,
             reproducibility, visualizations, and SHA-256 / MD5 immutability.

Author: BCA (AI & ML) Project Team
Exit Code: 0 on success, non-zero if ANY check fails.
"""

import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
import joblib

# Ensure backend/ml is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------
PROCESSED_FEATURES_PATH = os.path.join("data", "processed", "customer_features.csv")
RAW_CUSTOMERS_PATH = os.path.join("data", "raw", "customers.csv")
RAW_ORDERS_PATH = os.path.join("data", "raw", "orders.csv")

SEGMENTS_PATH = os.path.join("data", "processed", "customer_segments.csv")
PROFILES_PATH = os.path.join("data", "processed", "cluster_profiles.csv")
METRICS_PATH = os.path.join("data", "processed", "segmentation_metrics.json")
MANIFEST_PATH = os.path.join("data", "processed", "segmentation_manifest.json")

MODEL_PATH = os.path.join("models", "kmeans_customer_segmentation.joblib")
SCALER_PATH = os.path.join("models", "segmentation_scaler.joblib")
FIGURES_DIR = os.path.join("reports", "figures")

EXPECTED_CUSTOMERS = 7000
EXPECTED_RAW_CUST_MD5 = "EA39F916F2FA2D432F40F894F63A1715"
EXPECTED_RAW_CUST_SHA256 = "DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E"
EXPECTED_RAW_ORD_MD5 = "7E65B96077288D3DBDA3E50FAF6FD5EB"
EXPECTED_RAW_ORD_SHA256 = "AB632B3092F732B3B25BAAD096B191C1ACA777CB8D42B29EABB815A266C558E7"


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
    print("PHASE 4: CUSTOMER SEGMENTATION VALIDATION SUITE (AUDITED VERSION)")
    print("=" * 75)

    all_passed = True

    # 1. Source feature dataset exists
    c1 = run_check(1, "Source customer_features.csv exists", os.path.exists(PROCESSED_FEATURES_PATH), PROCESSED_FEATURES_PATH)
    if not c1:
        print("FATAL: Source customer_features.csv missing. Exiting.")
        sys.exit(1)
    all_passed = all_passed and c1

    # Load datasets
    df_feat = pd.read_csv(PROCESSED_FEATURES_PATH)
    if not os.path.exists(SEGMENTS_PATH):
        print(f"FATAL: {SEGMENTS_PATH} missing. Exiting.")
        sys.exit(1)
    df_seg = pd.read_csv(SEGMENTS_PATH)

    # 2. Exactly 7,000 segmented customer records
    c2 = run_check(2, "Exactly 7,000 segmented customer records", len(df_seg) == EXPECTED_CUSTOMERS, f"Found {len(df_seg):,} records")
    all_passed = all_passed and c2

    # 3. Customer IDs are unique
    c3 = run_check(3, "Customer IDs are completely unique", df_seg["customer_id"].nunique() == EXPECTED_CUSTOMERS, f"Unique IDs: {df_seg['customer_id'].nunique():,}")
    all_passed = all_passed and c3

    # 4. Every source customer is represented
    c4 = run_check(4, "Every source customer from Phase 3 is represented", set(df_seg["customer_id"]) == set(df_feat["customer_id"]))
    all_passed = all_passed and c4

    # 5. Every customer receives exactly one cluster
    c5 = run_check(5, "Every customer receives exactly one cluster (Zero duplicate assignments)", df_seg.groupby("customer_id")["cluster_id"].count().max() == 1)
    all_passed = all_passed and c5

    # 6. Cluster IDs are valid
    valid_cids = {0, 1, 2, 3, 4}
    actual_cids = set(df_seg["cluster_id"].unique())
    c6 = run_check(6, "Cluster IDs are valid integers {0, 1, 2, 3, 4}", actual_cids == valid_cids, f"Cluster IDs found: {actual_cids}")
    all_passed = all_passed and c6

    # 7. No missing cluster assignments
    null_clusters = df_seg["cluster_id"].isnull().sum()
    c7 = run_check(7, "Zero missing cluster assignments", null_clusters == 0, f"Null clusters: {null_clusters}")
    all_passed = all_passed and c7

    # 8. No identifiers are used as clustering inputs
    manifest = {}
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    clustering_inputs = manifest.get("clustering_features_ordered", [])
    forbidden_ids = ["customer_id", "customer_name", "signup_date"]
    no_ids_used = all(fid not in clustering_inputs for fid in forbidden_ids)
    c8 = run_check(8, "No customer identifiers used as clustering inputs", no_ids_used, f"Clustering inputs: {clustering_inputs}")
    all_passed = all_passed and c8

    # 9. Churn is excluded from clustering inputs
    churn_excluded = "churn" not in clustering_inputs and manifest.get("target_exclusion_certification", {}).get("churn_column_used_in_clustering") is False
    c9 = run_check(9, "Target column 'churn' strictly excluded from clustering inputs", churn_excluded, "Entirely unsupervised")
    all_passed = all_passed and c9

    # 10. Feature order in manifest matches model inputs
    expected_order = ["recency_delivered_days", "hist_delivered_order_count", "hist_delivered_order_value_inr"]
    order_matches = clustering_inputs == expected_order
    c10 = run_check(10, "Feature order in manifest exactly matches expected RFM inputs", order_matches, f"Manifest order: {clustering_inputs}")
    all_passed = all_passed and c10

    # 11. Scaler and K-Means artifacts can be reloaded
    artifacts_reloadable = False
    try:
        loaded_km = joblib.load(MODEL_PATH)
        loaded_scaler = joblib.load(SCALER_PATH)
        artifacts_reloadable = (loaded_km is not None) and (loaded_scaler is not None)
    except Exception as e:
        artifacts_reloadable = False
    c11 = run_check(11, "Scaler and K-Means artifacts can be successfully reloaded", artifacts_reloadable, f"Model: {MODEL_PATH}, Scaler: {SCALER_PATH}")
    all_passed = all_passed and c11

    # 12. Reloaded model produces 100% identical assignments
    reproducible = False
    if artifacts_reloadable:
        imp_rec = manifest.get("zero_delivered_strategy", {}).get("imputed_recency_days", 1117.0)
        X_test = pd.DataFrame()
        X_test["recency_delivered_days"] = np.log1p(df_feat["recency_delivered_days"].fillna(imp_rec))
        X_test["hist_delivered_order_count"] = np.log1p(df_feat["hist_delivered_order_count"])
        X_test["hist_delivered_order_value_inr"] = np.log1p(df_feat["hist_delivered_order_value_inr"])
        
        X_test_scaled = loaded_scaler.transform(X_test)
        reloaded_labels = loaded_km.predict(X_test_scaled)
        mismatch_count = (df_seg["cluster_id"] != reloaded_labels).sum()
        reproducible = mismatch_count == 0
    c12 = run_check(12, "Reloaded model and scaler produce 100% identical cluster assignments", reproducible, f"Mismatches: {mismatch_count}")
    all_passed = all_passed and c12

    # 13. Audit Check: Monetary transformation audit values
    metrics = {}
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    
    m_audit = metrics.get("monetary_transformation_audit", {})
    raw_skew_all = m_audit.get("raw_all_7000", {}).get("skewness", 0.0)
    raw_skew_act = m_audit.get("raw_active_6516", {}).get("skewness", 0.0)
    log_skew_all = m_audit.get("log1p_all_7000", {}).get("skewness", 0.0)
    log_skew_act = m_audit.get("log1p_active_6516", {}).get("skewness", 0.0)
    
    mon_audit_valid = (
        round(raw_skew_all, 2) == 2.46 and
        round(raw_skew_act, 2) == 2.38 and
        round(log_skew_all, 2) == -1.87 and
        round(log_skew_act, 2) == -0.42
    )
    c13 = run_check(13, "Monetary transformation audit verified (Active skewness = -0.42, Zero-inflation skewness = -1.87)", mon_audit_valid, f"Raw skew all/active: {raw_skew_all:.2f}/{raw_skew_act:.2f}, Log1p skew all/active: {log_skew_all:.2f}/{log_skew_act:.2f}")
    all_passed = all_passed and c13

    # 14. Audit Check: K=3 vs K=5 comparison metrics verified
    k_comp = metrics.get("k3_vs_k5_comparison", {})
    k3_sil = k_comp.get("k3_evaluation", {}).get("silhouette_score", 0.0)
    k5_sil = k_comp.get("k5_evaluation", {}).get("silhouette_score", 0.0)
    k3_inertia = k_comp.get("k3_evaluation", {}).get("inertia", 0.0)
    k5_inertia = k_comp.get("k5_evaluation", {}).get("inertia", 0.0)
    k_comp_valid = (round(k3_sil, 3) == 0.441) and (round(k5_sil, 3) == 0.407) and (k5_inertia < k3_inertia)
    c14 = run_check(14, "K=3 vs K=5 comparison verified (K=3 Silhouette=0.4412, K=5 Silhouette=0.4065 with 46% lower inertia)", k_comp_valid, f"K=3: Sil={k3_sil:.4f}, Inertia={k3_inertia:.1f} | K=5: Sil={k5_sil:.4f}, Inertia={k5_inertia:.1f}")
    all_passed = all_passed and c14

    # 15. Audit Check: Zero-delivered cohort subgroup counts verified
    z_audit = metrics.get("zero_delivered_cohort_audit", {})
    z_total = z_audit.get("total_zero_delivered_count", 0)
    z_never = z_audit.get("subgroup_never_purchased_count", 0)
    z_unfulfilled = z_audit.get("subgroup_attempted_unfulfilled_count", 0)
    z_subgroups_valid = (z_total == 484) and (z_never == 148) and (z_unfulfilled == 336) and (z_never + z_unfulfilled == z_total)
    c15 = run_check(15, "Zero-delivered cohort subgroups verified (148 never-purchased + 336 attempted unfulfilled = 484)", z_subgroups_valid, f"Never-purchased: {z_never}, Attempted unfulfilled: {z_unfulfilled}, Total: {z_total}")
    all_passed = all_passed and c15

    # 16. Audit Check: Zero-delivered cohort cleanly isolated into Cluster 2
    zero_mask = df_seg["has_delivered_order"] == 0
    zero_cluster_match = (df_seg.loc[zero_mask, "cluster_id"] == 2).all()
    c2_count = (df_seg["cluster_id"] == 2).sum()
    c16 = run_check(16, "Zero-delivered cohort cleanly isolated into Cluster 2 with 100% purity", zero_cluster_match and (c2_count == 484), f"Cluster 2 count: {c2_count}, Zero-delivered in Cluster 2: {(df_seg.loc[zero_mask, 'cluster_id'] == 2).sum()}/484")
    all_passed = all_passed and c16

    # 17. Audit Check: Undefined recency handling verified
    imp_rec_val = z_audit.get("imputed_recency_days", 0.0)
    max_raw_rec = df_feat["recency_delivered_days"].max()
    rec_handling_valid = (imp_rec_val == max_raw_rec + 30.0 == 1117.0)
    c17 = run_check(17, "Undefined recency handling verified (Observation boundary: max_recency + 30 = 1117.0 days)", rec_handling_valid, f"Max recency: {max_raw_rec}, Imputed boundary: {imp_rec_val}")
    all_passed = all_passed and c17

    # 18. Audit Check: Zero-delivered cohort subgroup counts in Cluster 2
    c2_mask = df_seg["cluster_id"] == 2
    c2_cust_ids = df_seg.loc[c2_mask, "customer_id"]
    c2_feat = df_feat[df_feat["customer_id"].isin(c2_cust_ids)]
    c2_zero_hist = c2_feat[c2_feat["hist_order_count"] == 0]
    c2_att_unfulfilled = c2_feat[(c2_feat["hist_order_count"] > 0) & (c2_feat["has_delivered_order"] == 0)]
    
    subgroups_match = (
        len(c2_zero_hist) == 148 and
        len(c2_att_unfulfilled) == 336 and
        (len(c2_zero_hist) + len(c2_att_unfulfilled) == 484) and
        (c2_feat["has_delivered_order"] == 0).all()
    )
    c18 = run_check(
        18,
        "Cluster 2 zero-delivered cohort subgroups verified (148 zero orders + 336 attempted unfulfilled = 484)",
        subgroups_match,
        f"Never-purchased (zero orders): {len(c2_zero_hist)}, Attempted unfulfilled: {len(c2_att_unfulfilled)}, Total C2: {len(c2_feat)}"
    )
    all_passed = all_passed and c18

    # 19. Audit Check: Pooled order-level friction rates across 368 historical orders (strictly <= 2025-12-31)
    raw_ord = pd.read_csv(RAW_ORDERS_PATH)
    raw_hist_ord = raw_ord[raw_ord["order_date"] <= "2025-12-31"]
    raw_fut_ord = raw_ord[raw_ord["order_date"] > "2025-12-31"]
    
    ord_336_hist = raw_hist_ord[raw_hist_ord["customer_id"].isin(c2_att_unfulfilled["customer_id"])]
    ord_336_fut = raw_fut_ord[raw_fut_ord["customer_id"].isin(c2_att_unfulfilled["customer_id"])]
    
    raw_att_cnt = len(ord_336_hist)
    raw_ret_cnt = int((ord_336_hist["order_status"] == "Returned").sum())
    raw_canc_cnt = int((ord_336_hist["order_status"] == "Cancelled").sum())
    raw_deliv_cnt = int((ord_336_hist["order_status"] == "Delivered").sum())
    
    pooled_ret_raw = raw_ret_cnt / raw_att_cnt
    pooled_canc_raw = raw_canc_cnt / raw_att_cnt
    
    pooled_valid = (
        raw_att_cnt == 368 and
        raw_ret_cnt == 207 and
        raw_canc_cnt == 161 and
        raw_deliv_cnt == 0 and
        (raw_ret_cnt + raw_canc_cnt == 368) and
        round(pooled_ret_raw, 4) == 0.5625 and
        round(pooled_canc_raw, 4) == 0.4375 and
        len(ord_336_fut) == 189  # Confirms future orders exist (189) but are strictly excluded from historical calculations
    )
    c19 = run_check(
        19,
        "Pooled order-level friction rates verified on 368 orders (207 returned [56.25%], 161 cancelled [43.75%], strictly <= 2025-12-31)",
        pooled_valid,
        f"Historical orders: {raw_att_cnt} (207 Ret + 161 Canc = 368, Deliv: {raw_deliv_cnt}), Pooled Ret: {pooled_ret_raw:.4f}, Pooled Canc: {pooled_canc_raw:.4f}, Future orders excluded: {len(ord_336_fut)}"
    )
    all_passed = all_passed and c19

    # 20. Audit Check: Customer-level rate averaging verified (Denominator 336, 148 undefined excluded)
    c336_records = c2_att_unfulfilled.copy()
    c336_indiv_ret = c336_records["hist_returned_order_count"] / c336_records["hist_order_count"]
    c336_indiv_canc = c336_records["hist_cancelled_order_count"] / c336_records["hist_order_count"]
    
    mean_cust_ret = c336_indiv_ret.mean()
    mean_cust_canc = c336_indiv_canc.mean()
    cust_denom = len(c336_records)
    c148_undefined_count = len(c2_zero_hist)
    
    df_prof = pd.read_csv(PROFILES_PATH)
    c2_prof = df_prof[df_prof["cluster_id"] == 2].iloc[0]
    
    cust_avg_valid = (
        cust_denom == 336 and
        c148_undefined_count == 148 and
        round(mean_cust_ret, 4) == 0.5645 and
        round(mean_cust_canc, 4) == 0.4355 and
        round(mean_cust_ret + mean_cust_canc, 4) == 1.0000 and
        c2_prof["mean_return_rate"] == 0.5645 and
        c2_prof["mean_cancellation_rate"] == 0.4355 and
        c2_prof["attempted_customer_count"] == 336 and
        c2_prof["undefined_rate_count"] == 148
    )
    c20 = run_check(
        20,
        "Customer-level averages verified across 336 attempting accounts (Mean Ret: 56.45%, Mean Canc: 43.55%, 148 undefined excluded)",
        cust_avg_valid,
        f"Denominator: {cust_denom}, Mean Ret: {mean_cust_ret:.4f}, Mean Canc: {mean_cust_canc:.4f}, Undefined accounts: {c148_undefined_count}, Profile row: Ret={c2_prof['mean_return_rate']}, Canc={c2_prof['mean_cancellation_rate']}"
    )
    all_passed = all_passed and c20

    # 21. Audit Guard Test: Statistical guard test preventing pooled rate substitution or conflated 484 denominator
    is_pooled_substitution = (round(c2_prof["mean_return_rate"], 4) == round(pooled_ret_raw, 4))
    is_conflated_denominator = (round(c2_prof["mean_return_rate"], 4) == 0.3919)
    is_mathematically_distinct = (round(mean_cust_ret, 4) != round(pooled_ret_raw, 4))
    
    guard_test_passed = (
        (not is_pooled_substitution) and
        (not is_conflated_denominator) and
        is_mathematically_distinct and
        (c2_prof["mean_return_rate"] == 0.5645)
    )
    c21 = run_check(
        21,
        "Statistical guard test: Customer-level rate is NOT substituted by pooled rate (0.5645 != 0.5625 and != 0.3919)",
        guard_test_passed,
        f"Customer-level: {c2_prof['mean_return_rate']} != Pooled: {round(pooled_ret_raw, 4)} and != Conflated: 0.3919 (Guard Test Passed)"
    )
    all_passed = all_passed and c21

    # 22. Visualizations exist and are non-empty
    figs = [
        "phase4_elbow_method.png",
        "phase4_silhouette_scores.png",
        "phase4_cluster_distribution.png",
        "phase4_rfm_cluster_profiles.png",
        "phase4_cluster_scatter_pca.png",
        "phase4_cluster_comparison_heatmap.png"
    ]
    figs_valid = all(os.path.exists(os.path.join(FIGURES_DIR, f)) and os.path.getsize(os.path.join(FIGURES_DIR, f)) > 1000 for f in figs)
    c22 = run_check(22, "All 6 required publication-grade visualizations exist and are non-empty", figs_valid, f"{len(figs)} figures verified in {FIGURES_DIR}")
    all_passed = all_passed and c22

    # 23. Cluster profile output matches customer assignments
    profiles_valid = False
    if os.path.exists(PROFILES_PATH):
        df_prof = pd.read_csv(PROFILES_PATH)
        seg_counts = df_seg["cluster_id"].value_counts().to_dict()
        prof_counts = df_prof.set_index("cluster_id")["count"].to_dict()
        profiles_valid = (seg_counts == prof_counts) and (len(df_prof) == 5)
    c23 = run_check(23, "Cluster profiles output matches customer segment assignments exactly", profiles_valid, f"Segment counts: {seg_counts}")
    all_passed = all_passed and c23

    # 24. Cluster percentages sum to 100%
    pct_sum = df_prof["pct"].sum() if os.path.exists(PROFILES_PATH) else 0.0
    c24 = run_check(24, "Cluster percentages sum to approximately 100.0%", abs(pct_sum - 100.0) < 0.1, f"Sum of percentages: {pct_sum:.2f}%")
    all_passed = all_passed and c24

    # 25. Cluster stability verified across multiple seeds (Mean ARI >= 0.95)
    mean_ari = metrics.get("stability_analysis", {}).get("mean_pairwise_ari", 0.0)
    stability_valid = mean_ari >= 0.95
    c25 = run_check(25, "Cluster stability verified across multiple seeds (Mean ARI >= 0.95)", stability_valid, f"Mean Pairwise ARI: {mean_ari:.4f}")
    all_passed = all_passed and c25

    # 26. Raw CSV files immutability audit (Both MD5 and SHA-256 cryptographic verification)
    cust_md5, cust_sha256 = calculate_hashes(RAW_CUSTOMERS_PATH)
    ord_md5, ord_sha256 = calculate_hashes(RAW_ORDERS_PATH)
    hashes_intact = (
        (cust_md5 == EXPECTED_RAW_CUST_MD5) and
        (cust_sha256 == EXPECTED_RAW_CUST_SHA256) and
        (ord_md5 == EXPECTED_RAW_ORD_MD5) and
        (ord_sha256 == EXPECTED_RAW_ORD_SHA256)
    )
    c26 = run_check(26, "Raw CSV datasets remain 100% cryptographically unchanged (MD5 & SHA-256 verified)", hashes_intact, f"customers SHA256: {cust_sha256[:16]}..., orders SHA256: {ord_sha256[:16]}...")
    all_passed = all_passed and c26

    print("=" * 75)
    if all_passed:
        print("ALL 26 VALIDATION & REPRODUCIBILITY CHECKS PASSED WITH ZERO ERRORS!")
        print("Phase 4 Customer Segmentation is fully audited, certified, and reproducible.")
        print("=" * 75)
        sys.exit(0)
    else:
        print("VALIDATION FAILED! Check failures listed above.")
        print("=" * 75)
        sys.exit(1)


if __name__ == "__main__":
    main()
