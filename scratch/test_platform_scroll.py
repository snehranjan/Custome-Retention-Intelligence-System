import subprocess
import os

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_FILE = os.path.abspath(r"reports\phase8\screenshots\test_platform_scroll.png")

chrome_args = [
    CHROME_PATH,
    "--headless=new",
    "--window-size=1440,1080",
    f"--screenshot={OUTPUT_FILE}",
    "--virtual-time-budget=6000",
    "--hide-scrollbars",
    "--disable-gpu",
    "--no-sandbox",
    "http://localhost:5173/#platform",
]

res = subprocess.run(chrome_args, capture_output=True, timeout=15)
print("Returncode:", res.returncode)
if os.path.exists(OUTPUT_FILE):
    print("Size:", os.path.getsize(OUTPUT_FILE))
