"""
Indian E-Commerce Customer Retention Intelligence System
Module: Comprehensive Master Test Suite (Pytest Interface)
Description: Integrates all Phase 1 through Phase 5.1 validation suites into a unified
             executable pytest test harness for QA automation and continuous integration.

Author: Senior Software Architect & QA Automation Engineer
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend", "ml"))

import validate_data
import validate_features
import validate_segmentation
import validate_modeling_data
import validate_training
import validate_final_model
import validate_independent_cohort
import validate_advanced_features
import validate_checkpoint3
import validate_final_ml


def _run_with_system_exit_guard(func):
    """Executes a validation suite function and confirms exit code is 0."""
    try:
        res = func()
        assert res is True or res is None, f"{func.__name__} returned False or failure status"
    except SystemExit as e:
        assert e.code == 0, f"{func.__name__} exited with non-zero exit code: {e.code}"


def test_phase1_raw_dataset_integrity():
    """Verify Phase 1 synthetic raw dataset integrity and temporal partitioning."""
    _run_with_system_exit_guard(validate_data.main)


def test_phase3_features_and_anti_leakage():
    """Verify Phase 3 feature engineering integrity, bounded values, and zero leakage."""
    _run_with_system_exit_guard(validate_features.main)


def test_phase4_customer_segmentation():
    """Verify Phase 4 RFM K-Means clustering, zero-delivered isolation, and stability."""
    _run_with_system_exit_guard(validate_segmentation.main)


def test_phase5_modeling_dataset_and_splits():
    """Verify Phase 5 stratified train/val/test splits and zero-leakage partitions."""
    _run_with_system_exit_guard(validate_modeling_data.main)


def test_phase5_training_and_pipelines():
    """Verify Phase 5 pipeline architectures, preprocessors, and CV metrics."""
    _run_with_system_exit_guard(validate_training.main)


def test_phase5_final_baseline_model():
    """Verify Phase 5 final baseline model integrity, threshold locking, and reproducibility."""
    _run_with_system_exit_guard(validate_final_model.run_final_validation)


def test_phase5_1_independent_cohort_integrity():
    """Verify Phase 5.1 sealed independent test cohort generation and set disjointness."""
    _run_with_system_exit_guard(validate_independent_cohort.run_validation)


def test_phase5_1_advanced_feature_engineering():
    """Verify Phase 5.1 velocity momentum ratios, friction index, and within-fold pruner."""
    _run_with_system_exit_guard(validate_advanced_features.run_all_tests)


def test_phase5_1_checkpoint3_nested_cv():
    """Verify Phase 5.1 Checkpoint 3 5x3 nested CV, OOF coverage, and candidate ranking."""
    _run_with_system_exit_guard(validate_checkpoint3.run_checkpoint3_validation)


def test_phase5_1_final_ml_completion():
    """Verify Phase 5.1 Checkpoint 4 final model lock, independent evaluation, and metrics."""
    _run_with_system_exit_guard(validate_final_ml.run_final_ml_validation)
