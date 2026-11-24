import sqlite3

conn = sqlite3.connect('data/local_database.db')
c = conn.cursor()

query = """
SELECT 
    c.customer_id,
    c.customer_name,
    c.signup_date,
    c.city,
    c.state,
    c.churn,
    p.churn_probability,
    p.predicted_churn,
    p.risk_tier,
    s.cluster_id,
    s.segment_name,
    s.recency_delivered_days,
    s.hist_delivered_order_count,
    s.hist_delivered_order_value_inr
FROM customers c
LEFT JOIN customer_predictions p ON c.customer_id = p.customer_id
LEFT JOIN customer_segments s ON c.customer_id = s.customer_id AND s.is_current = 1
WHERE p.risk_tier = 'HIGH' AND s.cluster_id = 1
ORDER BY p.churn_probability DESC
LIMIT 5 OFFSET 0
"""
rows = c.execute(query).fetchall()
print("Sample Query Results (HIGH risk in Cluster 1):")
for r in rows:
    print(r)

count_q = """
SELECT COUNT(*)
FROM customers c
LEFT JOIN customer_predictions p ON c.customer_id = p.customer_id
LEFT JOIN customer_segments s ON c.customer_id = s.customer_id AND s.is_current = 1
WHERE p.risk_tier = 'HIGH' AND s.cluster_id = 1
"""
total = c.execute(count_q).fetchone()[0]
print("Total matching:", total)
conn.close()
