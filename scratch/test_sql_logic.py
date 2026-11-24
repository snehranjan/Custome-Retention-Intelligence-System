import re

pg_defs = [
    "CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])))",
    "CHECK (((status)::text = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])))",
    "CHECK (status IN ('INVITED', 'PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED'))",
    "CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text, 'EXTRA'::text])))",
    "CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text])))",
]

for d in pg_defs:
    literals = re.findall(r"'([^']+)'", d)
    expected = {'INVITED', 'PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED'}
    found_statuses = set(literals)
    is_exact = (found_statuses == expected)
    print(f"Def: {d}\n  Literals: {literals} -> Exact Match: {is_exact}\n")
