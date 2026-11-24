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

frag = get_auth_fragment("analyst@retainiq.internal")

tabs = [
    ("customers", "Customer Directory"),
    ("predictions", "Churn Predictions"),
    ("recommendations", "Retention Actions"),
]

for tab_id, name in tabs:
    p = rf"C:\customer churn retention system\scratch\test_tab_{tab_id}_dark.png"
    target_url = f"http://127.0.0.1:5173/employee/dashboard?theme=dark#{frag}"
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--screenshot={p}",
        "--window-size=1440,900",
        "--virtual-time-budget=10000",
        "--hide-scrollbars",
        target_url
    ]
    # We can inject JS or navigate
    subprocess.run(cmd)

print("Tabs captured")
