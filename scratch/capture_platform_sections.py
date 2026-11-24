import subprocess
import os

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = os.path.abspath(r"reports\phase8\screenshots")

viewports = [
    ("platform_1440_desktop.png", 1440, 2900),
    ("platform_1024_laptop.png", 1024, 3100),
    ("platform_768_tablet.png", 768, 3900),
    ("platform_390_mobile.png", 390, 5400),
]

for filename, width, height in viewports:
    output_path = os.path.join(OUTPUT_DIR, filename)
    chrome_args = [
        CHROME_PATH,
        "--headless=new",
        f"--window-size={width},{height}",
        f"--screenshot={output_path}",
        "--virtual-time-budget=6000",
        "--hide-scrollbars",
        "--disable-gpu",
        "--no-sandbox",
        "http://localhost:5173",
    ]
    print(f"Capturing {filename} ({width}x{height})...")
    res = subprocess.run(chrome_args, capture_output=True, timeout=20)
    if os.path.exists(output_path):
        print(f"  Success: {filename} ({os.path.getsize(output_path)} bytes)")
