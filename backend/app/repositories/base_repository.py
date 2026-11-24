"""
Indian E-Commerce Customer Retention Intelligence System
Abstract Base Repository Interface (Phase 7.4)

Defines the contract for persistent storage operations across both
Supabase PostgreSQL and local SQLite fallback backends.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseRepository(ABC):
    """
    Abstract repository interface providing uniform customer lifecycle,
    ML prediction, RFM segmentation, and retention recommendation persistence.
    """

    # --------------------------------------------------------------------------
    # Customer Profile Persistence
    # --------------------------------------------------------------------------
    @abstractmethod
    def insert_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts a new customer record.
        Raises DuplicateRecordError if customer_id already exists.
        """
        pass

    @abstractmethod
    def upsert_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts or updates an existing customer profile by customer_id.
        """
        pass

    @abstractmethod
    def upsert_customers_batch(self, customers_data: List[Dict[str, Any]]) -> int:
        """
        Inserts or updates a batch of customer profiles atomically.
        Returns the count of successfully processed records.
        """
        pass

    @abstractmethod
    def get_existing_customer_ids(self) -> set:
        """
        Returns a set of all customer IDs currently stored.
        """
        pass

    @abstractmethod
    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single customer profile by string customer_id.
        Returns None if not found.
        """
        pass

    @abstractmethod
    def get_customer_count(self) -> int:
        """
        Returns the total count of customers in storage.
        """
        pass

    @abstractmethod
    def list_customers(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Lists customer profiles with pagination.
        """
        pass

    # --------------------------------------------------------------------------
    # Machine Learning Prediction History
    # --------------------------------------------------------------------------
    @abstractmethod
    def insert_prediction(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Records a machine learning churn prediction result for a customer.
        Raises ForeignKeyViolationError if customer does not exist.
        Raises ConstraintViolationError if probability or threshold invariants fail.
        """
        pass

    @abstractmethod
    def get_prediction_history(self, customer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves historical prediction records for a customer, newest first.
        """
        pass

    @abstractmethod
    def get_latest_prediction(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the most recent prediction for a customer, or None.
        """
        pass

    # --------------------------------------------------------------------------
    # RFM Customer Segmentation
    # --------------------------------------------------------------------------
    @abstractmethod
    def upsert_customer_segment(self, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assigns or updates a customer's RFM segment.
        If is_current is set to 1/True, all prior segment records for this customer
        are archived (is_current=0) to maintain single active segment uniqueness.
        """
        pass

    @abstractmethod
    def get_current_segment(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the single active segment assignment for a customer.
        """
        pass

    @abstractmethod
    def get_segment_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all historical and active segments for a customer.
        """
        pass

    # --------------------------------------------------------------------------
    # Retention Recommendations
    # --------------------------------------------------------------------------
    @abstractmethod
    def insert_recommendation(self, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persists a retention recommendation for a customer.
        prediction_id may be None.
        """
        pass

    @abstractmethod
    def get_recommendations(
        self, customer_id: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves recommendations for a customer, optionally filtered by status.
        """
        pass

    @abstractmethod
    def update_recommendation_status(
        self, recommendation_id: str, status: str
    ) -> Optional[Dict[str, Any]]:
        """
        Updates the execution status of a recommendation.
        Returns the updated record or None if not found.
        """
        pass

    # --------------------------------------------------------------------------
    # Storage Engine Health & Inspection
    # --------------------------------------------------------------------------
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        Returns diagnostic and health status information for the storage backend.
        """
        pass

    @abstractmethod
    def get_storage_status(self) -> Dict[str, Any]:
        """
        Returns comprehensive storage status, table availability, and migration readiness.
        """
        pass

    @abstractmethod
    def get_customer_metrics(self) -> Dict[str, int]:
        """
        Returns aggregated customer count metrics: total, churned, retained, null city, null state.
        """
        pass

    # --------------------------------------------------------------------------
    # Employee Registry & Administration (Phase 8.4.5)
    # Default implementations raise NotImplementedError for mock backward compatibility
    # --------------------------------------------------------------------------
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves employee record by administrator-issued employee_id.
        """
        raise NotImplementedError("Repository does not implement get_employee_by_id")

    def get_employee_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves employee record by work_email.
        """
        raise NotImplementedError("Repository does not implement get_employee_by_email")

    def get_employee_by_supabase_user_id(self, supabase_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves employee record by Supabase Auth user UUID.
        """
        raise NotImplementedError("Repository does not implement get_employee_by_supabase_user_id")

    def create_employee_invitation(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates an administrator-issued employee invitation in the registry with status 'INVITED'.
        """
        raise NotImplementedError("Repository does not implement create_employee_invitation")

    def register_employee(self, employee_id: str, supabase_user_id: str, work_email: str) -> Dict[str, Any]:
        """
        Updates an invited employee record upon applicant registration, setting status to 'PENDING'.
        """
        raise NotImplementedError("Repository does not implement register_employee")

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
        raise NotImplementedError("Repository does not implement update_employee_status")

    def get_employee_stats(self) -> Dict[str, int]:
        """
        Returns aggregated counts of employees by status (total, pending, approved, rejected, suspended, invited).
        """
        raise NotImplementedError("Repository does not implement get_employee_stats")

    def list_employees_by_status(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Lists employee records optionally filtered by status and search query with pagination.
        """
        raise NotImplementedError("Repository does not implement list_employees_by_status")

    # --------------------------------------------------------------------------
    # Intelligence & Advanced Analytics Queries (Phase 8.4.8)
    # --------------------------------------------------------------------------
    def query_customers(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        segment: Optional[int] = None,
        risk_tier: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        sort_by: str = "customer_id",
        sort_dir: str = "ASC",
    ) -> tuple:
        """
        Queries customers with search, multidimensional filters, and sorting.
        Returns (items, total_count).
        """
        raise NotImplementedError("Repository does not implement query_customers")

    def query_recommendations(
        self,
        limit: int = 50,
        offset: int = 0,
        segment: Optional[int] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        risk_tier: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple:
        """
        Queries enriched retention recommendations with filters.
        Returns (items, total_count).
        """
        raise NotImplementedError("Repository does not implement query_recommendations")

    def get_overview_analytics(self) -> Dict[str, Any]:
        """
        Calculates overview KPI metrics, risk distributions, and segment breakdowns.
        """
        raise NotImplementedError("Repository does not implement get_overview_analytics")

