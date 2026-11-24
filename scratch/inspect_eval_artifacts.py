import os
import json
import pandas as pd

# Check modeling dataset
if os.path.exists('data/modeling/modeling_dataset.csv'):
    df_mod = pd.read_csv('data/modeling/modeling_dataset.csv', nrows=2)
    print("modeling_dataset columns:", len(df_mod.columns), df_mod.columns[:15].tolist())

# Check independent test
for root, dirs, files in os.walk('data/independent_test'):
    for f in files:
        path = os.path.join(root, f)
        print(f"Independent test file: {path} ({os.path.getsize(path)} bytes)")

# Check reports for evaluation reports
for root, dirs, files in os.walk('reports'):
    for f in files:
        if 'eval' in f.lower() or 'metric' in f.lower() or 'phase5' in f.lower() or 'phase6' in f.lower() or 'audit' in f.lower():
            path = os.path.join(root, f)
            print(f"Report file: {path}")
