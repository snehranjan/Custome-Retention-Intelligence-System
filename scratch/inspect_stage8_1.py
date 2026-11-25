import os
import sys
import hashlib
import tracemalloc

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend/ml"))
import advanced_feature_engineering
import joblib
import pandas as pd
import numpy as np

tracemalloc.start()

rf_path = "models/phase5_1/final_model/final_churn_rf_pipeline.joblib"
scaler_path = "models/segmentation_scaler.joblib"
kmeans_path = "models/kmeans_customer_segmentation.joblib"

with open(rf_path, "rb") as f:
    h = hashlib.sha256(f.read()).hexdigest().upper()

rf_size = os.path.getsize(rf_path) / (1024*1024)
scaler_size = os.path.getsize(scaler_path) / (1024*1024)
kmeans_size = os.path.getsize(kmeans_path) / (1024*1024)

print(f"RF Model Path: {rf_path} ({rf_size:.2f} MB), SHA-256: {h}")
print(f"Scaler Path: {scaler_path} ({scaler_size:.2f} MB)")
print(f"KMeans Path: {kmeans_path} ({kmeans_size:.2f} MB)")

# Load models and measure memory
mem_before = tracemalloc.get_traced_memory()[0] / (1024*1024)
pipe = joblib.load(rf_path)
scaler = joblib.load(scaler_path)
kmeans = joblib.load(kmeans_path)
mem_after_load = tracemalloc.get_traced_memory()[0] / (1024*1024)
print(f"Memory traced before load: {mem_before:.2f} MB, after model load: {mem_after_load:.2f} MB (Delta: {mem_after_load - mem_before:.2f} MB)")

# Inspect clf
clf = pipe.named_steps.get("classifier", pipe[-1])
print(f"Classifier class: {type(clf).__name__}")
print(f"n_estimators: {getattr(clf, 'n_estimators', None)}")
print(f"max_depth: {getattr(clf, 'max_depth', None)}")
print(f"min_samples_leaf: {getattr(clf, 'min_samples_leaf', None)}")

# Perform inference on independent features dataset
features_df = pd.read_csv("data/independent_test/processed/independent_features.csv")
from backend.app.services.churn_service import ChurnPredictionService
X_sample = features_df[ChurnPredictionService.CONFIG_D_FEATURES]
probs = pipe.predict_proba(X_sample)[:, 1]
mem_after_infer = tracemalloc.get_traced_memory()[0] / (1024*1024)
peak_mem = tracemalloc.get_traced_memory()[1] / (1024*1024)
print(f"Inference on {len(X_sample)} rows completed. Memory after infer: {mem_after_infer:.2f} MB, Peak traced: {peak_mem:.2f} MB")
print(f"Sample prediction probs (min/mean/max): {probs.min():.4f} / {probs.mean():.4f} / {probs.max():.4f}")

# Check total size of git tracked files vs backend files
import subprocess
tracked = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
backend_tracked = [f for f in tracked if f.startswith(("backend", "models", "data", "requirements.txt"))]
backend_size = sum(os.path.getsize(f) for f in backend_tracked if os.path.exists(f)) / (1024*1024)
print(f"Total backend + models + data tracked in Git: {len(backend_tracked)} files, {backend_size:.2f} MB")

# Check Python version
print(f"Python version: {sys.version.split()[0]}")
