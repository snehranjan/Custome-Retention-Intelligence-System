import os
import re

files_with_slate = []
for dp, dn, filenames in os.walk('frontend/src'):
    for f in filenames:
        if f.endswith('.jsx'):
            p = os.path.join(dp, f)
            text = open(p, encoding='utf-8').read()
            matches = re.findall(r'(bg-slate-[^\s"\']+|bg-white[^\s"\']*|text-slate-[^\s"\']+|border-slate-[^\s"\']+)', text)
            if matches:
                files_with_slate.append((f, set(matches)))

for f, matches in sorted(files_with_slate):
    print(f"{f}: {sorted(matches)}")
