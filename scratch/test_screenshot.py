import subprocess
import time
import os

OUTPUT_FILE = os.path.abspath(r"reports\phase8\screenshots\test_desktop.png")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

proc = subprocess.Popen(
    ["cmd.exe", "/c", "npm", "run", "preview", "--", "--port", "5173", "--host", "0.0.0.0"],
    cwd="frontend",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(3)

try:
    chrome_args = [
        CHROME_PATH,
        "--headless=new",
        "--window-size=1440,1080",
        f"--screenshot={OUTPUT_FILE}",
        "--virtual-time-budget=3000",
        "--hide-scrollbars",
        "--disable-gpu",
        "--no-sandbox",
        "http://localhost:5173"
    ]
    res = subprocess.run(chrome_args, capture_output=True, timeout=15)
    print("Screenshot result code:", res.returncode)
    if os.path.exists(OUTPUT_FILE):
        print(f"File size: {os.path.getsize(OUTPUT_FILE)} bytes")
finally:
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except:
        proc.kill()
