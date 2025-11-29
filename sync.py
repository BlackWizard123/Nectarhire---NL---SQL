# sync.py
import json
import os
from datetime import datetime
from pg_extract import (
    get_connection,
    fetch_employees,
    fetch_employee_skills,
    build_employee_document,
)
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
from db import get_db_connection
from pg_extract import extract_all_employee_documents
from vector_ingest import ingest_documents


SYNC_FILE = "sync_state.json"


def load_last_sync_time():
    if not os.path.exists(SYNC_FILE):
        return None
    with open(SYNC_FILE, "r") as f:
        data = json.load(f)
        return data.get("last_sync_time")

def save_last_sync_time(timestamp: str):
    with open(SYNC_FILE, "w") as f:
        json.dump({"last_sync_time": timestamp}, f, indent=4)

def get_updated_employee_ids(conn, last_sync):
    updated_ids = set()

    # 1. Employee table updated
    cur = conn.cursor()
    cur.execute("""
        SELECT employee_id FROM employees
        WHERE updated_at > %s
    """, (last_sync,))
    updated_ids.update([row[0] for row in cur.fetchall()])

    # 2. Employee-skills updated
    cur.execute("""
        SELECT DISTINCT employee_id FROM employee_skills
        WHERE updated_at > %s
    """, (last_sync,))
    updated_ids.update([row[0] for row in cur.fetchall()])

    # 3. Skills updated → update ALL employees having that skill
    cur.execute("""
        SELECT DISTINCT es.employee_id
        FROM skills s
        JOIN employee_skills es ON es.skill_id = s.skill_id
        WHERE s.updated_at > %s
    """, (last_sync,))
    updated_ids.update([row[0] for row in cur.fetchall()])

    return list(updated_ids)

def sync_vector_db(chroma_path=r"C:\Users\H A R I H A R A N\Desktop\My works\Nectar\Project\vector_db"):
    print("\n=== Starting sync ===")

    # Load last sync time
    last_sync_time = load_last_sync_time()
    
    if last_sync_time is None:
        print("No previous sync detected — running FULL INGESTION...")

        docs = extract_all_employee_documents()
        ingest_documents(docs, persist_dir=chroma_path)

        # Save sync timestamp
        now = datetime.utcnow().isoformat() + "Z"
        save_last_sync_time(now)

        print("Full ingestion complete. Sync state initialized.")
        return "FULL_REINGEST_DONE"


    print(f"Last sync: {last_sync_time}")

    conn = get_db_connection()

    # Fetch updated employees
    updated_ids = get_updated_employee_ids(conn, last_sync_time)

    if not updated_ids:
        print("No updates found. Vector DB is already up-to-date.")
        return "NO_UPDATES"

    print(f"Employees requiring update: {updated_ids}")

    # Prepare embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Connect to Chroma
    client = PersistentClient(path=chroma_path)
    collection = client.get_collection("employee_collection")

    # Process employees
    for emp_id in updated_ids:
        print(f"Updating employee {emp_id}")

        # Fetch employee row
        cur = conn.cursor()
        cur.execute("SELECT * FROM employee WHERE employee_id = %s", (emp_id,))
        emp_row = cur.fetchone()
        if not emp_row:
            continue

        # Use RealDictCursor instead if needed
        columns = [desc[0] for desc in cur.description]
        emp = dict(zip(columns, emp_row))

        # Fetch skills for that employee
        skills = fetch_employee_skills(conn, emp_id)

        # Rebuild document
        doc = build_employee_document(emp, skills)

        # Delete old vector
        collection.delete(where={"row_id": emp_id})

        # Re-embed
        emb = model.encode([doc["content"]]).tolist()

        # Reinsert
        collection.upsert(
            ids=[doc["id"]],
            embeddings=emb,
            metadatas=[doc["metadata"]],
            documents=[doc["content"]],
        )

        print(f"Employee {emp_id} updated.")

    # Save new sync time
    now = datetime.utcnow().isoformat() + "Z"
    save_last_sync_time(now)

    print("Sync complete.")
    return "SYNC_COMPLETE"
