import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
p = r"C:\customer churn retention system\scratch\test_dark_full_page.png"
cmd = [
    CHROME_PATH,
    "--headless=new",
    f"--screenshot={p}",
    "--window-size=1440,3000",
    "--virtual-time-budget=6000",
    "--hide-scrollbars",
    "http://127.0.0.1:5173/?theme=dark"
]
subprocess.run(cmd)
print("Captured full landing page dark")
