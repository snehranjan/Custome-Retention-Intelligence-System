import subprocess
import time
import urllib.request
import os

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = os.path.abspath(r"reports\phase8\screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("1. Checking server response...")
with urllib.request.urlopen("http://localhost:5173", timeout=5) as resp:
    print(f"Server alive: HTTP {resp.status}")

print("\n2. Inspecting DOM for backend risk tier alignment...")
args = [
    CHROME_PATH,
    "--headless=new",
    "--dump-dom",
    "--no-sandbox",
    "--disable-gpu",
    "http://localhost:5173"
]
res = subprocess.run(args, capture_output=True, text=True, timeout=15)
dom = res.stdout

# Look inside the Platform Highlights section
idx = dom.find('id="platform"')
platform_dom = dom[idx:] if idx != -1 else dom

checks = [
    ("Low Risk: p < 0.50", "p &lt; 0.50" in platform_dom or "p < 0.50" in platform_dom),
    ("Moderate Risk: 0.50 <= p < 0.70", "0.50 ≤ p &lt; 0.70" in platform_dom or "0.50 ≤ p < 0.70" in platform_dom),
    ("High Risk: p >= 0.70", "p ≥ 0.70" in platform_dom),
    ("0.35 eliminated from PlatformHighlights", "0.35" not in platform_dom),
    ("Model Decision Threshold: tau = 0.50", "Model Decision Threshold" in platform_dom and "τ = 0.50" in platform_dom),
    ("Illustrative Prediction Preview retained", "Illustrative Prediction Preview" in platform_dom),
]

all_passed = True
for name, passed in checks:
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_passed = False
    print(f"  [{status}] {name}")

print(f"\nAudit Result: {'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")

print("\n3. Capturing updated screenshots at 4 viewports...")
viewports = [
    ("platform_1440_desktop.png", 1440, 2900),
    ("platform_1024_laptop.png", 1024, 3100),
    ("platform_768_tablet.png", 768, 3900),
    ("platform_390_mobile.png", 390, 5400),
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
        "http://localhost:5173",
    ]
    print(f"Capturing {filename} ({width}x{height})...")
    r = subprocess.run(chrome_args, capture_output=True, timeout=20)
    if os.path.exists(output_path):
        print(f"  Success: {filename} ({os.path.getsize(output_path)} bytes)")

print("\nVerification complete.")
