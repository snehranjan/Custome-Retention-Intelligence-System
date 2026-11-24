import sqlite3
import json

conn = sqlite3.connect('data/local_database.db')
c = conn.cursor()

tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('TABLES:', tables)

for t in ['customers', 'customer_predictions', 'customer_segments', 'retention_recommendations']:
    if t in tables:
        cols = [col[1] for col in c.execute(f"PRAGMA table_info({t})").fetchall()]
        cnt = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"\nTABLE {t} (count: {cnt}):\n  Columns: {cols[:10]} ... ({len(cols)} total)")
        sample = c.execute(f"SELECT * FROM {t} LIMIT 1").fetchone()
        if sample:
            print("  Sample:", dict(zip(cols[:5], sample[:5])))

# Check customer churn counts
churn_stats = c.execute("SELECT churn, COUNT(*) FROM customers GROUP BY churn").fetchall()
print("\nOBSERVED CHURN STATS:", churn_stats)

# Check city/state counts
states = c.execute("SELECT COUNT(DISTINCT state), COUNT(DISTINCT city) FROM customers").fetchone()
print("UNIQUE STATES & CITIES:", states)

# Check customer_segments distribution
seg_stats = c.execute("SELECT cluster_id, segment_name, COUNT(*) FROM customer_segments WHERE is_current=1 GROUP BY cluster_id, segment_name").fetchall()
print("\nSEGMENT STATS IN DB:", seg_stats)

# Check predictions distribution
pred_stats = c.execute("SELECT risk_tier, predicted_churn, COUNT(*) FROM customer_predictions GROUP BY risk_tier, predicted_churn").fetchall()
print("\nPREDICTION STATS IN DB:", pred_stats)
