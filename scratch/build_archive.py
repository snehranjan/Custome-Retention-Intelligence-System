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

# 1. Define Phase Directory Structure
phase_dirs = [
    "PHASE_01",
    "PHASE_02",
    "PHASE_03",
    "PHASE_04",
    "PHASE_05",
    "PHASE_05_1",
    "PHASE_06",
    "PHASE_07",
    "PHASE_07_1",
    "PHASE_07_2",
    "PHASE_08",
]

# 2. Define Screenshot Directory Structure
screenshot_dirs = [
    os.path.join("01_PUBLIC_WEBSITE", "HERO_SECTION"),
    os.path.join("01_PUBLIC_WEBSITE", "LANDING_PAGE"),
    os.path.join("01_PUBLIC_WEBSITE", "RESPONSIVE_VIEWS"),
    os.path.join("02_AUTHENTICATION", "EMPLOYEE_AUTH"),
    os.path.join("02_AUTHENTICATION", "ADMIN_AUTH"),
    os.path.join("02_AUTHENTICATION", "ACCESS_CONTROL"),
    os.path.join("03_EMPLOYEE_PORTAL", "OVERVIEW_DASHBOARD"),
    os.path.join("03_EMPLOYEE_PORTAL", "CUSTOMER_EXPLORER"),
    os.path.join("03_EMPLOYEE_PORTAL", "PREDICTION_EXPLORER"),
    os.path.join("03_EMPLOYEE_PORTAL", "SEGMENTATION_EXPLORER"),
    os.path.join("03_EMPLOYEE_PORTAL", "ANALYTICS_PERFORMANCE"),
    os.path.join("03_EMPLOYEE_PORTAL", "RECOMMENDATION_CENTER"),
    os.path.join("04_ADMIN_PORTAL", "ADMIN_DASHBOARD"),
    os.path.join("04_ADMIN_PORTAL", "EMPLOYEE_MANAGEMENT"),
    os.path.join("04_ADMIN_PORTAL", "APPROVAL_WORKFLOW"),
    os.path.join("04_ADMIN_PORTAL", "SYSTEM_HEALTH"),
    os.path.join("05_THEME_DESIGNS", "LIGHT_MODE"),
    os.path.join("05_THEME_DESIGNS", "DARK_MODE"),
    os.path.join("06_RESPONSIVE_TESTING", "DESKTOP_1440"),
    os.path.join("06_RESPONSIVE_TESTING", "LAPTOP_1024"),
    os.path.join("06_RESPONSIVE_TESTING", "TABLET_768"),
    os.path.join("06_RESPONSIVE_TESTING", "MOBILE_390"),
    "07_AUTHENTICATION_AND_SECURITY",
    "08_TESTING_AND_VALIDATION",
    "09_DEPLOYMENT",
]

# Create all folders
for pd in phase_dirs:
    os.makedirs(os.path.join(DOCS_ROOT, pd), exist_ok=True)

for sd in screenshot_dirs:
    os.makedirs(os.path.join(SCREENSHOTS_ROOT, sd), exist_ok=True)

print("Created folder structures cleanly.")
