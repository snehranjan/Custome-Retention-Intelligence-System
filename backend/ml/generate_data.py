"""
Indian E-Commerce Customer Retention Intelligence System
Module: Synthetic Data Generator
Description: Generates reproducible synthetic e-commerce datasets for 7,000 fictional Indian customers
             and their order history, establishing a strict 90-day churn definition with zero data leakage.

Author: BCA (AI & ML) Project Team
Seed: 42
Snapshot Date: 2025-12-31
Label Evaluation Window: 2026-01-01 to 2026-03-31 (90 days)
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Set fixed random seeds for perfect reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Constants & Configuration
NUM_CUSTOMERS = 7000
SNAPSHOT_DATE = datetime(2025, 12, 31)
OBSERVATION_START_DATE = datetime(2023, 1, 1)
FUTURE_WINDOW_DAYS = 90
LABEL_END_DATE = SNAPSHOT_DATE + timedelta(days=FUTURE_WINDOW_DAYS)  # 2026-03-31

# Indian Demographics Context
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
PAYMENT_WEIGHTS = [0.46, 0.24, 0.14, 0.08, 0.05, 0.03]  # Authentic Indian digital commerce split


def generate_customers():
    """Generate 7,000 unique fictional Indian e-commerce customers."""
    print("Generating 7,000 unique customers...")
    customers = []
    
    total_days_range = (SNAPSHOT_DATE - OBSERVATION_START_DATE).days - 5
    
    for i in range(NUM_CUSTOMERS):
        cust_id = f"IND_CUST_{10001 + i}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        customer_name = f"{first_name} {last_name}"
        
        city, state = random.choice(INDIAN_CITIES_STATES)
        
        # Signup dates skewed slightly towards recent 1-2 years
        # Power distribution gives realistic customer cohort growth
        offset_days = int((np.random.power(1.6)) * total_days_range)
        signup_date = OBSERVATION_START_DATE + timedelta(days=offset_days)
        
        # Determine latent customer persona profile
        # Personas influence purchase velocity, order value, returns, and churn probability
        persona_roll = np.random.rand()
        if persona_roll < 0.15:
            # High-Value Loyal (Frequent, high spend, low churn)
            persona = "loyal_vip"
            base_order_freq = np.random.uniform(1.2, 2.8)  # orders per month
            churn_propensity = 0.08
        elif persona_roll < 0.40:
            # Steady Repeat Customer (Regular buyer, medium churn)
            persona = "steady"
            base_order_freq = np.random.uniform(0.6, 1.3)
            churn_propensity = 0.22
        elif persona_roll < 0.65:
            # Occasional / Discount Hunter (Low freq, sensitive to discounts, higher churn)
            persona = "occasional"
            base_order_freq = np.random.uniform(0.2, 0.6)
            churn_propensity = 0.45
        elif persona_roll < 0.85:
            # At-Risk / Dissatisfied (High delay, high returns, high churn)
            persona = "dissatisfied"
            base_order_freq = np.random.uniform(0.3, 0.8)
            churn_propensity = 0.68
        elif persona_roll < 0.98:
            # One-and-Done / Dormant (Placed 1 order long ago, very high churn)
            persona = "dormant"
            base_order_freq = 0.05
            churn_propensity = 0.88
        else:
            # Zero-order signup (Signed up but never purchased historically)
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


def generate_orders_and_churn(customers_df):
    """
    Generate historical orders up to 2025-12-31, calculate ground-truth churn labels
    based on future purchasing behavior (2026-01-01 to 2026-03-31), and return
    both datasets.
    """
    print("Generating order history and calculating churn labels...")
    orders = []
    order_id_counter = 100001
    
    churn_labels = []

    for _, cust in customers_df.iterrows():
        cust_id = cust["customer_id"]
        signup_dt = cust["signup_date"]
        persona = cust["persona"]
        churn_prob = cust["churn_propensity"]
        
        # Calculate historical tenure in days up to snapshot date
        historical_days = (SNAPSHOT_DATE - signup_dt).days
        
        # 1. Historical Orders Simulation (order_date <= 2025-12-31)
        if persona == "zero_order":
            hist_orders_count = 0
        elif persona == "dormant":
            hist_orders_count = 1
        else:
            # Expected order count based on tenure and frequency
            months = max(1, historical_days / 30.0)
            expected_orders = max(1, int(cust["base_order_freq"] * months))
            hist_orders_count = max(1, int(np.random.poisson(expected_orders)))
            # Cap extremely high counts for realism
            hist_orders_count = min(hist_orders_count, 65)

        # Generate timestamps for historical orders
        if hist_orders_count > 0:
            if persona == "dormant":
                # Single order placed soon after signup (dormant for a long time)
                order_offsets = [random.randint(1, min(15, historical_days))]
            else:
                # Distribute order timestamps realistically
                order_offsets = sorted(random.sample(range(0, historical_days + 1), k=hist_orders_count))
            
            for offset in order_offsets:
                ord_dt = signup_dt + timedelta(days=offset)
                category = random.choice(CATEGORIES)
                min_p, max_p = CATEGORY_PRICE_RANGES[category]
                
                # Base price log-normally distributed
                base_price = float(np.round(np.random.uniform(min_p, max_p), 2))
                
                # Delivery delay probability and magnitude based on persona
                if persona == "dissatisfied":
                    delay = int(np.random.choice([0, 2, 4, 6, 8, 11], p=[0.30, 0.20, 0.20, 0.15, 0.10, 0.05]))
                    is_return = np.random.choice([0, 1], p=[0.75, 0.25])
                    is_cancel = np.random.choice([0, 1], p=[0.85, 0.15])
                elif persona == "loyal_vip":
                    delay = int(np.random.choice([0, 1, 2, 4], p=[0.80, 0.12, 0.06, 0.02]))
                    is_return = np.random.choice([0, 1], p=[0.96, 0.04])
                    is_cancel = np.random.choice([0, 1], p=[0.98, 0.02])
                else:
                    delay = int(np.random.choice([0, 1, 2, 3, 5, 8], p=[0.68, 0.16, 0.08, 0.04, 0.03, 0.01]))
                    is_return = np.random.choice([0, 1], p=[0.92, 0.08])
                    is_cancel = np.random.choice([0, 1], p=[0.94, 0.06])

                # Status determination
                if is_cancel:
                    order_status = "Cancelled"
                    return_status = "Not Returned"
                elif is_return:
                    order_status = "Returned"
                    return_status = np.random.choice(["Returned", "Return Requested"], p=[0.85, 0.15])
                else:
                    order_status = "Delivered"
                    return_status = "Not Returned"

                # Payment method & Discount
                pay_method = np.random.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)
                # Discount amount (up to 25% on average)
                if np.random.rand() < 0.65:
                    discount = float(np.round(base_price * np.random.uniform(0.05, 0.25), 2))
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

        # 2. Ground-Truth Churn Determination (Next 90 Days: 2026-01-01 to 2026-03-31)
        # Latent churn probability with small stochastic variation
        final_churn_roll = np.random.rand()
        churn_decision = 1 if final_churn_roll < churn_prob else 0
        churn_labels.append(churn_decision)

        # 3. Future Orders Generation (Strictly within label window 2026-01-01 to 2026-03-31)
        # If churn == 0 (Retained/Active): customer places at least 1 future order!
        # If churn == 1 (Churned): customer places ZERO future orders!
        if churn_decision == 0:
            # Customer returned and placed orders in the next 90 days
            future_order_count = max(1, int(np.random.poisson(max(1.0, cust["base_order_freq"] * 3.0))))
            future_order_count = min(future_order_count, 12)  # Cap for 90 days
            
            future_offsets = sorted(random.sample(range(1, FUTURE_WINDOW_DAYS + 1), k=future_order_count))
            for offset in future_offsets:
                fut_dt = SNAPSHOT_DATE + timedelta(days=offset)
                category = random.choice(CATEGORIES)
                min_p, max_p = CATEGORY_PRICE_RANGES[category]
                base_price = float(np.round(np.random.uniform(min_p, max_p), 2))
                pay_method = np.random.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)
                discount = float(np.round(base_price * np.random.uniform(0.0, 0.20), 2)) if np.random.rand() < 0.6 else 0.0
                delay = int(np.random.choice([0, 1, 2, 4], p=[0.75, 0.15, 0.07, 0.03]))

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

    # Update customers dataframe with churn target
    customers_df["churn"] = churn_labels
    
    # Format signup_date as string
    customers_df["signup_date"] = customers_df["signup_date"].dt.strftime("%Y-%m-%d")
    
    # Drop internal simulation parameters to keep clean schema
    customers_clean = customers_df[[
        "customer_id", "customer_name", "signup_date", "city", "state", "snapshot_date", "churn"
    ]].copy()

    orders_df = pd.DataFrame(orders)
    return customers_clean, orders_df


def inject_mild_raw_imperfections(customers_df, orders_df):
    """
    Introduce mild, documented data-quality imperfections into non-critical business columns
    for exploratory data analysis (EDA) practice.
    CRITICAL RULE: Never corrupt IDs, dates required for temporal split, or churn labels.
    """
    print("Introducing controlled raw data imperfections for EDA practice...")
    
    # 1. Missing values in orders.csv:
    # - ~2.0% in delivery_delay_days
    # - ~1.8% in discount_amount_inr
    # - ~1.2% in payment_method
    mask_delay = np.random.rand(len(orders_df)) < 0.020
    orders_df.loc[mask_delay, "delivery_delay_days"] = np.nan

    mask_discount = np.random.rand(len(orders_df)) < 0.018
    orders_df.loc[mask_discount, "discount_amount_inr"] = np.nan

    mask_payment = np.random.rand(len(orders_df)) < 0.012
    orders_df.loc[mask_payment, "payment_method"] = np.nan

    # 2. Missing values in customers.csv:
    # - ~0.6% missing city/state (e.g. unverified registration)
    mask_cust_loc = np.random.rand(len(customers_df)) < 0.006
    customers_df.loc[mask_cust_loc, "city"] = np.nan
    customers_df.loc[mask_cust_loc, "state"] = np.nan

    return customers_df, orders_df


def main():
    print("=" * 70)
    print("PHASE 1: SYNTHETIC DATASET GENERATION")
    print(f"Snapshot Date: {SNAPSHOT_DATE.strftime('%Y-%m-%d')}")
    print(f"Label Evaluation Window: 2026-01-01 to {LABEL_END_DATE.strftime('%Y-%m-%d')} (90 days)")
    print("=" * 70)

    # 1. Generate core customers
    raw_cust_df = generate_customers()

    # 2. Generate order transactions and compute churn target
    customers_df, orders_df = generate_orders_and_churn(raw_cust_df)

    # 3. Inject realistic imperfections for EDA practice
    customers_df, orders_df = inject_mild_raw_imperfections(customers_df, orders_df)

    # 4. Save datasets
    os.makedirs("data/raw", exist_ok=True)
    cust_path = os.path.join("data", "raw", "customers.csv")
    ord_path = os.path.join("data", "raw", "orders.csv")

    customers_df.to_csv(cust_path, index=False)
    orders_df.to_csv(ord_path, index=False)

    print("\nDataset files successfully created:")
    print(f"  - Customers: {cust_path} ({len(customers_df):,} rows)")
    print(f"  - Orders:    {ord_path} ({len(orders_df):,} rows)")

    # 5. Summary statistics
    churn_counts = customers_df["churn"].value_counts()
    churn_rate = customers_df["churn"].mean() * 100
    print("\nTarget Label Distribution:")
    print(f"  - Retained (churn = 0): {churn_counts.get(0, 0):,} ({100 - churn_rate:.2f}%)")
    print(f"  - Churned  (churn = 1): {churn_counts.get(1, 0):,} ({churn_rate:.2f}%)")

    # Historical vs Future Orders split
    hist_mask = orders_df["order_date"] <= "2025-12-31"
    fut_mask = orders_df["order_date"] > "2025-12-31"
    print("\nOrders Split:")
    print(f"  - Historical Orders (<= 2025-12-31): {hist_mask.sum():,} records")
    print(f"  - Future Validation Orders (> 2025-12-31): {fut_mask.sum():,} records")

    print("\nMissing Values Summary:")
    print("  Customers:")
    for col in customers_df.columns:
        null_count = customers_df[col].isnull().sum()
        if null_count > 0:
            print(f"    - {col}: {null_count} ({null_count / len(customers_df) * 100:.2f}%)")
    print("  Orders:")
    for col in orders_df.columns:
        null_count = orders_df[col].isnull().sum()
        if null_count > 0:
            print(f"    - {col}: {null_count} ({null_count / len(orders_df) * 100:.2f}%)")

    print("=" * 70)
    print("Data generation complete and ready for rigorous validation!")
    print("=" * 70)


if __name__ == "__main__":
    main()
