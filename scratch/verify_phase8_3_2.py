import subprocess
import time
import urllib.request
import os

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = os.path.abspath(r"reports\phase8\screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("1. Verifying dev server response...")
with urllib.request.urlopen("http://localhost:5173", timeout=5) as resp:
    print(f"Server alive with status {resp.status}")

print("\n2. Checking DOM elements for Phase 8.3.2...")
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
    ("Anchor id='platform'", 'id="platform"' in dom),
    ("Eyebrow: THE RETAINIQ PLATFORM", "THE RETAINIQ PLATFORM" in dom),
    ("Heading: Everything You Need to Understand Customer Retention", "Everything You Need to Understand Customer Retention" in dom),
    ("Subheading: From customer behaviour to smarter retention decisions.", "From customer behaviour to smarter retention decisions." in dom),
    ("Card 1: AI-Powered Churn Prediction", "AI-Powered Churn Prediction" in dom),
    ("Card 2: Intelligent Customer Segmentation", "Intelligent Customer Segmentation" in dom),
    ("Card 3: Retention Recommendations", "Retention Recommendations" in dom),
    ("Card 4: Actionable Customer Analytics", "Actionable Customer Analytics" in dom),
    ("Card 1: Illustrative Prediction Preview", "Illustrative Prediction Preview" in dom),
    ("Card 2: Champions & High-Value Loyalists", "Champions &amp; High-Value Loyalists" in dom or "Champions & High-Value Loyalists" in dom),
    ("Card 2: At-Risk / Lapsed Low-Value Customers", "At-Risk / Lapsed Low-Value Customers" in dom),
    ("Card 2: Zero Delivered-Purchase Customers", "Zero Delivered-Purchase Customers" in dom),
    ("Card 2: Steady Core Repeaters", "Steady Core Repeaters" in dom),
    ("Card 2: Recent Low-Ticket / New Promising Customers", "Recent Low-Ticket / New Promising Customers" in dom),
    ("Card 3: Illustrative Recommendation Preview", "Illustrative Recommendation Preview" in dom),
    ("Card 4: Illustrative Sample Data", "Illustrative Sample Data" in dom),
]

all_passed = True
for name, passed in checks:
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_passed = False
    print(f"  [{status}] {name}")

print(f"\nDOM Audit: {'ALL 16 CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")

print("\n3. Capturing Platform Highlights screenshots at 4 viewports...")
viewports = [
    ("platform_1440_desktop.png", 1440, 1080),
    ("platform_1024_laptop.png", 1024, 900),
    ("platform_768_tablet.png", 768, 1024),
    ("platform_390_mobile.png", 390, 844),
]

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
        "http://localhost:5173/#platform",
    ]
    print(f"Capturing {filename} ({width}x{height}) at #platform...")
    res = subprocess.run(chrome_args, capture_output=True, timeout=15)
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f"  Success: {filename} ({os.path.getsize(output_path)} bytes)")
    else:
        print(f"  Failed: {filename}")

print("\nVerification complete.")
