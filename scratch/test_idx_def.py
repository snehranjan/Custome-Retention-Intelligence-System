import re

def check_index_def(indexdef):
    # Normalize whitespace
    s = re.sub(r'\s+', ' ', indexdef.strip())
    # Expected: CREATE INDEX idx_employee_registry_status ON public.employee_registry USING btree (status)
    expected = "CREATE INDEX idx_employee_registry_status ON public.employee_registry USING btree (status)"
    return s.lower() == expected.lower()

defs = [
    "CREATE INDEX idx_employee_registry_status ON public.employee_registry USING btree (status)",
    "CREATE INDEX idx_employee_registry_status ON public.employee_registry USING btree (status, created_at)",
    "CREATE INDEX idx_employee_registry_status ON public.employee_registry USING hash (status)",
]

for d in defs:
    print(d, "->", check_index_def(d))
