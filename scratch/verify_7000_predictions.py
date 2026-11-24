import os
import sys
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
from backend.app.services.model_loader import ModelLoader
from backend.app.services.churn_service import ChurnPredictionService
from backend.ml.advanced_feature_engineering import compute_advanced_features

ModelLoader.setup_python_path()
pipeline = ModelLoader.get_rf_pipeline()

CLUSTER_PERSONAS = {
    0: "Champions & High-Value Loyalists",
    1: "At-Risk / Lapsed Low-Value Customers",
    2: "Zero Delivered-Purchase Customers",
    3: "Steady Core Repeaters",
    4: "Recent Low-Ticket / New Promising Customers",
}

df_feat = pd.read_csv('data/processed/customer_features.csv')
df_seg = pd.read_csv('data/processed/customer_segments.csv')
df_seg['segment_name'] = df_seg['cluster_id'].map(CLUSTER_PERSONAS)
df_full = df_feat.merge(df_seg[['customer_id', 'cluster_id', 'segment_name']], on='customer_id')

# Compute advanced features
df_augmented = compute_advanced_features(df_full)

features_list = ChurnPredictionService.CONFIG_D_FEATURES
X = df_augmented[features_list]

probs = pipeline.predict_proba(X)[:, 1]
preds = (probs >= 0.50).astype(int)

print(f"\n7,000 Cohort Inference Results:")
print(f"Total customers: {len(df_augmented)}")
print(f"Observed Churned: {(df_augmented['churn'] == 1).sum()} ({(df_augmented['churn'] == 1).mean()*100:.2f}%)")
print(f"Observed Retained: {(df_augmented['churn'] == 0).sum()} ({(df_augmented['churn'] == 0).mean()*100:.2f}%)")
print(f"Predicted At-Risk (Class 1, prob >= 0.50): {int(preds.sum())} ({preds.mean()*100:.2f}%)")
print(f"Predicted Retained (Class 0, prob < 0.50): {int((preds == 0).sum())} ({(preds == 0).mean()*100:.2f}%)")

low = int((probs < 0.50).sum())
mod = int(((probs >= 0.50) & (probs < 0.70)).sum())
high = int((probs >= 0.70).sum())
print(f"Risk Tiers: Low (<0.50)={low} ({low/len(df_augmented)*100:.2f}%), Moderate (0.50-0.70)={mod} ({mod/len(df_augmented)*100:.2f}%), High (>=0.70)={high} ({high/len(df_augmented)*100:.2f}%)")

df_augmented['churn_prob'] = probs
df_augmented['predicted_churn'] = preds
df_augmented['risk_tier'] = ['LOW' if p < 0.50 else ('MODERATE' if p < 0.70 else 'HIGH') for p in probs]

seg_churn = df_augmented.groupby(['cluster_id', 'segment_name']).agg(
    total=('customer_id', 'count'),
    observed_churn=('churn', 'sum'),
    observed_churn_rate=('churn', 'mean'),
    predicted_churn=('predicted_churn', 'sum'),
    predicted_churn_rate=('predicted_churn', 'mean'),
    avg_churn_prob=('churn_prob', 'mean')
).reset_index()

print("\nSegment Churn Breakdown:")
for _, r in seg_churn.iterrows():
    print(f"Cluster {r['cluster_id']} ({r['segment_name']}): N={r['total']} ({r['total']/70:.2f}%), Obs Churn={r['observed_churn']} ({r['observed_churn_rate']*100:.2f}%), Pred Churn={r['predicted_churn']} ({r['predicted_churn_rate']*100:.2f}%)")
