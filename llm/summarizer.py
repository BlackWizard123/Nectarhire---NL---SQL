from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SUMMARY_PROMPT_SQL = """
You are an AI assistant that summarizes database query results for HR or analytics purposes.

Your job is to read:
1. The user's question
2. The SQL query used
3. The database rows returned

And produce a clear, helpful, human-readable answer.

RULES:
- Give a brief summary if many rows.
- Mention key fields like name, role, years_experience, salary, domain, location.
- Do NOT output raw SQL or JSON.
- Be concise but informative.

Format your answer in clean **markdown**:
- Use bullet points
- Use bold for names and roles
- Use tables if multiple rows
- Keep it readable and structured

USER QUESTION:
{query}

SQL EXECUTED:
{sql}

DATABASE ROWS:
{rows}

Now summarize the results in a natural readable way:
"""

SUMMARY_PROMPT_VECTOR = """
You are an AI assistant that summarizes database query results for HR or analytics purposes.

Your job is to read:
1. The user's question
2. Vector search output

And produce a clear, helpful, human-readable answer.

RULES:
- Give a brief summary if many rows.
- Mention key fields like name, role, years_experience, salary, domain, location.
- Do NOT output raw SQL or JSON.
- Be concise but informative.

Format your answer in clean **markdown**:
- Use bullet points
- Use bold for names and roles
- Use tables if multiple rows
- Keep it readable and structured

USER QUESTION:
{query}

VECTOR DB EXTRACTED CONTENT:
{summary}

Now summarize the results in a natural readable way:
"""

def summarize_answer_sql(user_query: str, sql: str, rows: list):
    
    prompt = SUMMARY_PROMPT_SQL.format(
        query=user_query,
        sql=sql,
        rows=str(rows)
    )
    print(prompt)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    return response.choices[0].message.content.strip()

def summarize_answer_vector(user_query: str, summary: str):
    
    prompt = SUMMARY_PROMPT_VECTOR.format(
        query=user_query,
        summary = summary
    )
    print(prompt)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    return response.choices[0].message.content.strip()