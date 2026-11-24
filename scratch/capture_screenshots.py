import os
import subprocess
import time

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCREENSHOT_DIR = r"c:\customer churn retention system\reports\phase8\screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

targets = [
    # (name, url, width, height)
    ("landing_1440x900", "http://127.0.0.1:5173/", 1440, 900),
    ("landing_1024x768", "http://127.0.0.1:5173/", 1024, 768),
    ("landing_768x1024", "http://127.0.0.1:5173/", 768, 1024),
    ("landing_390x844", "http://127.0.0.1:5173/", 390, 844),
    ("login_1440x900", "http://127.0.0.1:5173/employee/login", 1440, 900),
    ("login_390x844", "http://127.0.0.1:5173/employee/login", 390, 844),
    ("employee_guard_1440x900", "http://127.0.0.1:5173/employee/dashboard", 1440, 900),
    ("admin_guard_1440x900", "http://127.0.0.1:5173/admin", 1440, 900),
    ("admin_guard_390x844", "http://127.0.0.1:5173/admin", 390, 844),
    ("not_found_1440x900", "http://127.0.0.1:5173/nonexistent-route", 1440, 900),
]

for name, url, w, h in targets:
    out_path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--screenshot={out_path}",
        f"--window-size={w},{h}",
        "--virtual-time-budget=4000",
        "--hide-scrollbars",
        url
    ]
    print(f"Capturing {name} ({w}x{h})...")
    res = subprocess.run(cmd, capture_output=True, timeout=30)
    exists = os.path.exists(out_path)
    size = os.path.getsize(out_path) if exists else 0
    print(f"  -> {'SUCCESS' if exists and size > 0 else 'FAILED'}: {out_path} ({size} bytes)")
