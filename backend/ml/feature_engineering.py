"""
Indian E-Commerce Customer Retention Intelligence System
Module: Feature Engineering & Preprocessing Pipeline
Description: Aggregates historical transaction records into customer-level behavioral features.
             Enforces strict zero future-data leakage (historical orders <= 2025-12-31).
             Extracts RFM, velocity, friction, and financial channel metrics.

Author: BCA (AI & ML) Project Team
Cutoff Date: 2025-12-31
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Constants & Paths
SNAPSHOT_DATE_STR = "2025-12-31"
SNAPSHOT_DATE = datetime(2025, 12, 31)
RAW_CUST_PATH = os.path.join("data", "raw", "customers.csv")
RAW_ORD_PATH = os.path.join("data", "raw", "orders.csv")
PROCESSED_DIR = os.path.join("data", "processed")
OUTPUT_FEATURES_PATH = os.path.join(PROCESSED_DIR, "customer_features.csv")
MANIFEST_PATH = os.path.join(PROCESSED_DIR, "feature_manifest.json")

os.makedirs(PROCESSED_DIR, exist_ok=True)


def load_raw_data(cust_path=RAW_CUST_PATH, ord_path=RAW_ORD_PATH):
    """Load raw customers and orders CSV files safely."""
    if not os.path.exists(cust_path):
        raise FileNotFoundError(f"Customer dataset not found: {cust_path}")
    if not os.path.exists(ord_path):
        raise FileNotFoundError(f"Orders dataset not found: {ord_path}")

    cust_df = pd.read_csv(cust_path)
    ord_df = pd.read_csv(ord_path)

    # Validate essential source columns
    expected_cust_cols = {"customer_id", "customer_name", "signup_date", "city", "state", "snapshot_date", "churn"}
    expected_ord_cols = {"order_id", "customer_id", "order_date", "order_amount_inr", "category",
                         "payment_method", "discount_amount_inr", "order_status", "return_status", "delivery_delay_days"}

    if not expected_cust_cols.issubset(cust_df.columns):
        raise ValueError(f"Missing columns in customers.csv: {expected_cust_cols - set(cust_df.columns)}")
    if not expected_ord_cols.issubset(ord_df.columns):
        raise ValueError(f"Missing columns in orders.csv: {expected_ord_cols - set(ord_df.columns)}")

    return cust_df, ord_df


def engineer_features(cust_df, ord_df, snapshot_date_str=SNAPSHOT_DATE_STR):
    """
    Compute customer-level predictive features strictly using historical orders.
    Zero future orders or churn targets enter the feature calculation.
    """
    snapshot_dt = pd.to_datetime(snapshot_date_str)
    
    # 1. Temporal Separation: Filter orders strictly <= snapshot date
    ord_df = ord_df.copy()
    ord_df["order_date_dt"] = pd.to_datetime(ord_df["order_date"])
    
    # STRICT ASSERTION: Only historical orders are passed to feature engineering
    hist_orders = ord_df[ord_df["order_date_dt"] <= snapshot_dt].copy()
    
    # 2. Base Customer Profile Features
    cust_df = cust_df.copy()
    cust_df["signup_date_dt"] = pd.to_datetime(cust_df["signup_date"])
    
    # Tenure in days as of snapshot date
    cust_df["customer_tenure_days"] = (snapshot_dt - cust_df["signup_date_dt"]).dt.days
    
    # Clean demographic missingness with explicit category (preserves missingness without fabricating data)
    cust_df["city"] = cust_df["city"].fillna("Unknown")
    cust_df["state"] = cust_df["state"].fillna("Unknown")

    # 3. Customer-Level Historical Aggregations
    # Velocity Windows (Strictly ending on snapshot date)
    date_30_start = snapshot_dt - timedelta(days=29)
    date_90_start = snapshot_dt - timedelta(days=89)
    date_180_start = snapshot_dt - timedelta(days=179)

    hist_orders["is_last_30"] = (hist_orders["order_date_dt"] >= date_30_start).astype(int)
    hist_orders["is_last_90"] = (hist_orders["order_date_dt"] >= date_90_start).astype(int)
    hist_orders["is_last_180"] = (hist_orders["order_date_dt"] >= date_180_start).astype(int)

    hist_orders["is_delivered"] = (hist_orders["order_status"] == "Delivered").astype(int)
    hist_orders["is_returned"] = (hist_orders["order_status"] == "Returned").astype(int)
    hist_orders["is_cancelled"] = (hist_orders["order_status"] == "Cancelled").astype(int)

    hist_orders["is_cod"] = (hist_orders["payment_method"] == "COD").astype(int)
    hist_orders["is_upi"] = (hist_orders["payment_method"] == "UPI").astype(int)

    # Missingness indicators
    hist_orders["delay_is_missing"] = hist_orders["delivery_delay_days"].isnull().astype(int)
    hist_orders["discount_is_missing"] = hist_orders["discount_amount_inr"].isnull().astype(int)
    hist_orders["payment_is_missing"] = hist_orders["payment_method"].isnull().astype(int)
    hist_orders["has_discount"] = (hist_orders["discount_amount_inr"] > 0).astype(int)

    # Delivered order date source for fulfilled recency
    hist_orders["delivered_order_date"] = hist_orders["order_date_dt"].where(hist_orders["is_delivered"] == 1)

    # Delivered in velocity windows
    hist_orders["delivered_last_30"] = (hist_orders["is_delivered"] & hist_orders["is_last_30"]).astype(int)
    hist_orders["delivered_last_90"] = (hist_orders["is_delivered"] & hist_orders["is_last_90"]).astype(int)
    hist_orders["delivered_last_180"] = (hist_orders["is_delivered"] & hist_orders["is_last_180"]).astype(int)

    # Group by customer_id
    agg_dict = {
        # Recency sources
        "last_order_date": ("order_date_dt", "max"),
        "last_delivered_order_date": ("delivered_order_date", "max"),
        
        # Frequency metrics
        "hist_order_count": ("order_id", "count"),
        "hist_delivered_order_count": ("is_delivered", "sum"),
        "hist_returned_order_count": ("is_returned", "sum"),
        "hist_cancelled_order_count": ("is_cancelled", "sum"),
        
        # Monetary metrics
        "hist_total_order_value_inr": ("order_amount_inr", "sum"),
        "hist_delivered_order_value_inr": ("order_amount_inr", lambda s: hist_orders.loc[s.index, "order_amount_inr"][hist_orders.loc[s.index, "is_delivered"] == 1].sum()),
        "hist_total_recorded_discount_inr": ("discount_amount_inr", lambda s: s.sum(skipna=True)),
        
        # Velocity metrics (recorded orders)
        "orders_last_30_days": ("is_last_30", "sum"),
        "orders_last_90_days": ("is_last_90", "sum"),
        "orders_last_180_days": ("is_last_180", "sum"),
        
        # Velocity metrics (delivered orders)
        "delivered_orders_last_30_days": ("delivered_last_30", "sum"),
        "delivered_orders_last_90_days": ("delivered_last_90", "sum"),
        "delivered_orders_last_180_days": ("delivered_last_180", "sum"),
        
        # Friction metrics
        "hist_average_delivery_delay_days": ("delivery_delay_days", "mean"),
        "hist_delivery_delay_missing_count": ("delay_is_missing", "sum"),
        
        # Payment & discount metrics
        "hist_average_discount_amount_inr": ("discount_amount_inr", "mean"),
        "hist_discounted_order_count": ("has_discount", "sum"),
        "hist_discount_missing_count": ("discount_is_missing", "sum"),
        "hist_payment_missing_count": ("payment_is_missing", "sum"),
        "hist_cod_order_count": ("is_cod", "sum"),
        "hist_upi_order_count": ("is_upi", "sum"),
    }

    cust_agg = hist_orders.groupby("customer_id").agg(**agg_dict).reset_index()

    # 4. Merge aggregations with full customer demographic list (Ensures all 7,000 customers are preserved)
    features_df = cust_df[[
        "customer_id", "customer_name", "signup_date", "city", "state", "customer_tenure_days", "churn"
    ]].merge(cust_agg, on="customer_id", how="left")

    # 5. Handle Zero-Order and Zero-Delivered Edge Cases Cleanly
    # Flag indicating whether customer has historical order activity
    has_history = features_df["hist_order_count"].notnull() & (features_df["hist_order_count"] > 0)
    features_df["has_historical_orders"] = has_history.astype(int)

    # Order-attempt recency: days since latest historical order across all statuses
    features_df["recency_days"] = np.where(
        has_history,
        (snapshot_dt - features_df["last_order_date"]).dt.days,
        np.nan
    )

    # Clean count variables for 0-order accounts
    count_cols = [
        "hist_order_count", "hist_delivered_order_count", "hist_returned_order_count", "hist_cancelled_order_count",
        "orders_last_30_days", "orders_last_90_days", "orders_last_180_days",
        "delivered_orders_last_30_days", "delivered_orders_last_90_days", "delivered_orders_last_180_days",
        "hist_delivery_delay_missing_count", "hist_discounted_order_count", "hist_discount_missing_count",
        "hist_payment_missing_count", "hist_cod_order_count", "hist_upi_order_count"
    ]
    for c in count_cols:
        features_df[c] = features_df[c].fillna(0).astype(int)

    # Delivered order indicators and fulfilled purchase recency
    has_delivered = features_df["hist_delivered_order_count"] > 0
    features_df["has_delivered_order"] = has_delivered.astype(int)
    features_df["recency_delivered_days"] = np.where(
        has_delivered,
        (snapshot_dt - features_df["last_delivered_order_date"]).dt.days,
        np.nan
    )

    monetary_cols = [
        "hist_total_order_value_inr", "hist_delivered_order_value_inr", "hist_total_recorded_discount_inr"
    ]
    for c in monetary_cols:
        features_df[c] = features_df[c].fillna(0.0).round(2)

    # Derived Rate Features (denominator is hist_order_count)
    features_df["hist_return_rate"] = np.where(
        has_history,
        features_df["hist_returned_order_count"] / features_df["hist_order_count"],
        0.0
    ).round(4)

    features_df["hist_cancellation_rate"] = np.where(
        has_history,
        features_df["hist_cancelled_order_count"] / features_df["hist_order_count"],
        0.0
    ).round(4)

    features_df["hist_delivery_delay_missing_rate"] = np.where(
        has_history,
        features_df["hist_delivery_delay_missing_count"] / features_df["hist_order_count"],
        0.0
    ).round(4)

    features_df["hist_discount_missing_rate"] = np.where(
        has_history,
        features_df["hist_discount_missing_count"] / features_df["hist_order_count"],
        0.0
    ).round(4)

    features_df["hist_payment_missing_rate"] = np.where(
        has_history,
        features_df["hist_payment_missing_count"] / features_df["hist_order_count"],
        0.0
    ).round(4)

    features_df["hist_cod_usage_rate"] = np.where(
        has_history,
        features_df["hist_cod_order_count"] / features_df["hist_order_count"],
        0.0
    ).round(4)

    features_df["hist_upi_usage_rate"] = np.where(
        has_history,
        features_df["hist_upi_order_count"] / features_df["hist_order_count"],
        0.0
    ).round(4)

    # Average Order Value (AOV): By deliberate business convention, ₹0.0 for zero-order accounts
    features_df["hist_average_order_value_inr"] = np.where(
        has_history,
        (features_df["hist_total_order_value_inr"] / features_df["hist_order_count"]).round(2),
        0.0
    )

    # Round average delay and discount
    features_df["hist_average_delivery_delay_days"] = features_df["hist_average_delivery_delay_days"].round(2)
    features_df["hist_average_discount_amount_inr"] = features_df["hist_average_discount_amount_inr"].round(2)

    # Drop temporary date object columns
    features_df = features_df.drop(columns=["last_order_date", "last_delivered_order_date"])

    # Final Column Ordering: 40 total columns
    # Identifiers (3) -> Profile & History (4) -> Recency (2) -> Fulfillment Flag (1) -> Frequency (4) -> Monetary (4) -> Velocity (6) -> Friction (5) -> Discount & Payment (10) -> Target (1)
    ordered_cols = [
        # Identifiers
        "customer_id", "customer_name", "signup_date",
        # Profile & History Flags
        "city", "state", "customer_tenure_days", "has_historical_orders",
        # Recency & Fulfillment
        "recency_days", "recency_delivered_days", "has_delivered_order",
        # Frequency
        "hist_order_count", "hist_delivered_order_count", "hist_returned_order_count", "hist_cancelled_order_count",
        # Monetary
        "hist_total_order_value_inr", "hist_delivered_order_value_inr", "hist_total_recorded_discount_inr", "hist_average_order_value_inr",
        # Velocity (Total recorded)
        "orders_last_30_days", "orders_last_90_days", "orders_last_180_days",
        # Velocity (Delivered)
        "delivered_orders_last_30_days", "delivered_orders_last_90_days", "delivered_orders_last_180_days",
        # Friction
        "hist_return_rate", "hist_cancellation_rate", "hist_average_delivery_delay_days",
        "hist_delivery_delay_missing_count", "hist_delivery_delay_missing_rate",
        # Financial & Payment Channels
        "hist_average_discount_amount_inr", "hist_discounted_order_count", "hist_discount_missing_count", "hist_discount_missing_rate",
        "hist_payment_missing_count", "hist_payment_missing_rate",
        "hist_cod_order_count", "hist_cod_usage_rate", "hist_upi_order_count", "hist_upi_usage_rate",
        # Target Label
        "churn"
    ]

    return features_df[ordered_cols]


def create_feature_manifest(features_df):
    """Generate comprehensive documentation manifest for all engineered features."""
    manifest = {
        "metadata": {
            "title": "Indian E-Commerce Customer Retention Feature Manifest",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "snapshot_cutoff_date": SNAPSHOT_DATE_STR,
            "target_label_window": "2026-01-01 through 2026-03-31, inclusive",
            "total_customers": len(features_df),
            "target_column": "churn",
            "identifier_columns": ["customer_id", "customer_name", "signup_date"],
            "leakage_safeguard": "All behavioral and transaction features are calculated strictly using historical orders where order_date <= 2025-12-31. Future orders are strictly excluded."
        },
        "target_definition": {
            "name": "churn",
            "type": "binary_integer",
            "values": {
                "0": "Retained (Customer completed at least 1 order between 2026-01-01 and 2026-03-31)",
                "1": "Churned (Customer placed zero orders between 2026-01-01 and 2026-03-31)"
            },
            "source": "Existing validated ground truth from data/raw/customers.csv"
        },
        "features": {
            # Profile Features
            "customer_id": {
                "role": "identifier", "type": "string",
                "description": "Unique customer identification code",
                "formula": "Primary key from customers.csv"
            },
            "customer_name": {
                "role": "identifier", "type": "string",
                "description": "Customer full name (Excluded from predictive models to prevent demographic overfitting)",
                "formula": "Direct from customers.csv"
            },
            "signup_date": {
                "role": "profile", "type": "date_string",
                "description": "Account registration date (YYYY-MM-DD)",
                "formula": "Direct from customers.csv"
            },
            "city": {
                "role": "predictive", "type": "categorical",
                "description": "Customer registered city",
                "formula": "customers.city with missing values encoded as 'Unknown'"
            },
            "state": {
                "role": "predictive", "type": "categorical",
                "description": "Customer registered state",
                "formula": "customers.state with missing values encoded as 'Unknown'"
            },
            "customer_tenure_days": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Account age in days as of snapshot date (2025-12-31)",
                "formula": "2025-12-31 - signup_date"
            },
            "has_historical_orders": {
                "role": "predictive", "type": "binary_indicator",
                "description": "Flag indicating whether customer has placed at least 1 order prior to snapshot date",
                "formula": "1 if hist_order_count > 0 else 0"
            },

            # RFM - Recency & Fulfillment
            "recency_days": {
                "role": "predictive", "type": "numerical_float",
                "description": "Days elapsed since the customer's last recorded order attempt across all statuses as of 2025-12-31 (NaN for zero-order accounts)",
                "formula": "2025-12-31 - max(order_date <= 2025-12-31)"
            },
            "recency_delivered_days": {
                "role": "predictive", "type": "numerical_float",
                "description": "Days elapsed since the customer's last successfully delivered order as of 2025-12-31 (NaN if no delivered orders)",
                "formula": "2025-12-31 - max(order_date <= 2025-12-31 where order_status == 'Delivered')"
            },
            "has_delivered_order": {
                "role": "predictive", "type": "binary_indicator",
                "description": "Flag indicating whether customer has at least 1 delivered order prior to snapshot date",
                "formula": "1 if hist_delivered_order_count > 0 else 0"
            },

            # RFM - Frequency
            "hist_order_count": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Total historical recorded orders placed by customer",
                "formula": "Count of historical order records"
            },
            "hist_delivered_order_count": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Total historical orders successfully delivered",
                "formula": "Count of orders where order_status == 'Delivered'"
            },
            "hist_returned_order_count": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Total historical orders returned by customer",
                "formula": "Count of orders where order_status == 'Returned'"
            },
            "hist_cancelled_order_count": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Total historical orders cancelled before delivery",
                "formula": "Count of orders where order_status == 'Cancelled'"
            },

            # RFM - Monetary
            "hist_total_order_value_inr": {
                "role": "predictive", "type": "numerical_float",
                "description": "Cumulative gross value of all booked orders placed by customer (INR)",
                "formula": "Sum of order_amount_inr across all historical orders"
            },
            "hist_delivered_order_value_inr": {
                "role": "predictive", "type": "numerical_float",
                "description": "Cumulative gross sales value of successfully delivered orders (INR)",
                "formula": "Sum of order_amount_inr where order_status == 'Delivered'"
            },
            "hist_total_recorded_discount_inr": {
                "role": "predictive", "type": "numerical_float",
                "description": "Cumulative promotional discount amount recorded for customer (INR, skipna=True)",
                "formula": "Sum of recorded discount_amount_inr across historical orders"
            },
            "hist_average_order_value_inr": {
                "role": "predictive", "type": "numerical_float",
                "description": "Average booked order value (AOV) per customer (INR). Exactly 0.0 for zero-order accounts by deliberate convention.",
                "formula": "hist_total_order_value_inr / hist_order_count if hist_order_count > 0 else 0.0"
            },

            # Velocity - Recorded Orders
            "orders_last_30_days": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Total orders booked within the last 30 days of the snapshot period (2025-12-02 to 2025-12-31)",
                "formula": "Count of orders where order_date >= 2025-12-02"
            },
            "orders_last_90_days": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Total orders booked within the last 90 days of the snapshot period (2025-10-03 to 2025-12-31)",
                "formula": "Count of orders where order_date >= 2025-10-03"
            },
            "orders_last_180_days": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Total orders booked within the last 180 days of the snapshot period (2025-07-05 to 2025-12-31)",
                "formula": "Count of orders where order_date >= 2025-07-05"
            },

            # Velocity - Delivered Orders
            "delivered_orders_last_30_days": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Delivered orders completed in last 30 days before snapshot date",
                "formula": "Count of delivered orders where order_date >= 2025-12-02"
            },
            "delivered_orders_last_90_days": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Delivered orders completed in last 90 days before snapshot date",
                "formula": "Count of delivered orders where order_date >= 2025-10-03"
            },
            "delivered_orders_last_180_days": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Delivered orders completed in last 180 days before snapshot date",
                "formula": "Count of delivered orders where order_date >= 2025-07-05"
            },

            # Customer Friction
            "hist_return_rate": {
                "role": "predictive", "type": "numerical_float",
                "description": "Proportion of customer orders that were returned",
                "formula": "hist_returned_order_count / hist_order_count"
            },
            "hist_cancellation_rate": {
                "role": "predictive", "type": "numerical_float",
                "description": "Proportion of customer orders that were cancelled",
                "formula": "hist_cancelled_order_count / hist_order_count"
            },
            "hist_average_delivery_delay_days": {
                "role": "predictive", "type": "numerical_float",
                "description": "Average delivery delay days experienced across recorded historical orders (NaN if no records)",
                "formula": "Mean of non-null delivery_delay_days"
            },
            "hist_delivery_delay_missing_count": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Count of historical orders where delivery delay was unrecorded",
                "formula": "Count of orders where delivery_delay_days is null"
            },
            "hist_delivery_delay_missing_rate": {
                "role": "predictive", "type": "numerical_float",
                "description": "Proportion of customer orders with missing delivery delay records",
                "formula": "hist_delivery_delay_missing_count / hist_order_count"
            },

            # Financial & Payment Channels
            "hist_average_discount_amount_inr": {
                "role": "predictive", "type": "numerical_float",
                "description": "Average promotional discount received on recorded discounted orders (INR)",
                "formula": "Mean of non-null discount_amount_inr"
            },
            "hist_discounted_order_count": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Count of historical orders with recorded discount > 0",
                "formula": "Count of orders where discount_amount_inr > 0"
            },
            "hist_discount_missing_count": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Count of historical orders where discount information was missing",
                "formula": "Count of orders where discount_amount_inr is null"
            },
            "hist_discount_missing_rate": {
                "role": "predictive", "type": "numerical_float",
                "description": "Proportion of orders with missing discount record",
                "formula": "hist_discount_missing_count / hist_order_count"
            },
            "hist_payment_missing_count": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Count of historical orders where payment method was unrecorded (null)",
                "formula": "Count of historical orders where payment_method is null"
            },
            "hist_payment_missing_rate": {
                "role": "predictive", "type": "numerical_float",
                "description": "Proportion of customer orders with unrecorded payment method",
                "formula": "hist_payment_missing_count / hist_order_count if hist_order_count > 0 else 0.0"
            },
            "hist_cod_order_count": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Number of orders paid using Cash on Delivery (COD)",
                "formula": "Count of orders where payment_method == 'COD'"
            },
            "hist_cod_usage_rate": {
                "role": "predictive", "type": "numerical_float",
                "description": "Proportion of customer orders paid using Cash on Delivery (COD)",
                "formula": "hist_cod_order_count / hist_order_count"
            },
            "hist_upi_order_count": {
                "role": "predictive", "type": "numerical_integer",
                "description": "Number of orders paid using Unified Payments Interface (UPI)",
                "formula": "Count of orders where payment_method == 'UPI'"
            },
            "hist_upi_usage_rate": {
                "role": "predictive", "type": "numerical_float",
                "description": "Proportion of customer orders paid using Unified Payments Interface (UPI)",
                "formula": "hist_upi_order_count / hist_order_count"
            },
            "churn": {
                "role": "target", "type": "binary_integer",
                "description": "Ground truth 90-day churn label (0 = Retained, 1 = Churned)",
                "formula": "1 if customer placed zero orders between 2026-01-01 and 2026-03-31 else 0"
            }
        }
    }
    return manifest


def main():
    print("=" * 75)
    print("PHASE 3: DATA CLEANING & FEATURE ENGINEERING")
    print(f"Snapshot Cutoff: {SNAPSHOT_DATE_STR} | Output Directory: {PROCESSED_DIR}")
    print("=" * 75)

    # 1. Load raw data
    print("Loading raw datasets...")
    cust_df, ord_df = load_raw_data()
    print(f"Loaded {len(cust_df):,} customers and {len(ord_df):,} orders.")

    # 2. Engineer features
    print("Executing historical feature aggregation with strict temporal boundary...")
    features_df = engineer_features(cust_df, ord_df)

    # 3. Save processed customer features dataset
    features_df.to_csv(OUTPUT_FEATURES_PATH, index=False)
    print(f"\nSuccessfully generated feature dataset: {OUTPUT_FEATURES_PATH}")
    print(f"  - Total Rows:    {len(features_df):,} customers")
    print(f"  - Total Columns: {len(features_df.columns)} columns")

    # 4. Generate and save feature manifest
    manifest = create_feature_manifest(features_df)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Successfully generated feature manifest: {MANIFEST_PATH}")

    # 5. Summary metrics
    num_pred_features = sum(1 for f in manifest["features"].values() if f.get("role") == "predictive")
    print("\nFeature Engineering Summary:")
    print(f"  - Total Features in Dataset: {len(features_df.columns)}")
    print(f"  - Total Predictive Features: {num_pred_features}")
    print(f"  - Target Label:             {manifest['metadata']['target_column']} (Binary 0/1)")
    print(f"  - Zero-History Customers:   {(features_df['has_historical_orders'] == 0).sum():,} ({((features_df['has_historical_orders'] == 0).mean()*100):.2f}%)")
    print(f"  - Single-Order Customers:   {(features_df['hist_order_count'] == 1).sum():,} ({((features_df['hist_order_count'] == 1).mean()*100):.2f}%)")
    print(f"  - Multi-Order Customers:    {(features_df['hist_order_count'] > 1).sum():,} ({((features_df['hist_order_count'] > 1).mean()*100):.2f}%)")

    print("\nMissing Values in Processed Feature Dataset:")
    nulls = features_df.isnull().sum()
    if nulls.sum() == 0:
        print("  None! (All features complete)")
    else:
        for col, cnt in nulls[nulls > 0].items():
            print(f"  - {col}: {cnt:,} missing ({cnt/len(features_df)*100:.2f}%) [Preserved for training-only imputer]")

    print("=" * 75)
    print("Phase 3 Feature Engineering complete! Ready for validation suite.")
    print("=" * 75)


if __name__ == "__main__":
    main()
