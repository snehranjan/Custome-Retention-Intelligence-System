import os

SCREENSHOT_DIR = r"C:\customer churn retention system\reports\phase8\screenshots"
files = sorted([f for f in os.listdir(SCREENSHOT_DIR) if f.endswith(('.png', '.jpg', '.jpeg', '.webp'))])

print(f"Total screenshots in reports/phase8/screenshots: {len(files)}")
for f in files:
    sz = os.path.getsize(os.path.join(SCREENSHOT_DIR, f))
    print(f"  {f} ({sz:,} bytes)")
