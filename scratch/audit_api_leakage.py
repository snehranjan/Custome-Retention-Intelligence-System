import os
import re
import subprocess

print("=== 1. SCANNING FRONTEND COMPILED BUNDLE (frontend/dist) ===")
dist_dir = "frontend/dist"
dist_findings = []

secret_patterns = [
    (r"service_role", "Supabase Service Role keyword"),
    (r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+", "Hardcoded JWT / Service Role Token"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API key pattern"),
    (r"AIza[0-9A-Za-z-_]{35}", "Google API key pattern"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"postgres(?:ql)?:\/\/[^\s\'\"]+", "Database Connection String"),
    (r"SUPABASE_SERVICE_ROLE_KEY", "Supabase Service Role Key Ref"),
]

if os.path.exists(dist_dir):
    for root, dirs, files in os.walk(dist_dir):
        for f in files:
            fp = os.path.join(root, f)
            with open(fp, "r", encoding="utf-8", errors="ignore") as s:
                content = s.read()
                for pat, desc in secret_patterns:
                    matches = re.findall(pat, content, re.I)
                    if matches:
                        dist_findings.append((fp, desc, matches[:3]))
else:
    print("Dist directory not found")

print(f"Dist findings: {len(dist_findings)}")
for fp, desc, m in dist_findings:
    print(f"  [ALERT] {fp} - {desc}: {m}")

print("\n=== 2. SCANNING FRONTEND SOURCE (frontend/src) ===")
src_findings = []
for root, dirs, files in os.walk("frontend/src"):
    for f in files:
        if f.endswith((".js", ".jsx", ".ts", ".tsx", ".json", ".html")):
            fp = os.path.join(root, f)
            with open(fp, "r", encoding="utf-8", errors="ignore") as s:
                content = s.read()
                for pat, desc in secret_patterns:
                    matches = re.findall(pat, content, re.I)
                    # Filter out benign mock/placeholder matches in comments
                    real_matches = [m for m in matches if "placeholder" not in str(m).lower() and "example" not in str(m).lower()]
                    if real_matches:
                        src_findings.append((fp, desc, real_matches[:3]))

print(f"Src findings: {len(src_findings)}")
for fp, desc, m in src_findings:
    print(f"  [ALERT] {fp} - {desc}: {m}")

print("\n=== 3. CHECKING GIT TRACKED FILES FOR .ENV OR SECRETS ===")
tracked_files = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
env_tracked = [f for f in tracked_files if ".env" in f]
print("Tracked .env files in Git:", env_tracked)

print("\n=== 4. CHECKING COMMITTED ENVIRONMENT TEMPLATES ===")
for ef in env_tracked:
    with open(ef, "r", encoding="utf-8", errors="ignore") as fp:
        lines = fp.readlines()
        filled = [l.strip() for l in lines if "=" in l and not l.strip().startswith("#") and len(l.split("=", 1)[1].strip()) > 0]
        print(f"  {ef}: {len(filled)} non-empty variable assignments:")
        for line in filled:
            # Mask potential secrets
            k, v = line.split("=", 1)
            print(f"    {k} = {v}")

print("\n=== 5. CHECKING FRONTEND API CLIENT BASE URL RESOLUTION ===")
api_client_path = "frontend/src/lib/apiClient.js"
if os.path.exists(api_client_path):
    with open(api_client_path, "r", encoding="utf-8") as fp:
        lines = [line.strip() for line in fp.readlines() if "API_BASE_URL" in line or "VITE_" in line]
        for l in lines:
            print("  ", l)

print("\n=== 6. CHECKING SUPABASE CLIENT KEYS IN FRONTEND ===")
supabase_client_path = "frontend/src/lib/supabase.js"
if os.path.exists(supabase_client_path):
    with open(supabase_client_path, "r", encoding="utf-8") as fp:
        lines = [line.strip() for line in fp.readlines() if "supabase" in line.lower() or "key" in line.lower() or "vite_" in line.lower()]
        for l in lines:
            print("  ", l)
