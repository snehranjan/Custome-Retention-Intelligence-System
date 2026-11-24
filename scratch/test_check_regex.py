import re

def validate_status_check(raw_def):
    # Normalize multiple whitespace to single space
    s = re.sub(r'\s+', ' ', raw_def.strip())
    
    # 1. Structural regex: must be strictly CHECK ((status = ANY (ARRAY[...])))
    # allowing optional casts like (status)::text or ::text on elements
    pattern = r"^CHECK \(\(\(?status\)?(?:::text)? = ANY \(ARRAY\[(.*?)\]\)\)\)$"
    m = re.match(pattern, s)
    if not m:
        return False, f"Does not match strict structural pattern: {s}"
    
    array_content = m.group(1).strip()
    
    # Extract each element in the array
    # Each element must be 'VALUE'::text or 'VALUE'
    elements = [e.strip() for e in array_content.split(',')]
    extracted_values = []
    for elem in elements:
        elem_m = re.match(r"^'([A-Z_]+)'(?:::text)?$", elem)
        if not elem_m:
            return False, f"Invalid array element format: {elem}"
        extracted_values.append(elem_m.group(1))
    
    # Check exact set
    expected = {'APPROVED', 'INVITED', 'PENDING', 'REJECTED', 'SUSPENDED'}
    if set(extracted_values) != expected or len(extracted_values) != 5:
        return False, f"Statuses do not match exact expected set: {extracted_values}"
        
    return True, "Valid"

test_cases = [
    # Canonical PostgreSQL deparsed form from migration 008:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])))", True),
    # Alphabetical order:
    ("CHECK ((status = ANY (ARRAY['APPROVED'::text, 'INVITED'::text, 'PENDING'::text, 'REJECTED'::text, 'SUSPENDED'::text])))", True),
    # Extra status:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text, 'DELETED'::text])))", False),
    # Missing status:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text])))", False),
    # Permissive OR:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])) OR (status IS NULL))", False),
    # Permissive 1=1:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])) OR (1 = 1))", False),
    # Substring injection:
    ("CHECK (status LIKE 'INV%')", False),
]

for test, expected_valid in test_cases:
    valid, reason = validate_status_check(test)
    assert valid == expected_valid, f"Failed for '{test}': expected {expected_valid}, got {valid} ({reason})"
    print(f"PASS: {test[:60]}... -> {valid} ({reason})")

print("\nAll check constraint test cases passed!")
