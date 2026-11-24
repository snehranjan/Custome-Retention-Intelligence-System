import os
import sys
sys.path.insert(0, os.path.abspath("."))
import time
import subprocess
import glob
import httpx
from backend.app.core.config import settings

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCREENSHOT_DIR = r"C:\customer churn retention system\reports\phase8\screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Clean up test artifacts
for test_img in glob.glob(os.path.join(SCREENSHOT_DIR, "test_*.png")):
    try:
        os.remove(test_img)
    except Exception:
        pass

def get_auth_fragment(email: str) -> str:
    url = f"{settings.SUPABASE_URL}/auth/v1/admin/generate_link"
    headers = {
        "apikey": settings.SUPABASE_SECRET_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SECRET_KEY}",
    }
    body = {
        "type": "magiclink",
        "email": email,
    }
    resp = httpx.post(url, json=body, headers=headers, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"generate_link failed: {resp.status_code} {resp.text}")
    
    action_link = resp.json()["action_link"]
    resp2 = httpx.get(action_link, follow_redirects=False, timeout=15)
    loc = resp2.headers.get("Location")
    if not loc or "#" not in loc:
        raise RuntimeError(f"Location header missing fragment: {loc}")
    
    return loc[loc.index("#") + 1:]

viewports = [
    ("1440x900", 1440, 900),
    ("1024x768", 1024, 768),
    ("768x1024", 768, 1024),
    ("390x844", 390, 844),
]

themes = ["light", "dark"]

results = []

def capture(url, out_path, w, h, budget_ms=8000):
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--screenshot={out_path}",
        f"--window-size={w},{h}",
        f"--virtual-time-budget={budget_ms}",
        "--hide-scrollbars",
        url
    ]
    res = subprocess.run(cmd, capture_output=True, timeout=40)
    exists = os.path.exists(out_path)
    sz = os.path.getsize(out_path) if exists else 0
    return exists, sz

# 1. Public Landing Page Captures (Light & Dark)
print("=== 1. Capturing Public Website (Landing Page) ===")
for theme in themes:
    for vp_name, w, h in viewports:
        out_file = os.path.join(SCREENSHOT_DIR, f"public_{theme}_{vp_name}.png")
        target_url = f"http://127.0.0.1:5173/?theme={theme}"
        ok, sz = capture(target_url, out_file, w, h, budget_ms=6000)
        status = "OK" if ok and sz > 10000 else "FAIL"
        print(f"  [{theme.upper()}] public_{theme}_{vp_name}.png -> {status} ({sz:,} bytes)")
        results.append((f"public_{theme}_{vp_name}.png", ok, sz))

# 2. Employee Portal Authenticated Captures (Light & Dark)
print("\n=== 2. Capturing Employee Portal (Authenticated) ===")
for theme in themes:
    print(f"Generating auth token for employee ({theme} mode)...")
    emp_fragment = get_auth_fragment("analyst@retainiq.internal")
    for vp_name, w, h in viewports:
        out_file = os.path.join(SCREENSHOT_DIR, f"employee_{theme}_{vp_name}.png")
        target_url = f"http://127.0.0.1:5173/employee/dashboard?theme={theme}#{emp_fragment}"
        ok, sz = capture(target_url, out_file, w, h, budget_ms=8000)
        status = "OK" if ok and sz > 10000 else "FAIL"
        print(f"  [{theme.upper()}] employee_{theme}_{vp_name}.png -> {status} ({sz:,} bytes)")
        results.append((f"employee_{theme}_{vp_name}.png", ok, sz))

# 3. Administrator Portal Authenticated Captures (Light & Dark)
print("\n=== 3. Capturing Administrator Portal (Authenticated) ===")
for theme in themes:
    print(f"Generating auth token for admin ({theme} mode)...")
    adm_fragment = get_auth_fragment("admin@retainiq.internal")
    for vp_name, w, h in viewports:
        out_file = os.path.join(SCREENSHOT_DIR, f"admin_{theme}_{vp_name}.png")
        target_url = f"http://127.0.0.1:5173/admin?theme={theme}#{adm_fragment}"
        ok, sz = capture(target_url, out_file, w, h, budget_ms=8000)
        status = "OK" if ok and sz > 10000 else "FAIL"
        print(f"  [{theme.upper()}] admin_{theme}_{vp_name}.png -> {status} ({sz:,} bytes)")
        results.append((f"admin_{theme}_{vp_name}.png", ok, sz))

print("\n=== SUMMARY ===")
total = len(results)
passed = sum(1 for _, ok, sz in results if ok and sz > 10000)
print(f"Total screenshots: {total}, Successfully captured: {passed}")
assert passed == 24, f"Expected 24 valid screenshots, got {passed}"
