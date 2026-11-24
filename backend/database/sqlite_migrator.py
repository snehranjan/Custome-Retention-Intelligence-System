"""
Indian E-Commerce Customer Retention Intelligence System
SQLite Schema & Migration Manager (Phase 7.4)

Provides:
- Idempotent schema application for local persistent SQLite storage
- Schema migration tracking via schema_migrations table
- Integrity verification of SQLite schema objects (tables, indexes, constraints)
"""

import os
import sqlite3
from typing import List, Tuple
from backend.app.core.logging import logger

MIGRATION_VERSION = "001_initial_schema"
MIGRATION_NAME = "Initial schema for customers, predictions, segments, and recommendations"

MIGRATION_008_VERSION = "008_employee_registry"
MIGRATION_008_NAME = "Persistent employee registry for administrator-controlled onboarding"


class SQLiteMigrator:
    """Manages SQLite schema creation, migrations, and version tracking."""

    @classmethod
    def get_schema_sql_path(cls) -> str:
        """Returns the absolute path to backend/database/sqlite_schema.sql."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "sqlite_schema.sql"))

    @classmethod
    def apply_migrations(cls, db_path: str) -> bool:
        """
        Idempotently applies the complete SQLite schema and records migration version.
        Returns True if a new migration was applied, False if already up to date.
        """
        # Ensure parent directory exists
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        sql_path = cls.get_schema_sql_path()
        if not os.path.isfile(sql_path):
            raise FileNotFoundError(f"SQLite schema file not found at: {sql_path}")

        with open(sql_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()

            # Execute schema DDL
            cursor.executescript(schema_sql)

            # Check if migration version is already recorded
            cursor.execute("SELECT version FROM schema_migrations WHERE version = ?", (MIGRATION_VERSION,))
            row = cursor.fetchone()

            applied_any = False
            if row is None:
                cursor.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (MIGRATION_VERSION, MIGRATION_NAME),
                )
                applied_any = True
                logger.info("Applied migration '%s' to SQLite database: %s", MIGRATION_VERSION, db_path)

            # Check and record Phase 8.4.5 employee registry migration
            cursor.execute("SELECT version FROM schema_migrations WHERE version = ?", (MIGRATION_008_VERSION,))
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (MIGRATION_008_VERSION, MIGRATION_008_NAME),
                )
                applied_any = True
                logger.info("Applied migration '%s' to SQLite database: %s", MIGRATION_008_VERSION, db_path)

            conn.commit()
            return applied_any
        finally:
            conn.close()

    @classmethod
    def get_applied_migrations(cls, db_path: str) -> List[Tuple[str, str, str]]:
        """Returns list of (version, name, applied_at) from schema_migrations."""
        if not os.path.isfile(db_path):
            return []
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version, name, applied_at FROM schema_migrations ORDER BY applied_at ASC")
            return cursor.fetchall()
        except sqlite3.OperationalError:
            # Table does not exist yet
            return []
        finally:
            conn.close()

    @classmethod
    def get_table_names(cls, db_path: str) -> List[str]:
        """Returns list of user tables in the SQLite database."""
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
