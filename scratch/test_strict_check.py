import re

def strict_validate_status_check(raw_def):
    # Normalize multiple whitespace to single space
    s = re.sub(r'\s+', ' ', raw_def.strip())
    
    # 1. Banned logic keywords
    banned = r'\b(OR|AND|NOT|TRUE|FALSE|IS\s+NULL|LIKE|ILIKE|CASE|WHEN|COALESCE|NULLIF)\b'
    if re.search(banned, s, re.IGNORECASE):
        return False, "Contains forbidden logical operator or permissive keyword"
        
    # 2. Strict AST structure:
    # Must start with CHECK ((status = ANY (ARRAY[
    # and end with ])))
    # Allowing optional (status)::text and ::text on array elements
    struct_pattern = r"^CHECK \(\(\(?status\)?(?:::text)? = ANY \(ARRAY\[(?P<elements>[^\]]+)\]\)\)\)$"
    m = re.match(struct_pattern, s)
    if not m:
        return False, "Failed strict structural AST match (not a single status = ANY (ARRAY[...]) check)"
        
    elements_str = m.group("elements").strip()
    
    # 3. Parse elements: must be strictly comma-separated quoted identifiers with optional ::text
    # Reject any complex expressions, nested arrays, arithmetic, or non-identifier tokens
    raw_elements = [e.strip() for e in elements_str.split(',')]
    
    parsed_statuses = []
    for elem in raw_elements:
        elem_m = re.match(r"^'([A-Z_]+)'(?:::text)?$", elem)
        if not elem_m:
            return False, f"Invalid or non-literal element in status ARRAY: {elem}"
        parsed_statuses.append(elem_m.group(1))
        
    # 4. Check for duplicates
    if len(parsed_statuses) != len(set(parsed_statuses)):
        return False, f"Duplicate status literals found in ARRAY: {parsed_statuses}"
        
    # 5. Check exact set match
    expected = {'APPROVED', 'INVITED', 'PENDING', 'REJECTED', 'SUSPENDED'}
    if set(parsed_statuses) != expected:
        return False, f"Statuses set mismatch. Expected {expected}, got {set(parsed_statuses)}"
        
    # 6. Verify total count is exactly 5
    if len(parsed_statuses) != 5:
        return False, f"Expected exactly 5 statuses, found {len(parsed_statuses)}"
        
    return True, "Valid"

# Test cases
test_cases = [
    # Canonical PostgreSQL deparsed form:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])))", True),
    # Alphabetical order:
    ("CHECK ((status = ANY (ARRAY['APPROVED'::text, 'INVITED'::text, 'PENDING'::text, 'REJECTED'::text, 'SUSPENDED'::text])))", True),
    # Without ::text:
    ("CHECK ((status = ANY (ARRAY['INVITED', 'PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED'])))", True),
    # With (status)::text:
    ("CHECK (((status)::text = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])))", True),
    # Duplicate literal:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])))", False),
    # Additional status:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text, 'DELETED'::text])))", False),
    # Missing status:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text])))", False),
    # Unexpected status:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'UNKNOWN'::text])))", False),
    # Permissive OR:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])) OR (status IS NULL))", False),
    # Permissive AND:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])) AND (true))", False),
    # Permissive 1=1:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])) OR (1 = 1))", False),
    # Expression inside array:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, substr('PENDING', 1, 7)::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])))", False),
    # Nested array:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, ARRAY['PENDING'::text], 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text])))", False),
    # Arbitrary content:
    ("CHECK ((status = ANY (ARRAY['INVITED'::text, 'PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUSPENDED'::text, 1::text])))", False),
]

for test, expected in test_cases:
    ok, msg = strict_validate_status_check(test)
    assert ok == expected, f"Failed for:\n{test}\nExpected: {expected}, Got: {ok} ({msg})"
    print(f"PASS: {test[:60]}... -> {ok} ({msg})")

print("\nALL STRICT CHECK VALIDATOR TESTS PASSED!")
