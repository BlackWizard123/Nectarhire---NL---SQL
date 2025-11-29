from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()

# Load your Groq key from ENV
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SQL_AGENT_PROMPT = """
You are an expert SQL query generator for a PostgreSQL database.
Your job is to convert natural language questions about employees
into SQL queries.

IMPORTANT RULES:
- Use ONLY the tables and columns provided in the schema below.
- Do NOT hallucinate or invent new column names.
- Use ONLY SELECT queries.
- NEVER use DELETE, UPDATE, INSERT, DROP, or ALTER.
- Use proper JOINs based on foreign keys.
- All string comparisons must be case-insensitive using LOWER().
- When user asks for "top" results, add LIMIT 20.
- RETURN ONLY the SQL query with no explanation.
- When selecting employees, prefer: SELECT e.*, r.name AS role_name
- When returning employee results, always include all relevant fields: SELECT e.*, r.name AS role_name and if they specify specific columns, use that alone.
- 

======== DATABASE SCHEMA =========

employees(employee_id, first_name, last_name, email, phone, date_of_birth,
          gender, hire_date, employment_type, status, department_id, role_id,
          years_experience, salary, location)

departments(department_id, name)

roles(role_id, name, description)

skills(skill_id, name)

employee_skills(employee_id, skill_id, proficiency)

projects(project_id, name, domain, description)

employee_projects(employee_id, project_id, role, contribution)

======== CATEGORICAL VALUES =========

these are the valid role names:
software engineer,
senior software engineer,
full stack developer,
data engineer,
data scientist,
machine learning engineer,
genai engineer,
cloud architect,
devops engineer,
security engineer,
product manager,
ai research scientist,
business analyst,
finance analyst,
people operations specialist

these are the valid skills:
python, sql,java,javascript,react,node.js,docker,kubernetes,aws,gcp,azure,machine learning,deep learning,genai,langchain,prompt engineering,
data modeling,ci/cd,terraform,cybersecurity

these are the valid employment types:
full-time,contract,internship

these are the  statuses:
active,resigned,terminated,on-leave


======== USER QUESTION =========
{query}

======== OUTPUT FORMAT RULES ========

Return ONLY pure SQL.

Do NOT include ``` characters.

DO NOT include "\n"

Do NOT include markdown.

Do NOT include “sql” labels.

Do NOT include explanations.

The output must be a single SQL statement.

Give a executable ready SQL query
"""

def generate_sql(user_query: str):
    prompt = SQL_AGENT_PROMPT.format(query=user_query)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=512
    )

    sql_output = response.choices[0].message.content.strip()
    print(sql_output)
    return sql_output