import os
import re

color_classes = set()
class_pattern = re.compile(r'className=["\']([^"\']+)["\']')

for dp, dn, filenames in os.walk('frontend/src'):
    for f in filenames:
        if f.endswith('.jsx'):
            path = os.path.join(dp, f)
            content = open(path, encoding='utf-8').read()
            for match in class_pattern.finditer(content):
                classes = match.group(1).split()
                for c in classes:
                    if any(c.startswith(prefix) for prefix in ['bg-', 'text-', 'border-']):
                        color_classes.add(c)

print(f"Total color utility classes found: {len(color_classes)}")
print("\nTop 50 bg- classes:")
print(sorted([c for c in color_classes if c.startswith('bg-')])[:50])
print("\nTop 50 text- classes:")
print(sorted([c for c in color_classes if c.startswith('text-')])[:50])
print("\nTop 50 border- classes:")
print(sorted([c for c in color_classes if c.startswith('border-')])[:50])
