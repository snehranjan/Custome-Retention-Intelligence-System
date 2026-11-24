import subprocess

cmd = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "--headless=new",
    "--dump-dom",
    "http://127.0.0.1:5173/?theme=dark",
]
res = subprocess.run(cmd, capture_output=True)
out = res.stdout.decode("utf-8", errors="ignore")
print("First 300 chars:")
print(out[:300])

idx = out.find("<html")
idx_end = out.find(">", idx)
print("HTML opening tag:", out[idx:idx_end+1])

idx_body = out.find("<body")
idx_body_end = out.find(">", idx_body)
print("BODY opening tag:", out[idx_body:idx_body_end+1])

print("\nDoes out have 'dark' in html class?", "class=\"scroll-smooth dark\"" in out or "dark" in out[idx:idx_end+1])
