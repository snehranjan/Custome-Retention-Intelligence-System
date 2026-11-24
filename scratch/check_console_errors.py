import subprocess
import json

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

args = [
    CHROME_PATH,
    "--headless=new",
    "--enable-logging=stderr",
    "--v=1",
    "--no-sandbox",
    "--disable-gpu",
    "http://localhost:5173"
]

res = subprocess.run(args, capture_output=True, text=True, timeout=10)
print("STDERR length:", len(res.stderr))
print("Any JS exception in stderr:")
for line in res.stderr.splitlines():
    if any(k in line.lower() for k in ["error", "exception", "failed", "warning"]):
        print("  ", line)
