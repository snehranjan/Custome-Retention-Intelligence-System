import sqlite3
import json

conn = sqlite3.connect('data/local_database.db')
c = conn.cursor()

# Test state breakdown
c.execute("""
    SELECT state, COUNT(*) as total, SUM(churn) as churned,
            ROUND(AVG(churn) * 100, 2) as churn_rate
    FROM customers
    GROUP BY state
    ORDER BY total DESC
""")
states = c.fetchall()
print(f"States count: {len(states)}, Top 3: {states[:3]}")

# Test city breakdown
c.execute("""
    SELECT city, COUNT(*) as total, SUM(churn) as churned,
            ROUND(AVG(churn) * 100, 2) as churn_rate
    FROM customers
    GROUP BY city
    ORDER BY total DESC
""")
cities = c.fetchall()
print(f"Cities count: {len(cities)}, Top 3: {cities[:3]}")

# Test segment breakdown
c.execute("""
    SELECT 
        s.cluster_id,
        s.segment_name,
        COUNT(c.customer_id) as total,
        SUM(c.churn) as obs_churn,
        ROUND(AVG(c.churn) * 100, 2) as obs_churn_rate,
        SUM(p.predicted_churn) as pred_churn,
        ROUND(AVG(p.predicted_churn) * 100, 2) as pred_churn_rate,
        ROUND(AVG(s.hist_delivered_order_value_inr), 2) as avg_spend,
        ROUND(AVG(s.recency_delivered_days), 1) as avg_recency,
        ROUND(AVG(s.hist_delivered_order_count), 1) as avg_orders
    FROM customer_segments s
    JOIN customers c ON s.customer_id = c.customer_id
    LEFT JOIN customer_predictions p ON s.customer_id = p.customer_id
    WHERE s.is_current = 1
    GROUP BY s.cluster_id, s.segment_name
    ORDER BY s.cluster_id ASC
""")
segs = c.fetchall()
print(f"Segments count: {len(segs)}")
for s in segs:
    print(" ", s[:7])

conn.close()
