from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv

from llm.sql_agent import generate_sql
from llm.sql_validator import validate_sql
from db import run_sql_query
from llm.summarizer import summarize_answer_sql, summarize_answer_vector
from fallback_handler import semantic_fallback

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

client = Groq(api_key = os.getenv("GROQ_API_KEY"))

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query")
def query(request: Request, user_query: str = Form(...)):
    sql_query = generate_sql(user_query)

    ok, msg = validate_sql(sql_query)
    ok = False

    if ok:
        rows, db_msg = run_sql_query(sql_query)
        if rows is None:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": db_msg,
                "sql": sql_query,
                "answer": None
            })
        answer = summarize_answer_sql(user_query, sql_query, rows)

    else:
        relevant_docs = semantic_fallback(user_nl_query = user_query)
        summary = relevant_docs['summary']
        answer = summarize_answer_vector(user_query, summary)
        sql_query = "Failed to generate SQL query!!!"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "sql": sql_query,
        "answer": answer
    })

'''
@app.post("/ask-sql")
def ask_sql(req: QueryRequest):
    user_query = req.query

    # Generate SQL
    # user_query = "Show me the people name and their id working on data like both data scientists or data engineers or data analysts with more than 5 years experience"
    # user_query = "can you show me everything about sneha reddy and the projects she worked and her expertise in technologies"
    sql_query = generate_sql(user_query)


     # Validate SQL
    ok, msg = validate_sql(sql_query)

    if not ok:
        return {
            "user_query": user_query,
            "generated_sql": sql_query,
            "status": "SQL validation failed",
            "message": msg
        }
    
    # Query execution
    rows, db_msg = run_sql_query(sql_query)

    if rows is None:
        return {
            "user_query": user_query,
            "generated_sql": sql_query,
            "status": "Database error",
            "message": db_msg
        }

    summary = summarize_answer(user_query, sql_query, rows)

    return {
        "user_query": user_query,
        "generated_sql": sql_query,
        "status": "success",
        "rows": rows,
        "summary": summary
    }
    

'''