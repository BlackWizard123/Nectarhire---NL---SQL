import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def run_sql_query(sql: str):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(sql)
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]

        result = [dict(zip(colnames, row)) for row in rows]

    except Exception as e:
        cur.close()
        conn.close()
        return None, f"Database execution error: {str(e)}"

    cur.close()
    conn.close()
    return result, "OK"
