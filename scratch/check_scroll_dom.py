import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

args = [
    CHROME_PATH,
    "--headless=new",
    "--dump-dom",
    "--no-sandbox",
    "--disable-gpu",
    "http://localhost:5173/#platform"
]

res = subprocess.run(args, capture_output=True, text=True, timeout=10)
print("DOM has 'Everything You Need':", "Everything You Need" in res.stdout)
print("DOM has 'AI-Powered Churn Prediction':", "AI-Powered Churn Prediction" in res.stdout)
print("DOM length:", len(res.stdout))
