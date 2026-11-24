import re

def normalize_check_def(raw_def):
    # Strip CHECK and outer parens
    # Replace multiple spaces with single space
    s = raw_def.strip()
    # Normalize whitespace
    s = re.sub(r'\s+', ' ', s)
    # Remove all type casts like ::text, ::character varying, ::varchar
    s = re.sub(r'::[a-zA-Z_ ]+', '', s)
    # Remove extra parens around column name like ((status)::text) or ((status)) or (status)
    s = re.sub(r'\(+\s*status\s*\)+', 'status', s)
    # Normalize outer CHECK (...)
    s = re.sub(r'^CHECK\s*\(\s*\(?', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\)?\s*\)$', '', s)
    s = s.strip()
    return s

examples = [
    "CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])))",
    "CHECK (((status)::text = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])))",
    "CHECK (status = ANY (ARRAY['INVITED'::character varying, 'PENDING'::character varying, 'APPROVED'::character varying, 'REJECTED'::character varying, 'SUSPENDED'::character varying]))",
    "CHECK (status IN ('INVITED', 'PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED'))",
]

for ex in examples:
    print(f"Original: {ex}")
    norm = normalize_check_def(ex)
    print(f"Normalized: {norm}")
    
    # Check if matches standard forms:
    # 1. status = ANY (ARRAY['INVITED', 'PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED'])
    # 2. status IN ('INVITED', 'PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED')
    is_valid = (
        norm == "status = ANY (ARRAY['INVITED', 'PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED'])" or
        norm == "status IN ('INVITED', 'PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED')"
    )
    print(f"Matches standard exact definition: {is_valid}\n")
