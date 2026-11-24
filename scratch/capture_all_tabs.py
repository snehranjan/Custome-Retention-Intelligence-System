import os
import sys
sys.path.insert(0, os.path.abspath("."))
import subprocess
import httpx
from backend.app.core.config import settings

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def get_auth_fragment(email: str) -> str:
    url = f"{settings.SUPABASE_URL}/auth/v1/admin/generate_link"
    headers = {
        "apikey": settings.SUPABASE_SECRET_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SECRET_KEY}",
    }
    body = {"type": "magiclink", "email": email}
    resp = httpx.post(url, json=body, headers=headers, timeout=15)
    action_link = resp.json()["action_link"]
    resp2 = httpx.get(action_link, follow_redirects=False, timeout=15)
    loc = resp2.headers.get("Location")
    return loc[loc.index("#") + 1:]

print("Getting auth fragments...")
emp_frag = get_auth_fragment("analyst@retainiq.internal")
adm_frag = get_auth_fragment("admin@retainiq.internal")

targets = [
    (f"http://127.0.0.1:5173/employee/dashboard?theme=dark&tab=customers#{emp_frag}", "test_tab_customers_dark.png"),
    (f"http://127.0.0.1:5173/employee/dashboard?theme=dark&tab=predictions#{emp_frag}", "test_tab_predictions_dark.png"),
    (f"http://127.0.0.1:5173/employee/dashboard?theme=dark&tab=recommendations#{emp_frag}", "test_tab_recommendations_dark.png"),
    (f"http://127.0.0.1:5173/admin?theme=dark&tab=directory#{adm_frag}", "test_admin_directory_dark.png"),
    (f"http://127.0.0.1:5173/admin?theme=dark&tab=requests#{adm_frag}", "test_admin_requests_dark.png"),
]

for url, filename in targets:
    p = os.path.join(r"C:\customer churn retention system\scratch", filename)
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--screenshot={p}",
        "--window-size=1440,900",
        "--virtual-time-budget=8000",
        "--hide-scrollbars",
        url
    ]
    subprocess.run(cmd)
    sz = os.path.getsize(p) if os.path.exists(p) else 0
    print(f"Captured {filename}: {sz:,} bytes")
