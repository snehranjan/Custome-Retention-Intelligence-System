import os
import shutil
import hashlib
import json
from datetime import datetime

WORKSPACE = r"C:\customer churn retention system"
ARCHIVE_ROOT = os.path.join(WORKSPACE, "RETAINIQ_PROJECT_ARCHIVE")
DOCS_ROOT = os.path.join(ARCHIVE_ROOT, "PHASE_DOCUMENTATION")
SCREENSHOTS_ROOT = os.path.join(ARCHIVE_ROOT, "SCREENSHOTS")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

inventory_docs = []
inventory_imgs = []

def copy_verified(src_rel, dst_folder, category_name):
    src_abs = os.path.join(WORKSPACE, src_rel)
    if not os.path.exists(src_abs):
        raise FileNotFoundError(f"Source file not found: {src_abs}")
    
    filename = os.path.basename(src_abs)
    dst_abs = os.path.join(dst_folder, filename)
    os.makedirs(dst_folder, exist_ok=True)
    
    shutil.copy2(src_abs, dst_abs)
    
    src_hash = sha256_file(src_abs)
    dst_hash = sha256_file(dst_abs)
    sz = os.path.getsize(dst_abs)
    
    if src_hash != dst_hash:
        raise ValueError(f"Hash mismatch on {filename}: {src_hash} != {dst_hash}")
    
    record = {
        "filename": filename,
        "original_path": src_rel,
        "archive_path": os.path.relpath(dst_abs, WORKSPACE),
        "size_bytes": sz,
        "sha256": src_hash,
        "category": category_name,
        "verified": True
    }
    return record

# -------------------------------------------------------------
# 1. PHASE DOCUMENTATION MAPPING
# -------------------------------------------------------------
doc_mappings = [
    # PHASE_01
    ("PROJECT_CONTEXT.md", "PHASE_01", "Technical Architecture & Dataset Schema"),
    ("PROJECT_HANDOFF.md", "PHASE_01", "Project Handoff & Development Milestones"),
    ("DEVELOPMENT_RULES.md", "PHASE_01", "Permanent Engineering Invariants"),
    ("README.md", "PHASE_01", "Root Project Overview & Getting Started"),

    # PHASE_02
    (r"reports\eda_report.md", "PHASE_02", "Exploratory Data Analysis Report"),

    # PHASE_03
    (r"reports\feature_engineering_report.md", "PHASE_03", "Feature Engineering & Anti-Leakage Audit"),

    # PHASE_04
    (r"reports\phase4_segmentation_report.md", "PHASE_04", "RFM Customer Segmentation Report"),

    # PHASE_05
    (r"reports\phase5\checkpoint3_training_report.md", "PHASE_05", "Baseline Training Report"),
    (r"reports\phase5\checkpoint4_validation_report.md", "PHASE_05", "Model Validation Report"),
    (r"reports\phase5\checkpoint5_final_model_report.md", "PHASE_05", "Phase 5 Final Model Report"),
    (r"reports\phase5\final_test_classification_report.txt", "PHASE_05", "Baseline Classification Report"),
    (r"reports\phase5\model_explainability_report.md", "PHASE_05", "Model Explainability Report"),

    # PHASE_05_1
    (r"reports\phase5_1\advanced_feature_engineering_report.md", "PHASE_05_1", "Advanced Feature Engineering Report"),
    (r"reports\phase5_1\checkpoint1_model_audit.md", "PHASE_05_1", "Mathematical Bayes Error & Oracle Audit"),
    (r"reports\phase5_1\checkpoint2_independent_cohort_report.md", "PHASE_05_1", "Independent Test Cohort Evaluation"),
    (r"reports\phase5_1\checkpoint2_2_pruner_alignment_audit.md", "PHASE_05_1", "Correlation Pruner Alignment Audit"),
    (r"reports\phase5_1\checkpoint3_1_methodology_audit.md", "PHASE_05_1", "Experimental Methodology Audit"),
    (r"reports\phase5_1\checkpoint3\checkpoint3_experiment_report.md", "PHASE_05_1", "Config D Experiment Evaluation"),
    (r"reports\phase5_1\final_evaluation\independent_evaluation_report.md", "PHASE_05_1", "Independent Evaluation Scorecard"),
    (r"reports\phase5_1\final_evaluation\ml_completion_report.md", "PHASE_05_1", "ML Pipeline Completion Report"),

    # PHASE_06
    (r"reports\phase8\PHASE_RETAINIQ_STAGE_6_ADMIN_PORTAL_REPORT.md", "PHASE_06", "Stage 6 Administrator Portal Report"),
    (r"reports\final_project_audit\final_project_audit_report.md", "PHASE_06", "Final Project Master Audit Report"),
    (r"reports\final_project_audit\known_limitations.md", "PHASE_06", "Known Limitations & Operational Bounds"),
    (r"reports\final_project_audit\project_readiness_report.md", "PHASE_06", "Pre-Deployment Readiness Report"),

    # PHASE_07
    (r"reports\phase7\phase7_1_backend_audit_report.md", "PHASE_07", "Phase 7.1 Backend Audit Report"),
    (r"reports\phase7\phase7_2_fastapi_setup_report.md", "PHASE_07", "FastAPI Setup & Route Architecture"),
    (r"reports\phase7\phase7_3_ml_integration_report.md", "PHASE_07", "FastAPI ML Pipeline Integration"),
    (r"reports\phase7\phase7_4_checkpoint2_schema_report.md", "PHASE_07", "Database Schema Report"),
    (r"reports\phase7\phase7_4_checkpoint3_sqlite_report.md", "PHASE_07", "SQLite Local Persistence Report"),
    (r"reports\phase7\phase7_4_checkpoint4_supabase_report.md", "PHASE_07", "Supabase Remote Integration Report"),
    (r"reports\phase7\phase7_4_checkpoint5_customer_import_report.md", "PHASE_07", "Customer Import Data Migration"),
    (r"reports\phase7\phase7_4_checkpoint6_ml_persistence_report.md", "PHASE_07", "ML Prediction Persistence"),
    (r"reports\phase7\phase7_4_checkpoint7_database_api_report.md", "PHASE_07", "Database API Integration"),
    (r"reports\phase7\phase7_4_checkpoint7_test_hang_diagnostic_report.md", "PHASE_07", "Test Diagnostic Diagnostic Report"),
    (r"reports\phase7\phase7_4_checkpoint8_final_audit_report.md", "PHASE_07", "Phase 7.4 Final Audit Report"),
    (r"reports\phase7\phase7_5_authentication_architecture_audit.md", "PHASE_07", "Authentication Security Audit"),
    (r"reports\phase7\phase7_5_checkpoint1_report.md", "PHASE_07", "Auth Checkpoint 1 Report"),
    (r"reports\phase7\phase7_5_checkpoint2_report.md", "PHASE_07", "Auth Checkpoint 2 Report"),
    (r"reports\phase7\phase7_5_checkpoint3_report.md", "PHASE_07", "Auth Checkpoint 3 Report"),
    (r"reports\phase7\phase7_5_checkpoint4_report.md", "PHASE_07", "Auth Checkpoint 4 Report"),
    (r"reports\phase7\phase7_5_checkpoint5_final_security_audit.md", "PHASE_07", "Phase 7.5 Final Security Audit"),
    (r"reports\phase7\supabase_check4_column_reconciliation.md", "PHASE_07", "Supabase Column Reconciliation"),
    (r"reports\phase7\supabase_check7_index_reconciliation.md", "PHASE_07", "Supabase Index Reconciliation"),
    (r"reports\phase7\supabase_migrations_preparation_report.md", "PHASE_07", "Supabase Migrations Preparation"),
    (r"reports\phase7\supabase_migrations_setup_guide.md", "PHASE_07", "Supabase Migrations Setup Guide"),
    (r"reports\phase7\supabase_migrations_verification_review.md", "PHASE_07", "Supabase Migrations Verification"),
    (r"reports\phase7\supabase_secret_rotation_verification_report.md", "PHASE_07", "Secret Rotation Verification"),

    # PHASE_07_1
    (r"reports\phase8\PHASE_RETAINIQ_STAGE_7_1_RECONCILIATION_REPORT.md", "PHASE_07_1", "Stage 7.1 Final Audit Reconciliation"),

    # PHASE_07_2
    (r"reports\phase8\PHASE_RETAINIQ_STAGE_7_2_FINAL_RECONCILIATION_REPORT.md", "PHASE_07_2", "Stage 7.2 Model Tree & Warning Reconciliation"),

    # PHASE_08
    (r"reports\phase8\phase8_1_frontend_readiness_audit.md", "PHASE_08", "Frontend Readiness Audit"),
    (r"reports\phase8\phase8_2_frontend_foundation_report.md", "PHASE_08", "Frontend Foundation Report"),
    (r"reports\phase8\phase8_3_1_hero_implementation_report.md", "PHASE_08", "Hero Section Implementation Report"),
    (r"reports\phase8\phase8_3_2_platform_highlights_report.md", "PHASE_08", "Platform Highlights Report"),
    (r"reports\phase8\phase8_3_3_feature_showcase_report.md", "PHASE_08", "Feature Showcase Report"),
    (r"reports\phase8\phase8_3_4_how_it_works_report.md", "PHASE_08", "How It Works Architecture Report"),
    (r"reports\phase8\phase8_3_5_about_academic_report.md", "PHASE_08", "About Academic Report"),
    (r"reports\phase8\phase8_3_5_visual_audit_report.md", "PHASE_08", "Visual Quality Audit Report"),
    (r"reports\phase8\phase8_4_1_architecture_security_audit.md", "PHASE_08", "Frontend Auth Architecture Audit"),
    (r"reports\phase8\phase8_4_2_frontend_auth_foundation_report.md", "PHASE_08", "Frontend Auth Foundation Report"),
    (r"reports\phase8\phase8_4_3_employee_authentication_ui_report.md", "PHASE_08", "Employee Authentication UI Report"),
    (r"reports\phase8\phase8_4_4_backend_customer_management_api_bridge_report.md", "PHASE_08", "Customer Management API Bridge Report"),
    (r"reports\phase8\phase8_4_5_employee_registration_admin_approval_report.md", "PHASE_08", "Registration & Admin Approval Report"),
    (r"reports\phase8\phase8_4_5_1_remote_supabase_migration_preflight_report.md", "PHASE_08", "Migration Preflight Report"),
    (r"reports\phase8\phase8_4_5_2_migration_hardening_review.md", "PHASE_08", "Migration Hardening Review"),
    (r"reports\phase8\phase8_4_5_2_1_post_drop_recovery_audit.md", "PHASE_08", "Post-Drop Recovery Audit"),
    (r"reports\phase8\PHASE_8_4_5_3_STEP_1_MIGRATION_SAFETY_AUDIT.md", "PHASE_08", "Step 1 Migration Safety Audit"),
    (r"reports\phase8\PHASE_8_4_5_3_STEP_2_MIGRATION_CORRECTIONS.md", "PHASE_08", "Step 2 Migration Corrections"),
    (r"reports\phase8\PHASE_8_4_5_3_STEP_3_FINAL_SECURITY_AUDIT.md", "PHASE_08", "Step 3 Security Audit"),
    (r"reports\phase8\PHASE_8_4_5_3_STEP_4_FINAL_SQL_REVIEW.md", "PHASE_08", "Step 4 SQL Review"),
    (r"reports\phase8\PHASE_8_4_5_3_STEP_5_FINAL_SAFETY_REVIEW.md", "PHASE_08", "Step 5 Safety Review"),
    (r"reports\phase8\PHASE_8_4_5_3_STEP_6_FINAL_CATALOG_REVIEW.md", "PHASE_08", "Step 6 Catalog Review"),
    (r"reports\phase8\PHASE_8_4_5_3_FINAL_MIGRATION_REVIEW.md", "PHASE_08", "Final Migration Review"),
    (r"reports\phase8\PHASE_8_4_6_COMPLETION_REPORT.md", "PHASE_08", "Phase 8.4.6 Completion Report"),
    (r"reports\phase8\PHASE_8_4_7_COMPLETION_REPORT.md", "PHASE_08", "Phase 8.4.7 Completion Report"),
    (r"reports\phase8\PHASE_8_4_8_COMPLETION_REPORT.md", "PHASE_08", "Phase 8.4.8 Completion Report"),
    (r"reports\phase8\PHASE_AUTH_STABILIZATION_COMPLETION_REPORT.md", "PHASE_08", "Auth Stabilization Completion Report"),
    (r"reports\phase8\PHASE_PRE_DEPLOYMENT_WEBSITE_POLISH_REPORT.md", "PHASE_08", "Pre-Deployment Website Polish Report"),
    (r"reports\phase8\PHASE_RETAINIQ_UNSLOP_STAGE_3_REPORT.md", "PHASE_08", "Stage 3 Design Tokens Report"),
    (r"reports\phase8\PHASE_RETAINIQ_UNSLOP_STAGE_4_REPORT.md", "PHASE_08", "Stage 4 Public Website Transformation"),
    (r"reports\phase8\PHASE_RETAINIQ_UNSLOP_STAGE_5_REPORT.md", "PHASE_08", "Stage 5 Employee Portal Transformation"),
    (r"reports\phase8\PHASE_RETAINIQ_STAGE_5_METRIC_INTEGRITY_AUDIT.md", "PHASE_08", "Stage 5 Metric Integrity Audit"),
    (r"reports\phase8\PHASE_RETAINIQ_GLOBAL_SPACING_REFINEMENT_REPORT.md", "PHASE_08", "Global Spacing & Container Refinement"),
    (r"reports\phase8\PHASE_RETAINIQ_STAGE_7_COMPLETE_APPLICATION_AUDIT_REPORT.md", "PHASE_08", "Stage 7 Complete QA Audit Report"),
    (r"reports\phase8\RETAINIQ_THEME_SWITCHER_IMPLEMENTATION_REPORT.md", "PHASE_08", "Theme Switcher Implementation Report"),
]

print(f"Total doc mapping entries: {len(doc_mappings)}")

for rel_path, phase_folder, desc in doc_mappings:
    target_dir = os.path.join(DOCS_ROOT, phase_folder)
    rec = copy_verified(rel_path, target_dir, phase_folder)
    rec["description"] = desc
    inventory_docs.append(rec)

print(f"Successfully copied and verified {len(inventory_docs)} documentation files!")

# -------------------------------------------------------------
# 2. SCREENSHOT MAPPING
# -------------------------------------------------------------
SCREENSHOT_SOURCE = r"reports\phase8\screenshots"

screenshot_mappings = [
    # 01_PUBLIC_WEBSITE / HERO_SECTION
    ("hero_1440_desktop.png", os.path.join("01_PUBLIC_WEBSITE", "HERO_SECTION")),
    ("hero_1024_laptop.png", os.path.join("01_PUBLIC_WEBSITE", "HERO_SECTION")),
    ("hero_768_tablet.png", os.path.join("01_PUBLIC_WEBSITE", "HERO_SECTION")),
    ("hero_390_mobile.png", os.path.join("01_PUBLIC_WEBSITE", "HERO_SECTION")),

    # 01_PUBLIC_WEBSITE / LANDING_PAGE
    ("landing_1440x900.png", os.path.join("01_PUBLIC_WEBSITE", "LANDING_PAGE")),
    ("landing_1024x768.png", os.path.join("01_PUBLIC_WEBSITE", "LANDING_PAGE")),
    ("landing_768x1024.png", os.path.join("01_PUBLIC_WEBSITE", "LANDING_PAGE")),
    ("landing_390x844.png", os.path.join("01_PUBLIC_WEBSITE", "LANDING_PAGE")),
    ("about_full_landing_page.png", os.path.join("01_PUBLIC_WEBSITE", "LANDING_PAGE")),
    ("features_full_landing_page.png", os.path.join("01_PUBLIC_WEBSITE", "LANDING_PAGE")),
    ("how_it_works_full_landing_page.png", os.path.join("01_PUBLIC_WEBSITE", "LANDING_PAGE")),
    ("platform_overview_full.png", os.path.join("01_PUBLIC_WEBSITE", "LANDING_PAGE")),
    ("not_found_1440x900.png", os.path.join("01_PUBLIC_WEBSITE", "LANDING_PAGE")),

    # 01_PUBLIC_WEBSITE / RESPONSIVE_VIEWS
    ("features_1440_desktop.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("features_1024_laptop.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("features_768_tablet.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("features_390_mobile.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("platform_1440_desktop.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("platform_1024_laptop.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("platform_768_tablet.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("platform_390_mobile.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("how_it_works_1440_desktop.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("how_it_works_1024_laptop.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("how_it_works_768_tablet.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("how_it_works_390_mobile.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("how_it_works_architecture_1440.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("about_1440_desktop.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("about_1024_laptop.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("about_768_tablet.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),
    ("about_390_mobile.png", os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS")),

    # 02_AUTHENTICATION / EMPLOYEE_AUTH
    ("login_1440_desktop.png", os.path.join("02_AUTHENTICATION", "EMPLOYEE_AUTH")),
    ("login_1024_laptop.png", os.path.join("02_AUTHENTICATION", "EMPLOYEE_AUTH")),
    ("login_768_tablet.png", os.path.join("02_AUTHENTICATION", "EMPLOYEE_AUTH")),
    ("login_390_mobile.png", os.path.join("02_AUTHENTICATION", "EMPLOYEE_AUTH")),
    ("login_1440x900.png", os.path.join("02_AUTHENTICATION", "EMPLOYEE_AUTH")),
    ("login_390x844.png", os.path.join("02_AUTHENTICATION", "EMPLOYEE_AUTH")),
    ("login_validation_errors.png", os.path.join("02_AUTHENTICATION", "EMPLOYEE_AUTH")),

    # 02_AUTHENTICATION / ADMIN_AUTH
    ("admin_guard_1440x900.png", os.path.join("02_AUTHENTICATION", "ADMIN_AUTH")),
    ("admin_guard_390x844.png", os.path.join("02_AUTHENTICATION", "ADMIN_AUTH")),

    # 02_AUTHENTICATION / ACCESS_CONTROL
    ("employee_guard_1440x900.png", os.path.join("02_AUTHENTICATION", "ACCESS_CONTROL")),
    ("auth_foundation_1440.png", os.path.join("02_AUTHENTICATION", "ACCESS_CONTROL")),
    ("auth_foundation_1024.png", os.path.join("02_AUTHENTICATION", "ACCESS_CONTROL")),
    ("auth_foundation_768.png", os.path.join("02_AUTHENTICATION", "ACCESS_CONTROL")),
    ("auth_foundation_390.png", os.path.join("02_AUTHENTICATION", "ACCESS_CONTROL")),

    # 03_EMPLOYEE_PORTAL / OVERVIEW_DASHBOARD
    ("employee_authenticated_1440x900.png", os.path.join("03_EMPLOYEE_PORTAL", "OVERVIEW_DASHBOARD")),
    ("employee_authenticated_1024x768.png", os.path.join("03_EMPLOYEE_PORTAL", "OVERVIEW_DASHBOARD")),
    ("employee_authenticated_768x1024.png", os.path.join("03_EMPLOYEE_PORTAL", "OVERVIEW_DASHBOARD")),
    ("employee_authenticated_390x844.png", os.path.join("03_EMPLOYEE_PORTAL", "OVERVIEW_DASHBOARD")),
    ("employee_light_1440x900.png", os.path.join("03_EMPLOYEE_PORTAL", "OVERVIEW_DASHBOARD")),
    ("employee_dark_1440x900.png", os.path.join("03_EMPLOYEE_PORTAL", "OVERVIEW_DASHBOARD")),

    # 03_EMPLOYEE_PORTAL / CUSTOMER_EXPLORER
    ("employee_customer_explorer_light.png", os.path.join("03_EMPLOYEE_PORTAL", "CUSTOMER_EXPLORER")),
    ("employee_customer_explorer_dark.png", os.path.join("03_EMPLOYEE_PORTAL", "CUSTOMER_EXPLORER")),

    # 03_EMPLOYEE_PORTAL / PREDICTION_EXPLORER
    ("employee_prediction_explorer_light.png", os.path.join("03_EMPLOYEE_PORTAL", "PREDICTION_EXPLORER")),
    ("employee_prediction_explorer_dark.png", os.path.join("03_EMPLOYEE_PORTAL", "PREDICTION_EXPLORER")),

    # 03_EMPLOYEE_PORTAL / SEGMENTATION_EXPLORER
    ("employee_segmentation_explorer_light.png", os.path.join("03_EMPLOYEE_PORTAL", "SEGMENTATION_EXPLORER")),
    ("employee_segmentation_explorer_dark.png", os.path.join("03_EMPLOYEE_PORTAL", "SEGMENTATION_EXPLORER")),

    # 03_EMPLOYEE_PORTAL / ANALYTICS_PERFORMANCE
    ("employee_analytics_light.png", os.path.join("03_EMPLOYEE_PORTAL", "ANALYTICS_PERFORMANCE")),
    ("employee_analytics_dark.png", os.path.join("03_EMPLOYEE_PORTAL", "ANALYTICS_PERFORMANCE")),

    # 03_EMPLOYEE_PORTAL / RECOMMENDATION_CENTER
    ("employee_recommendations_light.png", os.path.join("03_EMPLOYEE_PORTAL", "RECOMMENDATION_CENTER")),
    ("employee_recommendations_dark.png", os.path.join("03_EMPLOYEE_PORTAL", "RECOMMENDATION_CENTER")),

    # 04_ADMIN_PORTAL / ADMIN_DASHBOARD
    ("admin_authenticated_1440x900.png", os.path.join("04_ADMIN_PORTAL", "ADMIN_DASHBOARD")),
    ("admin_authenticated_1024x768.png", os.path.join("04_ADMIN_PORTAL", "ADMIN_DASHBOARD")),
    ("admin_authenticated_768x1024.png", os.path.join("04_ADMIN_PORTAL", "ADMIN_DASHBOARD")),
    ("admin_authenticated_390x844.png", os.path.join("04_ADMIN_PORTAL", "ADMIN_DASHBOARD")),
    ("admin_light_1440x900.png", os.path.join("04_ADMIN_PORTAL", "ADMIN_DASHBOARD")),
    ("admin_dark_1440x900.png", os.path.join("04_ADMIN_PORTAL", "ADMIN_DASHBOARD")),

    # 04_ADMIN_PORTAL / EMPLOYEE_MANAGEMENT
    ("admin_employee_management_light.png", os.path.join("04_ADMIN_PORTAL", "EMPLOYEE_MANAGEMENT")),
    ("admin_employee_management_dark.png", os.path.join("04_ADMIN_PORTAL", "EMPLOYEE_MANAGEMENT")),

    # 04_ADMIN_PORTAL / APPROVAL_WORKFLOW
    ("admin_approval_workflow_light.png", os.path.join("04_ADMIN_PORTAL", "APPROVAL_WORKFLOW")),
    ("admin_approval_workflow_dark.png", os.path.join("04_ADMIN_PORTAL", "APPROVAL_WORKFLOW")),

    # 04_ADMIN_PORTAL / SYSTEM_HEALTH
    ("admin_light_1024x768.png", os.path.join("04_ADMIN_PORTAL", "SYSTEM_HEALTH")),
    ("admin_dark_1024x768.png", os.path.join("04_ADMIN_PORTAL", "SYSTEM_HEALTH")),

    # 05_THEME_DESIGNS / LIGHT_MODE
    ("public_light_1440x900.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),
    ("public_light_1024x768.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),
    ("public_light_768x1024.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),
    ("public_light_390x844.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),
    ("employee_light_1440x900.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),
    ("employee_light_1024x768.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),
    ("employee_light_768x1024.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),
    ("employee_light_390x844.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),
    ("admin_light_1440x900.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),
    ("admin_light_1024x768.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),
    ("admin_light_768x1024.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),
    ("admin_light_390x844.png", os.path.join("05_THEME_DESIGNS", "LIGHT_MODE")),

    # 05_THEME_DESIGNS / DARK_MODE
    ("public_dark_1440x900.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),
    ("public_dark_1024x768.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),
    ("public_dark_768x1024.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),
    ("public_dark_390x844.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),
    ("employee_dark_1440x900.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),
    ("employee_dark_1024x768.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),
    ("employee_dark_768x1024.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),
    ("employee_dark_390x844.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),
    ("admin_dark_1440x900.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),
    ("admin_dark_1024x768.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),
    ("admin_dark_768x1024.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),
    ("admin_dark_390x844.png", os.path.join("05_THEME_DESIGNS", "DARK_MODE")),

    # 06_RESPONSIVE_TESTING / DESKTOP_1440
    ("public_light_1440x900.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("public_dark_1440x900.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("employee_light_1440x900.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("employee_dark_1440x900.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("admin_light_1440x900.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("admin_dark_1440x900.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("hero_1440_desktop.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("features_1440_desktop.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("platform_1440_desktop.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("how_it_works_1440_desktop.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("about_1440_desktop.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("login_1440_desktop.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),
    ("auth_foundation_1440.png", os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440")),

    # 06_RESPONSIVE_TESTING / LAPTOP_1024
    ("public_light_1024x768.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("public_dark_1024x768.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("employee_light_1024x768.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("employee_dark_1024x768.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("admin_light_1024x768.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("admin_dark_1024x768.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("hero_1024_laptop.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("features_1024_laptop.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("platform_1024_laptop.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("how_it_works_1024_laptop.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("about_1024_laptop.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("login_1024_laptop.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),
    ("auth_foundation_1024.png", os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024")),

    # 06_RESPONSIVE_TESTING / TABLET_768
    ("public_light_768x1024.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("public_dark_768x1024.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("employee_light_768x1024.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("employee_dark_768x1024.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("admin_light_768x1024.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("admin_dark_768x1024.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("hero_768_tablet.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("features_768_tablet.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("platform_768_tablet.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("how_it_works_768_tablet.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("about_768_tablet.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("login_768_tablet.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),
    ("auth_foundation_768.png", os.path.join("06_RESPONSIVE_TESTING", "TABLET_768")),

    # 06_RESPONSIVE_TESTING / MOBILE_390
    ("public_light_390x844.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("public_dark_390x844.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("employee_light_390x844.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("employee_dark_390x844.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("admin_light_390x844.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("admin_dark_390x844.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("hero_390_mobile.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("features_390_mobile.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("platform_390_mobile.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("how_it_works_390_mobile.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("about_390_mobile.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("login_390_mobile.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),
    ("auth_foundation_390.png", os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390")),

    # 07_AUTHENTICATION_AND_SECURITY
    ("admin_guard_1440x900.png", "07_AUTHENTICATION_AND_SECURITY"),
    ("admin_guard_390x844.png", "07_AUTHENTICATION_AND_SECURITY"),
    ("employee_guard_1440x900.png", "07_AUTHENTICATION_AND_SECURITY"),
    ("auth_foundation_1440.png", "07_AUTHENTICATION_AND_SECURITY"),
    ("login_validation_errors.png", "07_AUTHENTICATION_AND_SECURITY"),

    # 08_TESTING_AND_VALIDATION
    ("landing_1440_checkpoint8_4_3.png", "08_TESTING_AND_VALIDATION"),
    ("features_1440_deep_full.png", "08_TESTING_AND_VALIDATION"),

    # 09_DEPLOYMENT
    ("not_found_1440x900.png", "09_DEPLOYMENT"),
]

print(f"Total screenshot mapping entries: {len(screenshot_mappings)}")

for src_name, subfolder in screenshot_mappings:
    src_rel = os.path.join(SCREENSHOT_SOURCE, src_name)
    target_dir = os.path.join(SCREENSHOTS_ROOT, subfolder)
    rec = copy_verified(src_rel, target_dir, subfolder)
    inventory_imgs.append(rec)

print(f"Successfully copied and verified {len(inventory_imgs)} screenshot files!")

# Save raw inventory metadata
with open(os.path.join(ARCHIVE_ROOT, ".archive_metadata.json"), "w", encoding="utf-8") as fp:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "total_docs": len(inventory_docs),
        "total_imgs": len(inventory_imgs),
        "docs": inventory_docs,
        "images": inventory_imgs
    }, fp, indent=2)

print("Inventory metadata saved.")
