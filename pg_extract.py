# pg_extract.py
import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from datetime import date, datetime
from decimal import Decimal

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]

    # Convert date/datetime to string
    elif isinstance(obj, (date, datetime)):
        return obj.isoformat()

    # Convert Decimal → float
    elif isinstance(obj, Decimal):
        return float(obj)

    # Convert bytes → string
    elif isinstance(obj, bytes):
        return obj.decode("utf-8", errors="ignore")

    else:
        return obj
    
def fetch_employees(conn):
    sql = """
        SELECT * FROM employees;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]

def fetch_employee_skills(conn, emp_id):
    sql = """
        SELECT es.skill_id, es.updated_at, es.proficiency, s.name AS skill_name, s.updated_at AS skill_updated_at
        FROM employee_skills es
        JOIN skills s ON s.skill_id = es.skill_id
        WHERE es.employee_id = %s;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (emp_id,))
        return [dict(r) for r in cur.fetchall()]

def build_employee_document(emp, skills):
    """
    Creates the embedding-friendly content block.
    """
    full_name = f"{emp['first_name']} {emp['last_name']}".strip()

    # Build skill string
    if skills:
        skill_text = ", ".join(
            f"{s['skill_name']} ({s['proficiency']})"
            for s in skills
        )
    else:
        skill_text = "No skills listed"

    # Create embedding text (important!)
    content = (
        f"Employee {full_name} (ID: {emp['employee_id']}). "
        f"Works in {emp.get('domain', 'Unknown domain')}. "
        f"Experience: {emp.get('years_experience', 'NA')} years. "
        f"Skills: {skill_text}. "
        f"Employment Type: {emp.get('employment_type')}. "
        f"Status: {emp.get('status')}. "
        f"Location: {emp.get('location')}. "
        f"Hire Date: {emp.get('hire_date')}. "
    )

    safe_emp = make_json_safe(emp)
    safe_skills = make_json_safe(skills)

    # Metadata
    metadata = {
        "table": "employee",
        "row_id": emp["employee_id"],
        "updated_at": safe_emp.get("updated_at"),  
        "skills_json": json.dumps(safe_skills),   # 👍 FIXED
        "raw_json": json.dumps(safe_emp),         # 👍 FIXED
        "extracted_at": datetime.utcnow().isoformat() + "Z",
    }

    doc = {
        "id": f"employee:{emp['employee_id']}",
        "table": "employee",
        "row_id": emp["employee_id"],
        "content": content,
        "metadata": metadata,
    }

    return doc

def extract_all_employee_documents():
    conn = get_connection()
    documents = []

    try:
        employees = fetch_employees(conn)
        for emp in employees:
            emp_id = emp["employee_id"]
            skills = fetch_employee_skills(conn, emp_id)
            doc = build_employee_document(emp, skills)
            documents.append(doc)

    finally:
        conn.close()

    return documents

if __name__ == "__main__":
    import os
    print("hello")
    docs = extract_all_employee_documents()
    print(f"Extracted {len(docs)} employee documents")
    import pprint
    pprint.pprint(docs[:1])
