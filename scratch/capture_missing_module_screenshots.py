import os
import sys
sys.path.insert(0, os.path.abspath("."))
import subprocess
import httpx
from backend.app.core.config import settings

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEST_DIR = r"C:\customer churn retention system\reports\phase8\screenshots"
os.makedirs(DEST_DIR, exist_ok=True)

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

print("Fetching auth tokens...")
emp_frag_light = get_auth_fragment("analyst@retainiq.internal")
emp_frag_dark = get_auth_fragment("analyst@retainiq.internal")
adm_frag_light = get_auth_fragment("admin@retainiq.internal")
adm_frag_dark = get_auth_fragment("admin@retainiq.internal")

targets = [
    # Employee Modules (Light & Dark)
    ("customers", "employee_customer_explorer_light.png", "light", f"http://127.0.0.1:5173/employee/dashboard?theme=light&tab=customers#{emp_frag_light}"),
    ("customers", "employee_customer_explorer_dark.png", "dark", f"http://127.0.0.1:5173/employee/dashboard?theme=dark&tab=customers#{emp_frag_dark}"),
    
    ("predictions", "employee_prediction_explorer_light.png", "light", f"http://127.0.0.1:5173/employee/dashboard?theme=light&tab=predictions#{emp_frag_light}"),
    ("predictions", "employee_prediction_explorer_dark.png", "dark", f"http://127.0.0.1:5173/employee/dashboard?theme=dark&tab=predictions#{emp_frag_dark}"),
    
    ("segments", "employee_segmentation_explorer_light.png", "light", f"http://127.0.0.1:5173/employee/dashboard?theme=light&tab=segments#{emp_frag_light}"),
    ("segments", "employee_segmentation_explorer_dark.png", "dark", f"http://127.0.0.1:5173/employee/dashboard?theme=dark&tab=segments#{emp_frag_dark}"),
    
    ("recommendations", "employee_recommendations_light.png", "light", f"http://127.0.0.1:5173/employee/dashboard?theme=light&tab=recommendations#{emp_frag_light}"),
    ("recommendations", "employee_recommendations_dark.png", "dark", f"http://127.0.0.1:5173/employee/dashboard?theme=dark&tab=recommendations#{emp_frag_dark}"),
    
    ("analytics", "employee_analytics_light.png", "light", f"http://127.0.0.1:5173/employee/dashboard?theme=light&tab=analytics#{emp_frag_light}"),
    ("analytics", "employee_analytics_dark.png", "dark", f"http://127.0.0.1:5173/employee/dashboard?theme=dark&tab=analytics#{emp_frag_dark}"),

    # Admin Modules (Light & Dark)
    ("directory", "admin_employee_management_light.png", "light", f"http://127.0.0.1:5173/admin?theme=light&tab=directory#{adm_frag_light}"),
    ("directory", "admin_employee_management_dark.png", "dark", f"http://127.0.0.1:5173/admin?theme=dark&tab=directory#{adm_frag_dark}"),
    
    ("requests", "admin_approval_workflow_light.png", "light", f"http://127.0.0.1:5173/admin?theme=light&tab=requests#{adm_frag_light}"),
    ("requests", "admin_approval_workflow_dark.png", "dark", f"http://127.0.0.1:5173/admin?theme=dark&tab=requests#{adm_frag_dark}"),
]

for tab, filename, theme, url in targets:
    p = os.path.join(DEST_DIR, filename)
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
