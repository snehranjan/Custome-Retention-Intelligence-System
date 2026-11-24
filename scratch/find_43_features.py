import os
import pandas as pd

for root, dirs, files in os.walk('data'):
    for f in files:
        if f.endswith('.csv'):
            path = os.path.join(root, f)
            try:
                cols = pd.read_csv(path, nrows=1).columns.tolist()
                if 'velocity_ratio_30_90' in cols:
                    df = pd.read_csv(path)
                    print(f"MATCH: {path} has {len(cols)} columns, shape {df.shape}")
                    if 'customer_id' in cols:
                        print(f"  customer_id present, unique count: {df['customer_id'].nunique()}")
            except Exception as e:
                pass
