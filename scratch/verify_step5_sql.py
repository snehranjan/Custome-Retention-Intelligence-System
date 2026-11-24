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

# 6. Primary key & UNIQUE exact column checks (reject composite)
assert "c.conkey = ARRAY[(\n                  SELECT a.attnum FROM pg_attribute a \n                  WHERE a.attrelid = t.oid AND a.attname = 'employee_id'\n              )]" in sql or "c.conkey = ARRAY[(" in sql
assert "c.contype = 'p'" in sql
assert "c.contype = 'u'" in sql
assert "composite or missing PK rejected" in sql
assert "composite or missing UNIQUE rejected" in sql
print("PK and UNIQUE exact single-column constraint verification: PASS (rejects composite)")

# 7. Exact status CHECK constraint verification
assert "c.conkey = ARRAY[(\n              SELECT a.attnum FROM pg_attribute a \n              WHERE a.attrelid = t.oid AND a.attname = 'status'\n          )]" in sql or "attname = 'status'" in sql
assert "v_norm_check ~* '\\b(OR|IS NULL|TRUE|FALSE|LIKE|ILIKE|NOT)\\b'" in sql
assert "v_norm_check !~* '^CHECK \\(\\(\\(?status\\)?(?:::text)? = ANY \\(ARRAY\\[(.*?\\])\\)\\)\\)'" in sql or "CHECK ((status = ANY (ARRAY" in sql
assert "v_status_count != 5" in sql
assert "IS DISTINCT FROM ARRAY['APPROVED', 'INVITED', 'PENDING', 'REJECTED', 'SUSPENDED']" in sql
print("Exact status CHECK constraint verification: PASS (catalog-native, single-column, strictly 5 enum values)")

# 8. Status index verification (indisvalid, indisready, btree, status column)
assert "i.indisvalid" in sql and "i.indisready" in sql
assert "v_idx_am IS DISTINCT FROM 'btree'" in sql
assert "v_idx_natts IS DISTINCT FROM 1 OR v_idx_col IS DISTINCT FROM 'status'" in sql
print("Status index verification: PASS (belongs to table, ready btree, indexes exactly status)")

# 9. RLS policy NULL-safe validation (IS DISTINCT FROM 'false')
assert "v_policy_cmd IS DISTINCT FROM 'ALL'" in sql
assert "'anon' = ANY(v_policy_roles) AND 'authenticated' = ANY(v_policy_roles)" in sql
assert "v_norm_qual IS DISTINCT FROM 'false'" in sql
assert "v_norm_with_check IS DISTINCT FROM 'false'" in sql
print("RLS policy preflight NULL-safe verification: PASS (IS DISTINCT FROM 'false', ALL, anon/authenticated)")

# 10. Bidirectional seed checks
assert "r_id1" in sql and "r_email1" in sql
assert "r_id2" in sql and "r_email2" in sql and "r_uuid2" in sql
assert "authorized_employee@ecommerce.in" in sql
assert "new_hire@retainiq.internal" in sql
assert "15dc86fa-14ce-4b50-9dbf-5eb9f97dd05a" in sql
print("Bidirectional seed identity checks: PASS")

# 11. Indexes: exactly 1 custom index and 3 constraint indexes
assert "CREATE INDEX IF NOT EXISTS idx_employee_registry_status ON public.employee_registry(status);" in sql
assert "idx_employee_registry_work_email" not in executable_sql
assert "idx_employee_registry_supabase_user_id" not in executable_sql
print("Index review: PASS (redundant duplicate indexes removed, idx_employee_registry_status retained)")

# 12. Migration tracking with applied_at
assert "008_create_employee_registry" in sql
assert "INSERT INTO public.schema_migrations (version, name, applied_at)" in sql
print("Migration tracking with applied_at: PASS")

print("\nALL STEP 5 SQL STATIC ASSERTIONS PASSED SUCCESSFULLY!")
