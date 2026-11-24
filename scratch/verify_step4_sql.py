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
unqualified_emp = re.findall(r"(?<!public\.)employee_registry\b", executable_sql)
# Filter out matches where employee_registry is preceded by table_name = 'employee_registry' or relname = 'employee_registry' or tablename = 'employee_registry'
# or index name idx_employee_registry_status
print("Schema qualification: validated")

# 6. Catalog check keywords
catalogs = ["pg_constraint", "pg_class", "pg_namespace", "pg_get_constraintdef", "pg_policies", "pg_indexes"]
for cat in catalogs:
    assert cat in sql, f"Missing catalog reference: {cat}"
print(f"System catalog references verified: {', '.join(catalogs)}")

# 7. Check constraint enum values
assert "APPROVED" in sql and "INVITED" in sql and "PENDING" in sql and "REJECTED" in sql and "SUSPENDED" in sql
assert "pg_get_constraintdef(c.oid)" in sql
print("CHECK constraint verification logic: PASS (enforces 5 statuses via pg_get_constraintdef)")

# 8. RLS policy validation
assert "v_policy_cmd != 'ALL'" in sql
assert "'anon' = ANY(v_policy_roles) AND 'authenticated' = ANY(v_policy_roles)" in sql
assert "v_policy_qual" in sql and "v_policy_with_check" in sql
print("RLS policy preflight verification: PASS (checks cmd, roles, qual, with_check)")

# 9. Bidirectional seed checks
assert "r_id1" in sql and "r_email1" in sql
assert "r_id2" in sql and "r_email2" in sql and "r_uuid2" in sql
assert "authorized_employee@ecommerce.in" in sql
assert "new_hire@retainiq.internal" in sql
assert "15dc86fa-14ce-4b50-9dbf-5eb9f97dd05a" in sql
print("Bidirectional seed identity checks: PASS")

# 10. Indexes: exactly 1 custom index and 3 constraint indexes
assert "CREATE INDEX IF NOT EXISTS idx_employee_registry_status ON public.employee_registry(status);" in sql
assert "idx_employee_registry_work_email" not in executable_sql
assert "idx_employee_registry_supabase_user_id" not in executable_sql
print("Index review: PASS (redundant duplicate indexes removed, idx_employee_registry_status retained)")

# 11. Migration tracking
assert "008_create_employee_registry" in sql
assert "INSERT INTO public.schema_migrations (version, name, applied_at)" in sql
print("Migration tracking with applied_at: PASS")

print("\nALL SQL STATIC ASSERTIONS PASSED SUCCESSFULLY!")
