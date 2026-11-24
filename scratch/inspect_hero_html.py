import subprocess
import time

args = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "--headless=new",
    "--dump-dom",
    "--no-sandbox",
    "--disable-gpu",
    "http://localhost:5173"
]

proc = subprocess.Popen(
    ["cmd.exe", "/c", "npm", "run", "preview", "--", "--port", "5173", "--host", "0.0.0.0"],
    cwd="frontend",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(3)

try:
    res = subprocess.run(args, capture_output=True, text=True, timeout=10)
    html = res.stdout
    # find HeroContent
    idx = html.find("Predict Customer Churn")
    if idx != -1:
        start = max(0, idx - 400)
        end = min(len(html), idx + 2000)
        print("HERO CONTENT HTML:\n", html[start:end])
    else:
        print("Not found!")
finally:
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except:
        proc.kill()
