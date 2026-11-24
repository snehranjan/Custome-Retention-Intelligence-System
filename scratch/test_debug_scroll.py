import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# In Chrome, we can dump DOM after evaluating a script or let's check
args = [
    CHROME_PATH,
    "--headless=new",
    "--window-size=1440,1080",
    "--screenshot=reports/phase8/screenshots/debug_scroll.png",
    "--virtual-time-budget=4000",
    "--no-sandbox",
    "--disable-gpu",
    "http://localhost:5173/#platform"
]
res = subprocess.run(args, capture_output=True, text=True, timeout=10)
print("Code:", res.returncode)
