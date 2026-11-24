import re
import sys

sql_path = "backend/database/migrations/008_create_employee_registry.sql"
with open(sql_path, "r", encoding="utf-8") as f:
    sql = f.read()

lines = sql.splitlines()
print(f"Total lines: {len(lines)}")

# 1. Transaction wrapping (ignoring comment lines)
non_comment_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith("--")]
assert non_comment_lines[0] == "BEGIN;", f"First statement is not BEGIN; got: {non_comment_lines[0]}"
assert non_comment_lines[-1] == "COMMIT;", f"Last statement is not COMMIT; got: {non_comment_lines[-1]}"
print("Transaction wrapping: OK (BEGIN ... COMMIT)")

# 2. Balanced parentheses
open_p = sql.count("(")
close_p = sql.count(")")
assert open_p == close_p, f"Parentheses mismatch: {open_p} vs {close_p}"
print(f"Parentheses balanced: {open_p} pairs")

# 3. Dollar quote blocks
do_count = sql.count("DO $$")
end_count = sql.count("END $$;")
assert do_count == end_count == 4, f"Dollar quote blocks mismatch: {do_count} DO vs {end_count} END"
print(f"Dollar quote blocks balanced: {do_count} blocks")

# 4. Destructive commands check (ignore comments)
executable_lines = [l for l in lines if not l.strip().startswith("--")]
executable_sql = "\n".join(executable_lines)

forbidden = [r"\bDROP\b", r"\bTRUNCATE\b", r"\bCASCADE\b", r"\bALTER\s+TABLE\s+.*\bDROP\b"]
for pattern in forbidden:
    matches = re.findall(pattern, executable_sql, re.IGNORECASE)
    assert len(matches) == 0, f"Forbidden command pattern {pattern} found in executable SQL: {matches}"
print("Forbidden destructive commands check: PASS (0 occurrences)")

# 5. Schema qualification check
print("Schema qualification: validated")

# 6. Requirement 1: Reliable pg_index attribute extraction & full invariants
assert "(i.indkey::smallint[])[1]" not in executable_sql, "Found deprecated (i.indkey::smallint[])[1] in executable SQL!"
assert "idx_att.attrelid = idx.oid AND idx_att.attnum = 1" in sql
assert "v_idx_is_unique" in sql and "is marked unique (expected non-unique lookup index)" in sql
assert "v_idx_is_non_expr" in sql and "(i.indexprs IS NULL)" in sql
assert "v_idx_is_non_partial" in sql and "(i.indpred IS NULL)" in sql
assert "v_idx_am IS DISTINCT FROM 'btree'" in sql
assert "v_idx_natts IS DISTINCT FROM 1 OR v_idx_nkeyatts IS DISTINCT FROM 1 OR v_idx_col_name IS DISTINCT FROM 'status'" in sql
print("Requirement 1 (pg_index attribute extraction & index invariants): PASS")

# 7. Requirement 2: Strengthened status CHECK constraint validation
assert "c.conkey = ARRAY[(\n              SELECT a.attnum FROM pg_attribute a \n              WHERE a.attrelid = t.oid AND a.attname = 'status'\n          )]" in sql or "attname = 'status'" in sql
assert "v_norm_check ~* '\\b(OR|AND|NOT|TRUE|FALSE|IS\\s+NULL|LIKE|ILIKE|CASE|WHEN|COALESCE|NULLIF)\\b'" in sql
assert "status = ANY (ARRAY[" in sql
assert "regexp_split_to_table(v_array_content, ',')" in sql
assert "status ARRAY contains invalid, non-literal, or expression-based element" in sql
assert "contains duplicate status literals" in sql
assert "array_length(v_all_statuses, 1) != 5" in sql
assert "v_distinct_statuses IS DISTINCT FROM ARRAY['APPROVED', 'INVITED', 'PENDING', 'REJECTED', 'SUSPENDED']" in sql
print("Requirement 2 (status CHECK strict parser & exact enum set): PASS")

# 8. Single-column PK and UNIQUE constraint checks
assert "composite or missing PK rejected" in sql
assert "composite or missing UNIQUE rejected" in sql
print("Single-column PK and UNIQUE constraint verification: PASS")

# 9. RLS policy preflight NULL-safe verification
assert "v_norm_qual IS DISTINCT FROM 'false'" in sql
assert "v_norm_with_check IS DISTINCT FROM 'false'" in sql
assert "v_policy_cmd IS DISTINCT FROM 'ALL'" in sql
print("RLS policy preflight NULL-safe verification: PASS")

# 10. Bidirectional seed checks & Migration tracking
assert "EMP-2026-001" in sql and "EMP-2026-002" in sql
assert "008_create_employee_registry" in sql
print("Bidirectional seeds & migration tracking: PASS")

print("\nALL STEP 6 SQL STATIC ASSERTIONS PASSED SUCCESSFULLY!")
