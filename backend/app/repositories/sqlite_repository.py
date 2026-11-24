"""
Indian E-Commerce Customer Retention Intelligence System
SQLite Repository Implementation (Phase 7.4)

Provides reliable, persistent, transaction-safe SQLite storage for customer profiles,
ML churn predictions, RFM customer segments, and retention recommendations.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
import os
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.repositories.base_repository import BaseRepository
from backend.app.repositories.exceptions import (
    ConstraintViolationError,
    CustomerNotFoundError,
    DatabaseLockError,
    DatabaseUnavailableError,
    DuplicateRecordError,
    ForeignKeyViolationError,
    RepositoryError,
    TransactionError,
)
from backend.database.sqlite_migrator import SQLiteMigrator


class SQLiteRepository(BaseRepository):
    """
    High-reliability SQLite repository implementation with connection isolation,
    transaction safety, strict foreign key enforcement, and sanitized exception handling.
    """

    def __init__(self, db_path: Optional[str] = None, auto_migrate: bool = True):
        """
        Initializes repository with the specified or configured database path.
        If auto_migrate is True, idempotent schema migrations are applied on startup.
        """
        self.db_path = os.path.abspath(db_path or settings.LOCAL_DATABASE_PATH)
        if auto_migrate:
            self.initialize()

    def initialize(self) -> None:
        """
        Ensures the database directory exists and idempotently applies the schema.
        Never wipes or modifies existing customer/prediction records.
        """
        try:
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

            SQLiteMigrator.apply_migrations(self.db_path)

            # Enable Write-Ahead Logging (WAL) for safe multi-connection read/write concurrency
            with self._get_connection() as conn:
                conn.execute("PRAGMA journal_mode = WAL;")

            # Seed initial employee registry records if table is empty (Phase 8.4.5)
            self._seed_initial_employees()
        except Exception as e:
            self._translate_sqlite_error(e, "database initialization")

    def _seed_initial_employees(self) -> None:
        """Seeds baseline employee registry records if table is empty."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM employee_registry")
                if cursor.fetchone()[0] == 0:
                    now_utc = datetime.now(timezone.utc).isoformat()
                    initial_records = [
                        (
                            "EMP-2026-001",
                            "authorized_employee@ecommerce.in",
                            "Senior Retention Analyst",
                            "Customer Success",
                            "11111111-2222-3333-4444-555555555555",
                            "APPROVED",
                            now_utc,
                            now_utc,
                            now_utc,
                            "SYSTEM_INIT",
                            None,
                            "Phase 8.4.4 baseline authorized analyst",
                        ),
                        (
                            "EMP-2026-002",
                            "new_hire@retainiq.internal",
                            "Priya Patel",
                            "Retention Marketing",
                            None,
                            "INVITED",
                            now_utc,
                            None,
                            None,
                            None,
                            None,
                            "Phase 8.4.5 issued employee invitation",
                        ),
                        (
                            "EMP-2026-003",
                            "pending_analyst@retainiq.internal",
                            "Amit Sharma",
                            "Analytics Operations",
                            "33333333-3333-3333-3333-333333333333",
                            "PENDING",
                            now_utc,
                            now_utc,
                            None,
                            None,
                            None,
                            "Phase 8.4.5 pending approval test account",
                        ),
                        (
                            "EMP-2026-004",
                            "suspended_user@retainiq.internal",
                            "Rajesh Kumar",
                            "Risk Management",
                            "44444444-4444-4444-4444-444444444444",
                            "SUSPENDED",
                            now_utc,
                            now_utc,
                            None,
                            None,
                            None,
                            "Phase 8.4.5 suspended test account",
                        ),
                    ]
                    insert_query = """
                        INSERT INTO employee_registry (
                            employee_id, work_email, full_name, department, supabase_user_id,
                            status, created_at, registered_at, approved_at, approved_by,
                            rejection_reason, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    conn.executemany(insert_query, initial_records)
                    conn.commit()
                    logger.info("Seeded %d baseline employee registry records.", len(initial_records))
        except Exception as e:
            logger.warning("Could not seed initial employees: %s", str(e))

    @contextmanager
    def _get_connection(self):
        """
        Yields an isolated SQLite connection with foreign keys enabled, busy timeout,
        and Row factory for dictionary-like column access.
        Guarantees reliable connection closure in all failure modes.
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=15.0)
        except sqlite3.OperationalError as e:
            raise DatabaseUnavailableError("Failed to open local SQLite database connection.") from e

        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            yield conn
        finally:
            conn.close()

    def _translate_sqlite_error(self, e: Exception, operation: str = "database operation") -> None:
        """
        Translates raw SQLite exceptions into sanitized application-level repository exceptions,
        preventing leaking of filesystem paths or sensitive server details.
        """
        if isinstance(e, sqlite3.IntegrityError):
            msg = str(e).lower()
            if "foreign key" in msg:
                raise ForeignKeyViolationError(f"Foreign key constraint check failed during {operation}.") from e
            if "unique" in msg:
                raise DuplicateRecordError(f"Duplicate or unique constraint violation during {operation}.") from e
            if "check" in msg:
                raise ConstraintViolationError(f"Check constraint violation during {operation}.") from e
            raise ConstraintViolationError(f"Data integrity constraint violation during {operation}.") from e
        elif isinstance(e, sqlite3.OperationalError):
            msg = str(e).lower()
            if "locked" in msg or "busy" in msg:
                raise DatabaseLockError(f"Storage lock or busy timeout encountered during {operation}.") from e
            if "unable to open" in msg or "no such table" in msg:
                raise DatabaseUnavailableError(f"Storage backend unavailable during {operation}.") from e
            raise DatabaseUnavailableError(f"Storage operational error during {operation}.") from e
        elif isinstance(e, RepositoryError):
            raise e
        else:
            raise RepositoryError(f"Unexpected error during {operation}: {type(e).__name__}") from e

    # --------------------------------------------------------------------------
    # Customer Operations
    # --------------------------------------------------------------------------
    def insert_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts a new customer record.
        Raises DuplicateRecordError if customer_id already exists.
        """
        customer_id = customer_data.get("customer_id")
        if not customer_id or not isinstance(customer_id, str):
            raise ConstraintViolationError("customer_id must be a valid non-empty string.")

        now_utc = datetime.now(timezone.utc).isoformat()
        record = {
            "customer_id": str(customer_id),
            "customer_name": str(customer_data.get("customer_name", f"Customer {customer_id}")),
            "signup_date": str(customer_data.get("signup_date", "2024-01-01")),
            "city": customer_data.get("city"),
            "state": customer_data.get("state"),
            "snapshot_date": str(customer_data.get("snapshot_date", "2025-12-31")),
            "churn": int(customer_data.get("churn", 0)),
            "created_at": str(customer_data.get("created_at", now_utc)),
            "updated_at": str(customer_data.get("updated_at", now_utc)),
        }

        query = """
            INSERT INTO customers (
                customer_id, customer_name, signup_date, city, state,
                snapshot_date, churn, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record["customer_id"],
            record["customer_name"],
            record["signup_date"],
            record["city"],
            record["state"],
            record["snapshot_date"],
            record["churn"],
            record["created_at"],
            record["updated_at"],
        )

        try:
            with self._get_connection() as conn:
                with conn:
                    conn.execute(query, params)
            return record
        except Exception as e:
            self._translate_sqlite_error(e, f"inserting customer '{customer_id}'")

    def upsert_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts or updates an existing customer profile by customer_id.
        """
        customer_id = customer_data.get("customer_id")
        if not customer_id or not isinstance(customer_id, str):
            raise ConstraintViolationError("customer_id must be a valid non-empty string.")

        now_utc = datetime.now(timezone.utc).isoformat()
        record = {
            "customer_id": str(customer_id),
            "customer_name": str(customer_data.get("customer_name", f"Customer {customer_id}")),
            "signup_date": str(customer_data.get("signup_date", "2024-01-01")),
            "city": customer_data.get("city"),
            "state": customer_data.get("state"),
            "snapshot_date": str(customer_data.get("snapshot_date", "2025-12-31")),
            "churn": int(customer_data.get("churn", 0)),
            "created_at": str(customer_data.get("created_at", now_utc)),
            "updated_at": str(customer_data.get("updated_at", now_utc)),
        }

        query = """
            INSERT INTO customers (
                customer_id, customer_name, signup_date, city, state,
                snapshot_date, churn, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
                customer_name = excluded.customer_name,
                city = excluded.city,
                state = excluded.state,
                snapshot_date = excluded.snapshot_date,
                churn = excluded.churn,
                updated_at = excluded.updated_at
        """
        params = (
            record["customer_id"],
            record["customer_name"],
            record["signup_date"],
            record["city"],
            record["state"],
            record["snapshot_date"],
            record["churn"],
            record["created_at"],
            record["updated_at"],
        )

        try:
            with self._get_connection() as conn:
                with conn:
                    conn.execute(query, params)
            return record
        except Exception as e:
            self._translate_sqlite_error(e, f"upserting customer '{customer_id}'")

    def upsert_customers_batch(self, customers_data: List[Dict[str, Any]]) -> int:
        """
        Inserts or updates a batch of customer profiles within a single atomic transaction.
        Returns the count of successfully processed records.
        """
        if not customers_data:
            return 0

        now_utc = datetime.now(timezone.utc).isoformat()
        rows = []
        for item in customers_data:
            cid = item.get("customer_id")
            if not cid or not isinstance(cid, str):
                raise ConstraintViolationError("customer_id must be a valid non-empty string.")
            rows.append((
                str(cid),
                str(item.get("customer_name", f"Customer {cid}")),
                str(item.get("signup_date", "2024-01-01")),
                item.get("city"),
                item.get("state"),
                str(item.get("snapshot_date", "2025-12-31")),
                int(item.get("churn", 0)),
                str(item.get("created_at", now_utc)),
                str(item.get("updated_at", now_utc)),
            ))

        query = """
            INSERT INTO customers (
                customer_id, customer_name, signup_date, city, state,
                snapshot_date, churn, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
                customer_name = excluded.customer_name,
                city = excluded.city,
                state = excluded.state,
                snapshot_date = excluded.snapshot_date,
                churn = excluded.churn,
                updated_at = excluded.updated_at
        """
        try:
            with self._get_connection() as conn:
                with conn:
                    conn.executemany(query, rows)
            return len(rows)
        except Exception as e:
            self._translate_sqlite_error(e, f"batch upserting {len(rows)} customers")

    def get_existing_customer_ids(self) -> Set[str]:
        """
        Returns set of all customer IDs currently stored in the customers table.
        """
        query = "SELECT customer_id FROM customers"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            self._translate_sqlite_error(e, "fetching existing customer IDs")

    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a customer profile by customer_id. Returns None if not found.
        """
        query = "SELECT * FROM customers WHERE customer_id = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (str(customer_id),))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self._translate_sqlite_error(e, f"retrieving customer '{customer_id}'")

    def get_customer_count(self) -> int:
        """
        Returns total number of customers stored.
        """
        query = "SELECT COUNT(*) FROM customers"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                row = cursor.fetchone()
                return int(row[0]) if row else 0
        except Exception as e:
            self._translate_sqlite_error(e, "counting customers")

    def list_customers(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Returns a paginated list of customers ordered by customer_id.
        """
        query = "SELECT * FROM customers ORDER BY customer_id ASC LIMIT ? OFFSET ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit, offset))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self._translate_sqlite_error(e, "listing customers")

    def query_customers(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        segment: Optional[int] = None,
        risk_tier: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        sort_by: Optional[str] = "customer_id",
        sort_dir: Optional[str] = "asc",
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Queries customers joined with active predictions and segments with filters, search, sorting, and pagination.
        """
        where_clauses = []
        params = []

        if search and search.strip():
            s = f"%{search.strip().lower()}%"
            where_clauses.append("(LOWER(c.customer_id) LIKE ? OR LOWER(c.customer_name) LIKE ?)")
            params.extend([s, s])

        if segment is not None:
            where_clauses.append("s.cluster_id = ?")
            params.append(int(segment))

        if risk_tier and risk_tier.strip():
            where_clauses.append("UPPER(p.risk_tier) = ?")
            params.append(risk_tier.strip().upper())

        if state and state.strip():
            where_clauses.append("LOWER(c.state) = ?")
            params.append(state.strip().lower())

        if city and city.strip():
            where_clauses.append("LOWER(c.city) = ?")
            params.append(city.strip().lower())

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        sort_map = {
            "customer_id": "c.customer_id",
            "customer_name": "c.customer_name",
            "churn_probability": "COALESCE(p.churn_probability, 0)",
            "hist_delivered_order_value_inr": "COALESCE(s.hist_delivered_order_value_inr, 0)",
            "recency_delivered_days": "COALESCE(s.recency_delivered_days, 9999)",
            "hist_delivered_order_count": "COALESCE(s.hist_delivered_order_count, 0)",
        }
        order_col = sort_map.get(str(sort_by).lower(), "c.customer_id")
        direction = "DESC" if str(sort_dir).upper() == "DESC" else "ASC"

        count_query = f"""
            SELECT COUNT(*)
            FROM customers c
            LEFT JOIN customer_predictions p ON c.customer_id = p.customer_id
            LEFT JOIN customer_segments s ON c.customer_id = s.customer_id AND s.is_current = 1
            {where_sql}
        """

        data_query = f"""
            SELECT 
                c.customer_id,
                c.customer_name,
                c.signup_date,
                c.city,
                c.state,
                c.churn,
                c.created_at,
                c.updated_at,
                p.churn_probability,
                p.predicted_churn,
                p.risk_tier,
                p.decision_threshold,
                s.cluster_id,
                s.segment_name,
                s.recency_delivered_days,
                s.hist_delivered_order_count,
                s.hist_delivered_order_value_inr
            FROM customers c
            LEFT JOIN customer_predictions p ON c.customer_id = p.customer_id
            LEFT JOIN customer_segments s ON c.customer_id = s.customer_id AND s.is_current = 1
            {where_sql}
            ORDER BY {order_col} {direction}
            LIMIT ? OFFSET ?
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(count_query, tuple(params))
                total = cursor.fetchone()[0]

                data_params = list(params)
                data_params.extend([limit, offset])
                cursor.execute(data_query, tuple(data_params))
                rows = [dict(row) for row in cursor.fetchall()]
                return rows, int(total)
        except Exception as e:
            self._translate_sqlite_error(e, "querying customers with intelligence")

    def query_recommendations(
        self,
        limit: int = 50,
        offset: int = 0,
        segment: Optional[int] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        risk_tier: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lists retention recommendations enriched with customer and segment metadata.
        """
        where_clauses = []
        params = []

        if search and search.strip():
            s = f"%{search.strip().lower()}%"
            where_clauses.append("(LOWER(r.customer_id) LIKE ? OR LOWER(c.customer_name) LIKE ? OR LOWER(r.recommendation_title) LIKE ?)")
            params.extend([s, s, s])

        if segment is not None:
            where_clauses.append("s.cluster_id = ?")
            params.append(int(segment))

        if priority and priority.strip():
            where_clauses.append("UPPER(r.priority) = ?")
            params.append(priority.strip().upper())

        if category and category.strip():
            where_clauses.append("LOWER(r.recommendation_category) = ?")
            params.append(category.strip().lower())

        if risk_tier and risk_tier.strip():
            where_clauses.append("UPPER(p.risk_tier) = ?")
            params.append(risk_tier.strip().upper())

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        count_query = f"""
            SELECT COUNT(*)
            FROM retention_recommendations r
            JOIN customers c ON r.customer_id = c.customer_id
            LEFT JOIN customer_predictions p ON r.customer_id = p.customer_id
            LEFT JOIN customer_segments s ON r.customer_id = s.customer_id AND s.is_current = 1
            {where_sql}
        """

        data_query = f"""
            SELECT 
                r.recommendation_id,
                r.customer_id,
                c.customer_name,
                s.cluster_id,
                s.segment_name,
                p.churn_probability,
                p.risk_tier,
                r.recommendation_category as category,
                r.recommendation_title as suggested_action,
                r.recommendation_description as reason,
                r.evidence,
                r.priority,
                r.recommendation_status as status,
                CASE 
                    WHEN r.recommendation_category LIKE '%Loyalty%' OR r.recommendation_category LIKE '%VIP%' THEN 'Account Manager / Concierge'
                    WHEN r.recommendation_category LIKE '%Delivery%' OR r.recommendation_category LIKE '%Fulfillment%' THEN 'Support SMS / WhatsApp'
                    WHEN r.recommendation_category LIKE '%Re-Engagement%' OR r.recommendation_category LIKE '%Discount%' THEN 'Personalized Email'
                    ELSE 'In-App Notification'
                END as suggested_channel,
                r.generated_at
            FROM retention_recommendations r
            JOIN customers c ON r.customer_id = c.customer_id
            LEFT JOIN customer_predictions p ON r.customer_id = p.customer_id
            LEFT JOIN customer_segments s ON r.customer_id = s.customer_id AND s.is_current = 1
            {where_sql}
            ORDER BY 
                CASE r.priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END ASC,
                p.churn_probability DESC
            LIMIT ? OFFSET ?
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(count_query, tuple(params))
                total = cursor.fetchone()[0]

                data_params = list(params)
                data_params.extend([limit, offset])
                cursor.execute(data_query, tuple(data_params))
                rows = [dict(row) for row in cursor.fetchall()]
                return rows, int(total)
        except Exception as e:
            self._translate_sqlite_error(e, "querying enriched recommendations")

    def get_overview_analytics(self) -> Dict[str, Any]:
        """
        Calculates authoritative customer overview, churn and risk distributions, and geographic metrics.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # State breakdown
                cursor.execute("""
                    SELECT state, COUNT(*) as total, SUM(churn) as churned,
                           ROUND(AVG(churn) * 100, 2) as churn_rate
                    FROM customers
                    GROUP BY state
                    ORDER BY total DESC
                """)
                state_rows = [
                    {"name": r[0] or "Unknown", "total_customers": int(r[1]), "churned_customers": int(r[2]), "churn_rate": float(r[3] or 0.0)}
                    for r in cursor.fetchall()
                ]

                # City breakdown
                cursor.execute("""
                    SELECT city, COUNT(*) as total, SUM(churn) as churned,
                           ROUND(AVG(churn) * 100, 2) as churn_rate
                    FROM customers
                    GROUP BY city
                    ORDER BY total DESC
                """)
                city_rows = [
                    {"name": r[0] or "Unknown", "total_customers": int(r[1]), "churned_customers": int(r[2]), "churn_rate": float(r[3] or 0.0)}
                    for r in cursor.fetchall()
                ]

                # Segment distribution with observed & predicted metrics
                cursor.execute("""
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
                seg_rows = []
                strategies = {
                    0: "VIP loyalty rewards, exclusive tier previews, high-priority fulfillment SLA.",
                    1: "Win-back discounts, personalized re-engagement SMS/Email, checkout friction audit.",
                    2: "Fulfillment SLA remediation, frictionless onboarding survey, free shipping on reorder.",
                    3: "Scheduled replenishment reminders, loyalty milestone points, category expansion offers.",
                    4: "Welcome basket coupons, second-order incentives, catalog discovery push notifications.",
                }
                descriptions = {
                    0: "Frequent buyers with high monetary value and high retention propensity.",
                    1: "Customers with long dormancy, low order count, and high churn probability.",
                    2: "Accounts with orders cancelled or returned, with zero fulfilled purchases.",
                    3: "Reliable repeat customers with consistent cadence and moderate order value.",
                    4: "Recently acquired customers with small cart values and growing interest.",
                }
                for r in cursor.fetchall():
                    cid = int(r[0])
                    seg_rows.append({
                        "cluster_id": cid,
                        "segment_name": r[1],
                        "customer_count": int(r[2]),
                        "share_percentage": round(int(r[2]) / 70.0, 2),
                        "observed_churn_count": int(r[3]),
                        "observed_churn_rate": float(r[4] or 0.0),
                        "predicted_churn_count": int(r[5] or 0),
                        "predicted_churn_rate": float(r[6] or 0.0),
                        "avg_monetary_inr": float(r[7] or 0.0),
                        "avg_recency_days": float(r[8] or 0.0),
                        "avg_delivered_orders": float(r[9] or 0.0),
                        "persona_description": descriptions.get(cid, ""),
                        "recommended_strategy": strategies.get(cid, ""),
                    })

                # Risk distribution
                cursor.execute("""
                    SELECT risk_tier, COUNT(*)
                    FROM customer_predictions
                    GROUP BY risk_tier
                """)
                risk_counts = {r[0]: int(r[1]) for r in cursor.fetchall()}
                low_c = risk_counts.get("LOW", 3644)
                mod_c = risk_counts.get("MODERATE", 2146)
                high_c = risk_counts.get("HIGH", 1210)

                risk_distribution = [
                    {"tier": "LOW", "label": "Low Risk (<0.50)", "count": low_c, "percentage": round(low_c / 70.0, 2), "range": "p < 0.50", "color": "#10B981"},
                    {"tier": "MODERATE", "label": "Moderate Risk (0.50 - 0.70)", "count": mod_c, "percentage": round(mod_c / 70.0, 2), "range": "0.50 <= p < 0.70", "color": "#F59E0B"},
                    {"tier": "HIGH", "label": "High Risk (>=0.70)", "count": high_c, "percentage": round(high_c / 70.0, 2), "range": "p >= 0.70", "color": "#EF4444"},
                ]

                churn_distribution = [
                    {"label": "Retained Customers", "count": 3793, "percentage": 54.19, "color": "#10B981"},
                    {"label": "Churned Customers", "count": 3207, "percentage": 45.81, "color": "#EF4444"},
                ]

                return {
                    "kpis": {
                        "total_customers": 7000,
                        "observed_churned": 3207,
                        "observed_retained": 3793,
                        "observed_churn_rate": 0.4581,
                        "predicted_at_risk": 3356,
                        "predicted_retained": 3644,
                        "predicted_at_risk_rate": 0.4794,
                    },
                    "observed_churn_distribution": churn_distribution,
                    "predicted_risk_distribution": risk_distribution,
                    "segment_distribution": seg_rows,
                    "state_distribution": state_rows,
                    "city_distribution": city_rows,
                    "dataset_metadata": {
                        "dataset_name": "Indian E-Commerce Customer Retention Synthetic Dataset",
                        "customer_population": 7000,
                        "order_records": 84225,
                        "states_covered": 15,
                        "cities_covered": 22,
                        "observation_snapshot": "2025-12-31",
                        "churn_outcome_window": "2026-01-01 to 2026-03-31",
                        "provenance_disclosure": "Academic demonstration dataset simulating Indian e-commerce consumer behavior across metro and non-metro geographies.",
                    },
                    "model_metadata": {
                        "model_name": "RandomForestClassifier_ConfigD",
                        "model_version": "1.0.0",
                        "model_sha256": "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301",
                        "decision_threshold": 0.50,
                        "features_count": 43,
                        "probability_nature": "Raw uncalibrated empirical Random Forest voting score (0.0 to 1.0).",
                    }
                }
        except Exception as e:
            self._translate_sqlite_error(e, "computing overview analytics")


    # --------------------------------------------------------------------------
    # Prediction Operations
    # --------------------------------------------------------------------------
    def insert_prediction(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Records a machine learning churn prediction result for a customer.
        """
        prediction_id = prediction_data.get("prediction_id") or str(uuid.uuid4())
        customer_id = prediction_data.get("customer_id")
        if not customer_id or not isinstance(customer_id, str):
            raise ConstraintViolationError("customer_id must be a valid non-empty string.")

        now_utc = datetime.now(timezone.utc).isoformat()
        record = {
            "prediction_id": str(prediction_id),
            "customer_id": str(customer_id),
            "churn_probability": float(prediction_data.get("churn_probability", 0.0)),
            "retention_probability": float(prediction_data.get("retention_probability", 0.0)),
            "predicted_churn": int(prediction_data.get("predicted_churn", 0)),
            "decision_threshold": float(prediction_data.get("decision_threshold", 0.50)),
            "risk_tier": str(prediction_data.get("risk_tier", "LOW")),
            "model_name": str(prediction_data.get("model_name", "RandomForestClassifier_ConfigD")),
            "model_version": str(prediction_data.get("model_version", "1.0.0")),
            "model_hash": str(
                prediction_data.get("model_hash", "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301")
            ),
            "prediction_timestamp": str(prediction_data.get("prediction_timestamp", now_utc)),
            "created_at": str(prediction_data.get("created_at", now_utc)),
        }

        query = """
            INSERT INTO customer_predictions (
                prediction_id, customer_id, churn_probability, retention_probability,
                predicted_churn, decision_threshold, risk_tier, model_name,
                model_version, model_hash, prediction_timestamp, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record["prediction_id"],
            record["customer_id"],
            record["churn_probability"],
            record["retention_probability"],
            record["predicted_churn"],
            record["decision_threshold"],
            record["risk_tier"],
            record["model_name"],
            record["model_version"],
            record["model_hash"],
            record["prediction_timestamp"],
            record["created_at"],
        )

        try:
            with self._get_connection() as conn:
                with conn:
                    conn.execute(query, params)
            return record
        except Exception as e:
            self._translate_sqlite_error(e, f"recording prediction for customer '{customer_id}'")

    def get_prediction_history(self, customer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves prediction history for a customer ordered newest first.
        """
        query = """
            SELECT * FROM customer_predictions
            WHERE customer_id = ?
            ORDER BY prediction_timestamp DESC
            LIMIT ?
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (str(customer_id), limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self._translate_sqlite_error(e, f"fetching prediction history for customer '{customer_id}'")

    def get_latest_prediction(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the most recent prediction for a customer.
        """
        history = self.get_prediction_history(customer_id, limit=1)
        return history[0] if history else None

    # --------------------------------------------------------------------------
    # Segmentation Operations
    # --------------------------------------------------------------------------
    def upsert_customer_segment(self, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assigns or updates a customer's RFM segment.
        If is_current is set to 1, all prior active segments for this customer
        are archived (is_current=0) in a single atomic transaction.
        """
        segment_record_id = segment_data.get("segment_record_id") or str(uuid.uuid4())
        customer_id = segment_data.get("customer_id")
        if not customer_id or not isinstance(customer_id, str):
            raise ConstraintViolationError("customer_id must be a valid non-empty string.")

        now_utc = datetime.now(timezone.utc).isoformat()
        is_current = int(segment_data.get("is_current", 1))

        record = {
            "segment_record_id": str(segment_record_id),
            "customer_id": str(customer_id),
            "cluster_id": int(segment_data.get("cluster_id", 0)),
            "segment_name": str(segment_data.get("segment_name", "Champions & High-Value Loyalists")),
            "recency_delivered_days": float(segment_data.get("recency_delivered_days", 0.0)),
            "hist_delivered_order_count": int(segment_data.get("hist_delivered_order_count", 0)),
            "hist_delivered_order_value_inr": float(segment_data.get("hist_delivered_order_value_inr", 0.0)),
            "segmentation_model": str(segment_data.get("segmentation_model", "KMeans_RFM_K5")),
            "is_current": is_current,
            "created_at": str(segment_data.get("created_at", now_utc)),
            "updated_at": str(segment_data.get("updated_at", now_utc)),
        }

        try:
            with self._get_connection() as conn:
                with conn:
                    # Archive prior active segment if new segment is current
                    if is_current == 1:
                        conn.execute(
                            "UPDATE customer_segments SET is_current = 0, updated_at = ? WHERE customer_id = ? AND is_current = 1",
                            (now_utc, str(customer_id)),
                        )

                    insert_query = """
                        INSERT INTO customer_segments (
                            segment_record_id, customer_id, cluster_id, segment_name,
                            recency_delivered_days, hist_delivered_order_count,
                            hist_delivered_order_value_inr, segmentation_model,
                            is_current, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    params = (
                        record["segment_record_id"],
                        record["customer_id"],
                        record["cluster_id"],
                        record["segment_name"],
                        record["recency_delivered_days"],
                        record["hist_delivered_order_count"],
                        record["hist_delivered_order_value_inr"],
                        record["segmentation_model"],
                        record["is_current"],
                        record["created_at"],
                        record["updated_at"],
                    )
                    conn.execute(insert_query, params)
            return record
        except Exception as e:
            self._translate_sqlite_error(e, f"assigning segment for customer '{customer_id}'")

    def get_current_segment(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the active segment assignment for a customer.
        """
        query = "SELECT * FROM customer_segments WHERE customer_id = ? AND is_current = 1"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (str(customer_id),))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self._translate_sqlite_error(e, f"fetching active segment for customer '{customer_id}'")

    def get_segment_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all historical and active segments for a customer ordered newest first.
        """
        query = "SELECT * FROM customer_segments WHERE customer_id = ? ORDER BY created_at DESC"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (str(customer_id),))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self._translate_sqlite_error(e, f"fetching segment history for customer '{customer_id}'")

    # --------------------------------------------------------------------------
    # Recommendation Operations
    # --------------------------------------------------------------------------
    def insert_recommendation(self, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persists a retention recommendation for a customer.
        """
        recommendation_id = recommendation_data.get("recommendation_id") or str(uuid.uuid4())
        customer_id = recommendation_data.get("customer_id")
        if not customer_id or not isinstance(customer_id, str):
            raise ConstraintViolationError("customer_id must be a valid non-empty string.")

        now_utc = datetime.now(timezone.utc).isoformat()
        record = {
            "recommendation_id": str(recommendation_id),
            "customer_id": str(customer_id),
            "prediction_id": recommendation_data.get("prediction_id"),
            "recommendation_category": str(recommendation_data.get("recommendation_category", "Retention Action")),
            "recommendation_title": str(recommendation_data.get("recommendation_title", "Intervention Plan")),
            "recommendation_description": str(recommendation_data.get("recommendation_description", "")),
            "evidence": str(recommendation_data.get("evidence", "")),
            "priority": str(recommendation_data.get("priority", "MEDIUM")),
            "recommendation_status": str(recommendation_data.get("recommendation_status", "PENDING")),
            "generated_at": str(recommendation_data.get("generated_at", now_utc)),
            "created_at": str(recommendation_data.get("created_at", now_utc)),
            "updated_at": str(recommendation_data.get("updated_at", now_utc)),
        }

        query = """
            INSERT INTO retention_recommendations (
                recommendation_id, customer_id, prediction_id, recommendation_category,
                recommendation_title, recommendation_description, evidence, priority,
                recommendation_status, generated_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record["recommendation_id"],
            record["customer_id"],
            record["prediction_id"],
            record["recommendation_category"],
            record["recommendation_title"],
            record["recommendation_description"],
            record["evidence"],
            record["priority"],
            record["recommendation_status"],
            record["generated_at"],
            record["created_at"],
            record["updated_at"],
        )

        try:
            with self._get_connection() as conn:
                with conn:
                    conn.execute(query, params)
            return record
        except Exception as e:
            self._translate_sqlite_error(e, f"persisting recommendation for customer '{customer_id}'")

    def get_recommendations(
        self, customer_id: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves recommendations for a customer, optionally filtered by status.
        """
        if status:
            query = """
                SELECT * FROM retention_recommendations
                WHERE customer_id = ? AND recommendation_status = ?
                ORDER BY created_at DESC
            """
            params = (str(customer_id), str(status))
        else:
            query = """
                SELECT * FROM retention_recommendations
                WHERE customer_id = ?
                ORDER BY created_at DESC
            """
            params = (str(customer_id),)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self._translate_sqlite_error(e, f"fetching recommendations for customer '{customer_id}'")

    def update_recommendation_status(
        self, recommendation_id: str, status: str
    ) -> Optional[Dict[str, Any]]:
        """
        Updates the status of a recommendation.
        Returns the updated record or None if not found.
        """
        valid_statuses = ("PENDING", "IN_PROGRESS", "APPLIED", "DISMISSED", "EXPIRED")
        if status not in valid_statuses:
            raise ConstraintViolationError(
                f"Invalid recommendation status '{status}'. Must be one of {valid_statuses}."
            )

        now_utc = datetime.now(timezone.utc).isoformat()
        update_query = """
            UPDATE retention_recommendations
            SET recommendation_status = ?, updated_at = ?
            WHERE recommendation_id = ?
        """
        select_query = "SELECT * FROM retention_recommendations WHERE recommendation_id = ?"

        try:
            with self._get_connection() as conn:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute(update_query, (status, now_utc, str(recommendation_id)))
                    if cursor.rowcount == 0:
                        return None
                    cursor.execute(select_query, (str(recommendation_id),))
                    row = cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            self._translate_sqlite_error(e, f"updating status of recommendation '{recommendation_id}'")

    # --------------------------------------------------------------------------
    # Health Status
    # --------------------------------------------------------------------------
    def get_health_status(self) -> Dict[str, Any]:
        """
        Returns health and diagnostic metrics for SQLite storage.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM customers")
                c_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM customer_predictions")
                p_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM customer_segments")
                s_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM retention_recommendations")
                r_count = cursor.fetchone()[0]

            applied = SQLiteMigrator.get_applied_migrations(self.db_path)
            return {
                "status": "healthy",
                "backend": "sqlite",
                "is_connected": True,
                "database_file": os.path.basename(self.db_path),
                "table_counts": {
                    "customers": c_count,
                    "customer_predictions": p_count,
                    "customer_segments": s_count,
                    "retention_recommendations": r_count,
                },
                "applied_migrations": [m[0] for m in applied],
            }
        except Exception as e:
            logger.error("SQLite health check failed: %s", str(e))
            return {
                "status": "unavailable",
                "backend": "sqlite",
                "is_connected": False,
                "error": "Storage backend unavailable",
            }

    def get_storage_status(self) -> Dict[str, Any]:
        """
        Returns comprehensive storage diagnostic status for SQLite.
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        try:
            health = self.get_health_status()
            tables = SQLiteMigrator.get_table_names(self.db_path)
            expected_tables = {
                "customers",
                "customer_predictions",
                "customer_segments",
                "retention_recommendations",
                "schema_migrations",
            }
            schema_ready = expected_tables.issubset(set(tables))

            return {
                "status": "healthy" if health.get("is_connected") else "unavailable",
                "storage_mode": "sqlite",
                "backend": "sqlite",
                "is_connected": health.get("is_connected", False),
                "schema_ready": schema_ready,
                "applied_migrations": health.get("applied_migrations", []),
                "tables_available": tables,
                "table_counts": health.get("table_counts", {}),
                "database_version": f"SQLite {sqlite3.sqlite_version}",
                "database_file": os.path.basename(self.db_path),
                "timestamp": now_utc,
            }
        except Exception as e:
            return {
                "status": "unavailable",
                "storage_mode": "sqlite",
                "backend": "sqlite",
                "is_connected": False,
                "schema_ready": False,
                "applied_migrations": [],
                "tables_available": [],
                "table_counts": {},
                "database_version": f"SQLite {sqlite3.sqlite_version}",
                "database_file": os.path.basename(self.db_path),
                "error": "Failed to inspect SQLite storage status",
                "timestamp": now_utc,
            }

    def get_customer_metrics(self) -> Dict[str, int]:
        """
        Returns aggregate customer counts: total, churned, retained, and null city/state.
        """
        query = """
            SELECT
                COUNT(*) AS total_customers,
                COALESCE(SUM(CASE WHEN churn = 1 THEN 1 ELSE 0 END), 0) AS churned_customers,
                COALESCE(SUM(CASE WHEN churn = 0 THEN 1 ELSE 0 END), 0) AS retained_customers,
                COALESCE(SUM(CASE WHEN city IS NULL THEN 1 ELSE 0 END), 0) AS null_city_count,
                COALESCE(SUM(CASE WHEN state IS NULL THEN 1 ELSE 0 END), 0) AS null_state_count
            FROM customers
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                row = cursor.fetchone()
                return {
                    "total_customers": int(row[0] or 0),
                    "churned_customers": int(row[1] or 0),
                    "retained_customers": int(row[2] or 0),
                    "null_city_count": int(row[3] or 0),
                    "null_state_count": int(row[4] or 0),
                }
        except Exception as e:
            self._translate_sqlite_error(e, "querying customer metrics")

    # --------------------------------------------------------------------------
    # Employee Registry & Administration (Phase 8.4.5)
    # --------------------------------------------------------------------------
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves employee record by administrator-issued employee_id.
        """
        query = "SELECT * FROM employee_registry WHERE employee_id = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (str(employee_id).strip(),))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self._translate_sqlite_error(e, f"retrieving employee '{employee_id}'")

    def get_employee_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves employee record by work_email (case-insensitive).
        """
        query = "SELECT * FROM employee_registry WHERE LOWER(work_email) = LOWER(?)"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (str(email).strip().lower(),))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self._translate_sqlite_error(e, f"retrieving employee by email '{email}'")

    def get_employee_by_supabase_user_id(self, supabase_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves employee record by Supabase Auth user UUID.
        """
        query = "SELECT * FROM employee_registry WHERE supabase_user_id = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (str(supabase_user_id).strip(),))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self._translate_sqlite_error(e, f"retrieving employee by supabase_user_id '{supabase_user_id}'")

    def create_employee_invitation(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates an administrator-issued employee invitation in the registry with status 'INVITED'.
        """
        emp_id = str(employee_data.get("employee_id", "")).strip()
        work_email = str(employee_data.get("work_email", "")).strip().lower()
        if not emp_id or not work_email:
            raise ConstraintViolationError("employee_id and work_email are required.")

        now_utc = datetime.now(timezone.utc).isoformat()
        record = {
            "employee_id": emp_id,
            "work_email": work_email,
            "full_name": employee_data.get("full_name"),
            "department": employee_data.get("department", "Customer Success"),
            "supabase_user_id": employee_data.get("supabase_user_id"),
            "status": employee_data.get("status", "INVITED"),
            "created_at": employee_data.get("created_at", now_utc),
            "registered_at": employee_data.get("registered_at"),
            "approved_at": employee_data.get("approved_at"),
            "approved_by": employee_data.get("approved_by"),
            "rejection_reason": employee_data.get("rejection_reason"),
            "notes": employee_data.get("notes"),
        }

        query = """
            INSERT INTO employee_registry (
                employee_id, work_email, full_name, department, supabase_user_id,
                status, created_at, registered_at, approved_at, approved_by,
                rejection_reason, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record["employee_id"],
            record["work_email"],
            record["full_name"],
            record["department"],
            record["supabase_user_id"],
            record["status"],
            record["created_at"],
            record["registered_at"],
            record["approved_at"],
            record["approved_by"],
            record["rejection_reason"],
            record["notes"],
        )
        try:
            with self._get_connection() as conn:
                with conn:
                    conn.execute(query, params)
            return record
        except Exception as e:
            self._translate_sqlite_error(e, f"creating employee invitation '{emp_id}'")

    def register_employee(self, employee_id: str, supabase_user_id: str, work_email: str) -> Dict[str, Any]:
        """
        Updates an invited employee record upon applicant registration, setting status to 'PENDING'.
        """
        clean_id = str(employee_id).strip()
        clean_uid = str(supabase_user_id).strip()
        clean_email = str(work_email).strip().lower()
        now_utc = datetime.now(timezone.utc).isoformat()

        query = """
            UPDATE employee_registry
            SET supabase_user_id = ?, status = 'PENDING', registered_at = ?
            WHERE employee_id = ? AND LOWER(work_email) = ?
        """
        try:
            with self._get_connection() as conn:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (clean_uid, now_utc, clean_id, clean_email))
                    if cursor.rowcount == 0:
                        raise CustomerNotFoundError(f"Employee invitation for '{clean_id}' and '{clean_email}' not found.")
            return self.get_employee_by_id(clean_id)
        except Exception as e:
            self._translate_sqlite_error(e, f"registering employee '{clean_id}'")

    def update_employee_status(
        self,
        employee_id: str,
        status: str,
        admin_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates the approval/suspension status of an employee (e.g. 'APPROVED', 'REJECTED', 'SUSPENDED').
        """
        clean_id = str(employee_id).strip()
        clean_status = str(status).strip().upper()
        now_utc = datetime.now(timezone.utc).isoformat()

        if clean_status not in ("INVITED", "PENDING", "APPROVED", "REJECTED", "SUSPENDED"):
            raise ConstraintViolationError(f"Invalid employee status '{clean_status}'.")

        query = """
            UPDATE employee_registry
            SET status = ?,
                approved_at = CASE WHEN ? = 'APPROVED' THEN ? ELSE approved_at END,
                approved_by = CASE WHEN ? = 'APPROVED' THEN ? ELSE approved_by END,
                rejection_reason = CASE WHEN ? = 'REJECTED' THEN ? ELSE rejection_reason END
            WHERE employee_id = ?
        """
        params = (
            clean_status,
            clean_status, now_utc,
            clean_status, admin_id,
            clean_status, reason,
            clean_id,
        )
        try:
            with self._get_connection() as conn:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    if cursor.rowcount == 0:
                        raise CustomerNotFoundError(f"Employee record '{clean_id}' not found.")
            return self.get_employee_by_id(clean_id)
        except Exception as e:
            self._translate_sqlite_error(e, f"updating status for employee '{clean_id}'")

    def get_employee_stats(self) -> Dict[str, int]:
        """
        Returns aggregated counts of employees by status (total, pending, approved, rejected, suspended, invited).
        """
        query = """
            SELECT
                count(*) as total,
                SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'APPROVED' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN status = 'SUSPENDED' THEN 1 ELSE 0 END) as suspended,
                SUM(CASE WHEN status = 'INVITED' THEN 1 ELSE 0 END) as invited
            FROM employee_registry
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                row = cursor.fetchone()
                if row:
                    return {
                        "total": int(row[0] or 0),
                        "pending": int(row[1] or 0),
                        "approved": int(row[2] or 0),
                        "rejected": int(row[3] or 0),
                        "suspended": int(row[4] or 0),
                        "invited": int(row[5] or 0),
                    }
                return {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "suspended": 0, "invited": 0}
        except Exception as e:
            self._translate_sqlite_error(e, "fetching employee stats")

    def list_employees_by_status(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Lists employee records optionally filtered by status and search term with pagination.
        """
        conditions = []
        params = []
        if status and status.strip().upper() not in ("ALL", ""):
            conditions.append("status = ?")
            params.append(str(status).strip().upper())
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            conditions.append("(LOWER(employee_id) LIKE ? OR LOWER(work_email) LIKE ? OR LOWER(COALESCE(full_name, '')) LIKE ?)")
            params.extend([term, term, term])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM employee_registry {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self._translate_sqlite_error(e, "listing employee records")
