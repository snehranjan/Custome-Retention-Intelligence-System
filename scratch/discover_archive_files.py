import os
import json

WORKSPACE = r"C:\customer churn retention system"
EXCLUDE_DIRS = {
    "node_modules", ".venv", ".git", ".gemini", "dist", ".system_generated",
    "RETAINIQ_PROJECT_ARCHIVE", "__pycache__", ".pytest_cache"
}

doc_files = []
img_files = []

for root, dirs, files in os.walk(WORKSPACE):
    # prune excluded dirs
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
    
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        full_path = os.path.join(root, f)
        rel_path = os.path.relpath(full_path, WORKSPACE)
        
        if ext in [".md", ".markdown", ".txt"]:
            # Exclude requirements.txt or test output files if not documentation
            doc_files.append((rel_path, f, ext, os.path.getsize(full_path)))
        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            img_files.append((rel_path, f, ext, os.path.getsize(full_path)))

print(f"Total doc files found: {len(doc_files)}")
print(f"Total img files found: {len(img_files)}")

with open("scratch/discovered_docs.json", "w", encoding="utf-8") as fp:
    json.dump(doc_files, fp, indent=2)

with open("scratch/discovered_imgs.json", "w", encoding="utf-8") as fp:
    json.dump(img_files, fp, indent=2)

print("\nSample doc files:")
for rel, f, ext, sz in doc_files[:30]:
    print(f"  {rel} ({sz:,} bytes)")

print("\nSample img files:")
for rel, f, ext, sz in img_files[:30]:
    print(f"  {rel} ({sz:,} bytes)")
