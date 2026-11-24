"""
Indian E-Commerce Customer Retention Intelligence System
Repository Layer Exception Hierarchy (Phase 7.4)

Provides standardized, application-level exceptions for database operations,
sanitizing error details to prevent leaking internal filesystem paths or
sensitive configuration parameters.
"""


class RepositoryError(Exception):
    """Base exception for all repository data access errors."""
    def __init__(self, message: str, details: str = ""):
        super().__init__(message)
        self.message = message
        self.details = details


class DatabaseUnavailableError(RepositoryError):
    """Raised when the database cannot be connected to or initialized."""
    pass


class ConfigurationError(RepositoryError):
    """Raised when storage configuration or credentials are missing, invalid, or mismatched."""
    pass


class CustomerNotFoundError(RepositoryError):
    """Raised when a queried customer ID is not found in storage."""
    pass


class DuplicateRecordError(RepositoryError):
    """Raised when an insertion violates a unique constraint or primary key."""
    pass


class ForeignKeyViolationError(RepositoryError):
    """Raised when a foreign key constraint check fails."""
    pass


class ConstraintViolationError(RepositoryError):
    """Raised when a check constraint or column domain validation fails."""
    pass


class DatabaseLockError(RepositoryError):
    """Raised when a concurrent lock or busy timeout occurs in storage."""
    pass


class TransactionError(RepositoryError):
    """Raised when an explicit database transaction fails or cannot commit."""
    pass
