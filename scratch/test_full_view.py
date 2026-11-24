import subprocess
import os

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_FILE = os.path.abspath(r"reports\phase8\screenshots\platform_overview_full.png")

chrome_args = [
    CHROME_PATH,
    "--headless=new",
    "--window-size=1440,2200",
    f"--screenshot={OUTPUT_FILE}",
    "--virtual-time-budget=6000",
    "--hide-scrollbars",
    "--disable-gpu",
    "--no-sandbox",
    "http://localhost:5173",
]

res = subprocess.run(chrome_args, capture_output=True, timeout=15)
print("Returncode:", res.returncode)
if os.path.exists(OUTPUT_FILE):
    print("Full overview size:", os.path.getsize(OUTPUT_FILE))
