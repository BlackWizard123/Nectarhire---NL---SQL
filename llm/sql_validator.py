import sqlglot
from sqlglot import expressions as exp

SCHEMA = {
    "employees": ["employee_id", "first_name", "last_name", "email", "phone", "date_of_birth",
                  "gender", "hire_date", "employment_type", "status", "department_id", "role_id",
                  "domain", "years_experience", "salary", "location"],
    "departments": ["department_id", "name"],
    "roles": ["role_id", "name", "description"],
    "skills": ["skill_id", "name"],
    "employee_skills": ["employee_id", "skill_id", "proficiency"],
    "projects": ["project_id", "name", "domain", "description"],
    "employee_projects": ["employee_id", "project_id", "role", "contribution"],
}

ALLOWED_TABLES = set(SCHEMA.keys())

FORBIDDEN_KEYWORDS = ["DELETE", "UPDATE", "INSERT", "DROP", "ALTER", "TRUNCATE", "CREATE"]

def validate_sql(sql: str):
    sql_upper = sql.upper()

    # 1. Block dangerous keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_upper:
            return False, f"Forbidden operation detected: {keyword}"
    
    # 2. Parse SQL
    try:
        ast = sqlglot.parse_one(sql)
    except Exception as e:
        return False, f"SQL parsing error: {str(e)}"
    
     # Helper
    def safe_name(x):
        if x is None:
            return None
        if isinstance(x, str):
            return x.lower()
        if hasattr(x, "this"):
            return str(x.this).lower()
        return str(x).lower()

    # 3. Validate tables 
    real_tables = set()

    for t in ast.find_all(exp.Table):
        table_name = safe_name(t.this)
        if table_name in ALLOWED_TABLES:
            real_tables.add(table_name)

    for t in real_tables:
        if t not in ALLOWED_TABLES:
            return False, f"Unknown table: {t}"
    
    # 4. Validate columns 
    valid_columns = set()
    for table in real_tables:
        valid_columns.update([c.lower() for c in SCHEMA[table]])

    for col in ast.find_all(exp.Column):
        column_name = col.name.lower()  # ignore alias/table prefix

        if column_name not in valid_columns and column_name != '*':
            return False, f"Unknown column: {column_name}"
    
    return True, "OK"
