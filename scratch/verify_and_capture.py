import subprocess
import time
import urllib.request
import os
import sys

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = os.path.abspath(r"reports\phase8\screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

viewports = [
    ("hero_1440_desktop.png", 1440, 1080),
    ("hero_1024_laptop.png", 1024, 900),
    ("hero_768_tablet.png", 768, 1024),
    ("hero_390_mobile.png", 390, 844),
]

print("1. Verifying dev server...")
with urllib.request.urlopen("http://localhost:5173", timeout=5) as resp:
    print(f"Dev server responding with HTTP {resp.status}")

print("\n2. Inspecting DOM for required text corrections...")
dump_args = [
    CHROME_PATH,
    "--headless=new",
    "--dump-dom",
    "--no-sandbox",
    "--disable-gpu",
    "http://localhost:5173"
]
dom_res = subprocess.run(dump_args, capture_output=True, text=True, timeout=15)
dom = dom_res.stdout

checks = [
    ("PREVIEW MODE", "Preview Mode" in dom),
    ("RETENTION OVERVIEW removed", "Retention Overview" not in dom),
    ("Illustrative Churn Risk Score", "Illustrative Churn Risk Score" in dom),
    ("Calibrated Churn Probability removed", "Calibrated Churn Probability" not in dom),
    ("Champions & High-Value Loyalists", "Champions &amp; High-Value Loyalists" in dom or "Champions & High-Value Loyalists" in dom),
    ("At-Risk / Lapsed Low-Value Customers", "At-Risk / Lapsed Low-Value Customers" in dom),
    ("Steady Core Repeaters", "Steady Core Repeaters" in dom),
    ("Across 5 customer segments", "Across 5 customer segments" in dom),
    ("Across 5 RFM clusters removed", "Across 5 RFM clusters" not in dom),
    ("Threshold: 0.50", "Threshold: 0.50" in dom or "Threshold: τ = 0.50" in dom),
    ("Target 0.50 removed", "Target 0.50" not in dom),
    ("Illustrative Retention Action (Demonstration)", "Illustrative Retention Action (Demonstration)" in dom),
    ("Low Risk in chart", "Low Risk" in dom),
    ("Moderate Risk in chart", "Moderate Risk" in dom),
    ("High Risk in chart", "High Risk" in dom),
]

all_passed = True
for name, passed in checks:
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_passed = False
    print(f"  [{status}] {name}")

print(f"\nDOM checks overall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")

print("\n3. Capturing updated screenshots at all 4 viewports...")
for filename, width, height in viewports:
    output_path = os.path.join(OUTPUT_DIR, filename)
    chrome_args = [
        CHROME_PATH,
        "--headless=new",
        f"--window-size={width},{height}",
        f"--screenshot={output_path}",
        "--virtual-time-budget=6000",
        "--hide-scrollbars",
        "--disable-gpu",
        "--no-sandbox",
        "http://localhost:5173",
    ]
    print(f"Capturing {filename} at {width}x{height}...")
    result = subprocess.run(chrome_args, capture_output=True, timeout=15)
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f"  Success: {filename} ({os.path.getsize(output_path)} bytes)")
    else:
        print(f"  Failed: {filename}, returncode={result.returncode}, stderr={result.stderr}")

print("\nVerification and screenshot capture complete.")
