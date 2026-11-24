"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5.1 — Checkpoint 2: Independent Synthetic Test Cohort Generator
Description: Generates an independent, isolated, reproducible evaluation cohort of exactly
             1,500 synthetic Indian e-commerce customers and their order history using
             seed 2026. Enforces strict ID disjointness against existing Phase 1 raw data.

Author: BCA (AI & ML) Project Team
Random Seed: 2026
Snapshot Date: 2025-12-31
Label Window: 2026-01-01 to 2026-03-31 (90 days)
"""

import os
import sys
import json
import random
import hashlib
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Paths Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

EXISTING_RAW_CUST = os.path.join(PROJECT_ROOT, "data", "raw", "customers.csv")
EXISTING_RAW_ORD = os.path.join(PROJECT_ROOT, "data", "raw", "orders.csv")

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "independent_test", "raw")
OUTPUT_CUST_PATH = os.path.join(OUTPUT_DIR, "customers_independent.csv")
OUTPUT_ORD_PATH = os.path.join(OUTPUT_DIR, "orders_independent.csv")
MANIFEST_PATH = os.path.join(OUTPUT_DIR, "independent_cohort_manifest.json")

# Cohort Constants
INDEPENDENT_SEED = 2026
NUM_INDEPENDENT_CUSTOMERS = 1500
CUSTOMER_ID_START = 50001
ORDER_ID_START = 500001

SNAPSHOT_DATE = datetime(2025, 12, 31)
OBSERVATION_START_DATE = datetime(2023, 1, 1)
FUTURE_WINDOW_DAYS = 90
LABEL_END_DATE = SNAPSHOT_DATE + timedelta(days=FUTURE_WINDOW_DAYS)

# Authentic Indian Demographics
INDIAN_CITIES_STATES = [
    ("Bhopal", "Madhya Pradesh"),
    ("Indore", "Madhya Pradesh"),
    ("Mumbai", "Maharashtra"),
    ("Pune", "Maharashtra"),
    ("Nagpur", "Maharashtra"),
    ("Delhi", "Delhi"),
    ("Jaipur", "Rajasthan"),
    ("Bengaluru", "Karnataka"),
    ("Mysuru", "Karnataka"),
    ("Hyderabad", "Telangana"),
    ("Chennai", "Tamil Nadu"),
    ("Coimbatore", "Tamil Nadu"),
    ("Kolkata", "West Bengal"),
    ("Ahmedabad", "Gujarat"),
    ("Surat", "Gujarat"),
    ("Lucknow", "Uttar Pradesh"),
    ("Varanasi", "Uttar Pradesh"),
    ("Patna", "Bihar"),
    ("Chandigarh", "Punjab"),
    ("Kochi", "Kerala"),
    ("Bhubaneswar", "Odisha"),
    ("Guwahati", "Assam")
]

FIRST_NAMES = [
    "Aarav", "Rohan", "Priya", "Ananya", "Rajesh", "Vikram", "Neha", "Pooja",
    "Amit", "Suresh", "Sunita", "Deepak", "Kavita", "Rahul", "Sneha", "Aditya",
    "Manoj", "Swati", "Divya", "Rakesh", "Manish", "Shilpa", "Sanjay", "Meera",
    "Arjun", "Lakshmi", "Harish", "Bhavna", "Alok", "Shweta", "Gaurav", "Anita",
    "Vikas", "Tanvi", "Kunal", "Preeti", "Nitin", "Komal", "Abhishek", "Ritika",
    "Pradeep", "Simran", "Ashish", "Anjali", "Varun", "Pallavi", "Sachin", "Monika"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Singh", "Joshi", "Kumar", "Mehta",
    "Rao", "Nair", "Das", "Chatterjee", "Banerjee", "Mukherjee", "Reddy", "Iyer",
    "Kulkarni", "Deshmukh", "Patil", "Yadav", "Mishra", "Chauhan", "Jain", "Agarwal",
    "Tiwari", "Pandey", "Bhat", "Nambiar", "Pillai", "Choudhury", "Saxena", "Malhotra"
]

CATEGORIES = [
    "Electronics", "Fashion", "Grocery", "Beauty", "Home", "Books", "Sports"
]

CATEGORY_PRICE_RANGES = {
    "Electronics": (1500, 35000),
    "Fashion": (400, 4500),
    "Grocery": (250, 2800),
    "Beauty": (200, 2200),
    "Home": (500, 8500),
    "Books": (150, 1400),
    "Sports": (350, 5000)
}

PAYMENT_METHODS = ["UPI", "COD", "Credit Card", "Debit Card", "Net Banking", "Wallet"]
PAYMENT_WEIGHTS = [0.46, 0.24, 0.14, 0.08, 0.05, 0.03]


def compute_sha256(file_path):
    """Compute cryptographic SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest().upper()


def generate_independent_customers(rng_np, rng_py, num_cust=NUM_INDEPENDENT_CUSTOMERS, cust_id_start=CUSTOMER_ID_START):
    """Generates independent customers with identical latent persona distributions."""
    customers = []
    total_days_range = (SNAPSHOT_DATE - OBSERVATION_START_DATE).days - 5

    for i in range(num_cust):
        cust_id = f"IND_CUST_{cust_id_start + i}"
        first_name = rng_py.choice(FIRST_NAMES)
        last_name = rng_py.choice(LAST_NAMES)
        customer_name = f"{first_name} {last_name}"

        city, state = rng_py.choice(INDIAN_CITIES_STATES)

        # Skewed signup date
        offset_days = int((rng_np.power(1.6)) * total_days_range)
        signup_date = OBSERVATION_START_DATE + timedelta(days=offset_days)

        # Latent Persona Assignment
        persona_roll = rng_np.random()
        if persona_roll < 0.15:
            persona = "loyal_vip"
            base_order_freq = rng_np.uniform(1.2, 2.8)
            churn_propensity = 0.08
        elif persona_roll < 0.40:
            persona = "steady"
            base_order_freq = rng_np.uniform(0.6, 1.3)
            churn_propensity = 0.22
        elif persona_roll < 0.65:
            persona = "occasional"
            base_order_freq = rng_np.uniform(0.2, 0.6)
            churn_propensity = 0.45
        elif persona_roll < 0.85:
            persona = "dissatisfied"
            base_order_freq = rng_np.uniform(0.3, 0.8)
            churn_propensity = 0.68
        elif persona_roll < 0.98:
            persona = "dormant"
            base_order_freq = 0.05
            churn_propensity = 0.88
        else:
            persona = "zero_order"
            base_order_freq = 0.0
            churn_propensity = 0.94

        customers.append({
            "customer_id": cust_id,
            "customer_name": customer_name,
            "signup_date": signup_date,
            "city": city,
            "state": state,
            "snapshot_date": SNAPSHOT_DATE.strftime("%Y-%m-%d"),
            "persona": persona,
            "base_order_freq": base_order_freq,
            "churn_propensity": churn_propensity
        })

    return pd.DataFrame(customers)


def generate_independent_orders_and_churn(customers_df, rng_np, rng_py, order_id_start=ORDER_ID_START):
    """Simulates historical transactions, Bernoulli churn targets, and future order validation."""
    orders = []
    order_id_counter = order_id_start
    churn_labels = []

    for _, cust in customers_df.iterrows():
        cust_id = cust["customer_id"]
        signup_dt = cust["signup_date"]
        persona = cust["persona"]
        churn_prob = cust["churn_propensity"]

        historical_days = (SNAPSHOT_DATE - signup_dt).days

        # 1. Historical Orders Simulation (<= 2025-12-31)
        if persona == "zero_order":
            hist_orders_count = 0
        elif persona == "dormant":
            hist_orders_count = 1
        else:
            months = max(1, historical_days / 30.0)
            expected_orders = max(1, int(cust["base_order_freq"] * months))
            hist_orders_count = max(1, int(rng_np.poisson(expected_orders)))
            hist_orders_count = min(hist_orders_count, 65)

        if hist_orders_count > 0:
            if persona == "dormant":
                order_offsets = [rng_py.randint(1, min(15, historical_days))]
            else:
                order_offsets = sorted(rng_py.sample(range(0, historical_days + 1), k=hist_orders_count))

            for offset in order_offsets:
                ord_dt = signup_dt + timedelta(days=offset)
                category = rng_py.choice(CATEGORIES)
                min_p, max_p = CATEGORY_PRICE_RANGES[category]
                base_price = float(np.round(rng_np.uniform(min_p, max_p), 2))

                if persona == "dissatisfied":
                    delay = int(rng_np.choice([0, 2, 4, 6, 8, 11], p=[0.30, 0.20, 0.20, 0.15, 0.10, 0.05]))
                    is_return = rng_np.choice([0, 1], p=[0.75, 0.25])
                    is_cancel = rng_np.choice([0, 1], p=[0.85, 0.15])
                elif persona == "loyal_vip":
                    delay = int(rng_np.choice([0, 1, 2, 4], p=[0.80, 0.12, 0.06, 0.02]))
                    is_return = rng_np.choice([0, 1], p=[0.96, 0.04])
                    is_cancel = rng_np.choice([0, 1], p=[0.98, 0.02])
                else:
                    delay = int(rng_np.choice([0, 1, 2, 3, 5, 8], p=[0.68, 0.16, 0.08, 0.04, 0.03, 0.01]))
                    is_return = rng_np.choice([0, 1], p=[0.92, 0.08])
                    is_cancel = rng_np.choice([0, 1], p=[0.94, 0.06])

                if is_cancel:
                    order_status = "Cancelled"
                    return_status = "Not Returned"
                elif is_return:
                    order_status = "Returned"
                    return_status = rng_np.choice(["Returned", "Return Requested"], p=[0.85, 0.15])
                else:
                    order_status = "Delivered"
                    return_status = "Not Returned"

                pay_method = rng_np.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)
                if rng_np.random() < 0.65:
                    discount = float(np.round(base_price * rng_np.uniform(0.05, 0.25), 2))
                else:
                    discount = 0.0

                orders.append({
                    "order_id": f"ORD_{order_id_counter}",
                    "customer_id": cust_id,
                    "order_date": ord_dt.strftime("%Y-%m-%d"),
                    "order_amount_inr": base_price,
                    "category": category,
                    "payment_method": pay_method,
                    "discount_amount_inr": discount,
                    "order_status": order_status,
                    "return_status": return_status,
                    "delivery_delay_days": delay
                })
                order_id_counter += 1

        # 2. Ground-Truth Churn Determination (Bernoulli Trial)
        final_churn_roll = rng_np.random()
        churn_decision = 1 if final_churn_roll < churn_prob else 0
        churn_labels.append(churn_decision)

        # 3. Future Orders Generation (2026-01-01 to 2026-03-31)
        # churn == 0 -> >= 1 future order; churn == 1 -> exactly 0 future orders
        if churn_decision == 0:
            future_order_count = max(1, int(rng_np.poisson(max(1.0, cust["base_order_freq"] * 3.0))))
            future_order_count = min(future_order_count, 12)

            future_offsets = sorted(rng_py.sample(range(1, FUTURE_WINDOW_DAYS + 1), k=future_order_count))
            for offset in future_offsets:
                fut_dt = SNAPSHOT_DATE + timedelta(days=offset)
                category = rng_py.choice(CATEGORIES)
                min_p, max_p = CATEGORY_PRICE_RANGES[category]
                base_price = float(np.round(rng_np.uniform(min_p, max_p), 2))
                pay_method = rng_np.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)
                discount = float(np.round(base_price * rng_np.uniform(0.0, 0.20), 2)) if rng_np.random() < 0.6 else 0.0
                delay = int(rng_np.choice([0, 1, 2, 4], p=[0.75, 0.15, 0.07, 0.03]))

                orders.append({
                    "order_id": f"ORD_{order_id_counter}",
                    "customer_id": cust_id,
                    "order_date": fut_dt.strftime("%Y-%m-%d"),
                    "order_amount_inr": base_price,
                    "category": category,
                    "payment_method": pay_method,
                    "discount_amount_inr": discount,
                    "order_status": "Delivered",
                    "return_status": "Not Returned",
                    "delivery_delay_days": delay
                })
                order_id_counter += 1

    customers_df["churn"] = churn_labels
    customers_df["signup_date"] = customers_df["signup_date"].dt.strftime("%Y-%m-%d")

    customers_clean = customers_df[[
        "customer_id", "customer_name", "signup_date", "city", "state", "snapshot_date", "churn"
    ]].copy()

    orders_df = pd.DataFrame(orders)
    return customers_clean, orders_df


def inject_mild_imperfections(customers_df, orders_df, rng_np):
    """Applies realistic data imperfections identical to Phase 1 specs."""
    mask_delay = rng_np.random(len(orders_df)) < 0.020
    orders_df.loc[mask_delay, "delivery_delay_days"] = np.nan

    mask_discount = rng_np.random(len(orders_df)) < 0.018
    orders_df.loc[mask_discount, "discount_amount_inr"] = np.nan

    mask_payment = rng_np.random(len(orders_df)) < 0.012
    orders_df.loc[mask_payment, "payment_method"] = np.nan

    mask_cust_loc = rng_np.random(len(customers_df)) < 0.006
    customers_df.loc[mask_cust_loc, "city"] = np.nan
    customers_df.loc[mask_cust_loc, "state"] = np.nan

    return customers_df, orders_df


def verify_id_disjointness(new_cust_df, new_ord_df):
    """Rigorous exact set disjointness verification against existing raw datasets."""
    print("Verifying strict ID set disjointness against existing Phase 1 raw data...")
    assert os.path.exists(EXISTING_RAW_CUST), f"Missing existing customers: {EXISTING_RAW_CUST}"
    assert os.path.exists(EXISTING_RAW_ORD), f"Missing existing orders: {EXISTING_RAW_ORD}"

    existing_cust = pd.read_csv(EXISTING_RAW_CUST)
    existing_ord = pd.read_csv(EXISTING_RAW_ORD)

    existing_cust_ids = set(existing_cust["customer_id"])
    existing_ord_ids = set(existing_ord["order_id"])

    new_cust_ids = set(new_cust_df["customer_id"])
    new_ord_ids = set(new_ord_df["order_id"])

    cust_overlap = new_cust_ids.intersection(existing_cust_ids)
    ord_overlap = new_ord_ids.intersection(existing_ord_ids)

    assert len(cust_overlap) == 0, f"Customer ID collision detected: {len(cust_overlap)} overlap!"
    assert len(ord_overlap) == 0, f"Order ID collision detected: {len(ord_overlap)} overlap!"
    assert len(new_cust_ids) == len(new_cust_df), "Duplicate customer IDs found in new cohort!"
    assert len(new_ord_ids) == len(new_ord_df), "Duplicate order IDs found in new cohort!"

    print("   [PASSED] Customer ID set intersection: 0 overlapping records.")
    print("   [PASSED] Order ID set intersection: 0 overlapping records.")
    print(f"   [PASSED] New customer IDs: {len(new_cust_ids):,} completely unique.")
    print(f"   [PASSED] New order IDs: {len(new_ord_ids):,} completely unique.")
    return True


def generate_cohort(seed=INDEPENDENT_SEED):
    """Main generation execution with isolated RNG instances."""
    print("=" * 80)
    print("PHASE 5.1: GENERATING INDEPENDENT SYNTHETIC TEST COHORT")
    print(f"Seed: {seed} | Target Customers: {NUM_INDEPENDENT_CUSTOMERS}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 80)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Isolated RNG instances ensuring complete generator isolation
    rng_np = np.random.default_rng(seed)
    rng_py = random.Random(seed)

    # 1. Generate core customers
    raw_cust_df = generate_independent_customers(rng_np, rng_py)

    # 2. Generate orders and churn
    customers_df, orders_df = generate_independent_orders_and_churn(raw_cust_df, rng_np, rng_py)

    # 3. Inject imperfections
    customers_df, orders_df = inject_mild_imperfections(customers_df, orders_df, rng_np)

    # 4. Strict Set Disjointness Verification
    verify_id_disjointness(customers_df, orders_df)

    # 5. Save Datasets
    customers_df.to_csv(OUTPUT_CUST_PATH, index=False)
    orders_df.to_csv(OUTPUT_ORD_PATH, index=False)

    cust_sha256 = compute_sha256(OUTPUT_CUST_PATH)
    ord_sha256 = compute_sha256(OUTPUT_ORD_PATH)

    # Metrics summary
    churn_counts = customers_df["churn"].value_counts().to_dict()
    churn_rate = float(customers_df["churn"].mean())

    hist_orders = orders_df[pd.to_datetime(orders_df["order_date"]) <= SNAPSHOT_DATE]
    fut_orders = orders_df[pd.to_datetime(orders_df["order_date"]) > SNAPSHOT_DATE]

    manifest = {
        "dataset_name": "Phase 5.1 Independent Synthetic Test Cohort",
        "generated_at": datetime.now().isoformat(),
        "random_seed": seed,
        "snapshot_date": SNAPSHOT_DATE.strftime("%Y-%m-%d"),
        "label_window_start": "2026-01-01",
        "label_window_end": LABEL_END_DATE.strftime("%Y-%m-%d"),
        "future_window_days": FUTURE_WINDOW_DAYS,
        "customers": {
            "file": "customers_independent.csv",
            "sha256": cust_sha256,
            "total_records": len(customers_df),
            "customer_id_min": customers_df["customer_id"].min(),
            "customer_id_max": customers_df["customer_id"].max(),
            "churn_distribution": {
                "retained_0": int(churn_counts.get(0, 0)),
                "churned_1": int(churn_counts.get(1, 0)),
                "churn_rate": round(churn_rate, 4)
            }
        },
        "orders": {
            "file": "orders_independent.csv",
            "sha256": ord_sha256,
            "total_records": len(orders_df),
            "historical_records": len(hist_orders),
            "future_records": len(fut_orders),
            "order_id_min": orders_df["order_id"].min(),
            "order_id_max": orders_df["order_id"].max()
        },
        "isolation_proof": {
            "customer_id_overlap_count": 0,
            "order_id_overlap_count": 0,
            "set_disjointness_verified": True
        }
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\nIndependent test cohort generated and saved successfully:")
    print(f"   Customers: {OUTPUT_CUST_PATH} (N={len(customers_df)}, SHA-256: {cust_sha256})")
    print(f"   Orders   : {OUTPUT_ORD_PATH} (N={len(orders_df)}, SHA-256: {ord_sha256})")
    print(f"   Manifest : {MANIFEST_PATH}")
    print(f"   Churn Class Distribution: Churned={churn_counts.get(1, 0)} ({churn_rate:.2%}), Retained={churn_counts.get(0, 0)}")
    return manifest


if __name__ == "__main__":
    generate_cohort()
