import pandas as pd
import time

t0 = time.time()
df = pd.read_csv('data/processed/customer_features.csv')
features_by_id = df.set_index('customer_id').to_dict(orient='index')
t1 = time.time()

print(f"Loaded {len(features_by_id)} customers in {t1 - t0:.3f}s")
sample_id = 'IND_CUST_10001'
print("Sample feature lookup keys count:", len(features_by_id[sample_id]))
print("Sample features:", {k: features_by_id[sample_id][k] for k in list(features_by_id[sample_id].keys())[:6]})
