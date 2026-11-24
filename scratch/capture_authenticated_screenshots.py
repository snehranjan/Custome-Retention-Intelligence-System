import os
import sys
sys.path.insert(0, ".")
import subprocess
import httpx
from urllib.parse import urlparse
from backend.app.core.config import settings

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCREENSHOT_DIR = r"c:\customer churn retention system\reports\phase8\screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

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
    resp = httpx.post(url, json=body, headers=headers, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"generate_link failed: {resp.status_code} {resp.text}")
    
    action_link = resp.json()["action_link"]
    resp2 = httpx.get(action_link, follow_redirects=False, timeout=10)
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

# 1. Admin Portal Authenticated Captures
print("Fetching admin auth token for admin@retainiq.internal...")
admin_fragment = get_auth_fragment("admin@retainiq.internal")
print(f"Admin fragment obtained (len={len(admin_fragment)})")

for vp_name, w, h in viewports:
    out_file = os.path.join(SCREENSHOT_DIR, f"admin_authenticated_{vp_name}.png")
    target_url = f"http://127.0.0.1:5173/admin#{admin_fragment}"
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--screenshot={out_file}",
        f"--window-size={w},{h}",
        "--virtual-time-budget=6000",
        "--hide-scrollbars",
        target_url
    ]
    print(f"Capturing Admin Portal ({vp_name})...")
    res = subprocess.run(cmd, capture_output=True, timeout=30)
    exists = os.path.exists(out_file)
    sz = os.path.getsize(out_file) if exists else 0
    print(f"  -> {'SUCCESS' if exists and sz > 0 else 'FAILED'}: {out_file} ({sz} bytes)")

# 2. Employee Dashboard Authenticated Captures
print("\nFetching employee auth token for analyst@retainiq.internal...")
employee_fragment = get_auth_fragment("analyst@retainiq.internal")
print(f"Employee fragment obtained (len={len(employee_fragment)})")

for vp_name, w, h in viewports:
    out_file = os.path.join(SCREENSHOT_DIR, f"employee_authenticated_{vp_name}.png")
    target_url = f"http://127.0.0.1:5173/employee/dashboard#{employee_fragment}"
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--screenshot={out_file}",
        f"--window-size={w},{h}",
        "--virtual-time-budget=6000",
        "--hide-scrollbars",
        target_url
    ]
    print(f"Capturing Employee Portal ({vp_name})...")
    res = subprocess.run(cmd, capture_output=True, timeout=30)
    exists = os.path.exists(out_file)
    sz = os.path.getsize(out_file) if exists else 0
    print(f"  -> {'SUCCESS' if exists and sz > 0 else 'FAILED'}: {out_file} ({sz} bytes)")
