import json

with open("scratch/discovered_docs.json", "r", encoding="utf-8") as fp:
    docs = json.load(fp)

print("=== ALL DISCOVERED DOCUMENTATION FILES ===")
for rel, f, ext, sz in sorted(docs, key=lambda x: x[0]):
    print(f"{rel} | {sz} bytes")
