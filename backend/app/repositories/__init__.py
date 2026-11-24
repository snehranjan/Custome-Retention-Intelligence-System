"""
Indian E-Commerce Customer Retention Intelligence System
Repository Layer Package (Phase 7.4)
"""

from typing import Optional

from backend.app.core.config import settings
from backend.app.repositories.base_repository import BaseRepository
from backend.app.repositories.exceptions import (
    ConfigurationError,
    ConstraintViolationError,
    CustomerNotFoundError,
    DatabaseLockError,
    DatabaseUnavailableError,
    DuplicateRecordError,
    ForeignKeyViolationError,
    RepositoryError,
    TransactionError,
)
from backend.app.repositories.sqlite_repository import SQLiteRepository
from backend.app.repositories.supabase_repository import SupabaseRepository


def get_repository(storage_mode: Optional[str] = None) -> BaseRepository:
    """
    Factory function returning the active repository implementation.
    Strictly enforces the NO SILENT FALLBACK invariant:
    - When STORAGE_MODE='supabase': initializes SupabaseRepository only.
      If credentials or connection fail, raises ConfigurationError or
      DatabaseUnavailableError. Never silently falls back to SQLite.
    - When STORAGE_MODE='sqlite': initializes SQLiteRepository only.
    - When STORAGE_MODE is invalid: raises ConfigurationError.
    """
    mode = (storage_mode or settings.STORAGE_MODE).lower()
    if mode == "sqlite":
        return SQLiteRepository()
    elif mode == "supabase":
        return SupabaseRepository()
    else:
        raise ConfigurationError(
            f"Invalid STORAGE_MODE '{mode}'. Must be either 'sqlite' or 'supabase'."
        )


__all__ = [
    "BaseRepository",
    "SQLiteRepository",
    "SupabaseRepository",
    "get_repository",
    "RepositoryError",
    "DatabaseUnavailableError",
    "ConfigurationError",
    "CustomerNotFoundError",
    "DuplicateRecordError",
    "ForeignKeyViolationError",
    "ConstraintViolationError",
    "DatabaseLockError",
    "TransactionError",
]
