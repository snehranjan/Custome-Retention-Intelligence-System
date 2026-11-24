import os
import json
import pandas as pd

print("data/predictions:", os.listdir('data/predictions') if os.path.exists('data/predictions') else None)
print("data/independent_test:", os.listdir('data/independent_test') if os.path.exists('data/independent_test') else None)
print("data/modeling:", os.listdir('data/modeling') if os.path.exists('data/modeling') else None)

# Inspect customer_features.csv
if os.path.exists('data/processed/customer_features.csv'):
    df_feat = pd.read_csv('data/processed/customer_features.csv', nrows=2)
    print(f"\ncustomer_features.csv shape: {pd.read_csv('data/processed/customer_features.csv').shape}")
    print("customer_features columns (first 10):", df_feat.columns[:10].tolist())

# Inspect customer_segments.csv
if os.path.exists('data/processed/customer_segments.csv'):
    df_seg = pd.read_csv('data/processed/customer_segments.csv')
    print(f"\ncustomer_segments.csv shape: {df_seg.shape}")
    print("customer_segments value counts:")
    print(df_seg['cluster_id'].value_counts().sort_index())
    if 'segment_name' in df_seg.columns:
        print(df_seg.groupby(['cluster_id', 'segment_name']).size())

# Inspect predictions if available
if os.path.exists('data/predictions'):
    for f in os.listdir('data/predictions'):
        print(f"\nPrediction file: {f}")
        df_p = pd.read_csv(f'data/predictions/{f}')
        print(f"  Shape: {df_p.shape}, Columns: {df_p.columns.tolist()[:8]}")
        if 'risk_tier' in df_p.columns:
            print("  Risk tiers:\n", df_p['risk_tier'].value_counts())
        if 'predicted_churn' in df_p.columns:
            print("  Predicted churn:\n", df_p['predicted_churn'].value_counts())

# Inspect independent test metrics if available
if os.path.exists('data/independent_test'):
    for f in os.listdir('data/independent_test'):
        print(f"\nIndependent test file: {f}")
