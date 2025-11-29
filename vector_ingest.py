import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from pg_extract import extract_all_employee_documents

class VectorDB:
    def __init__(self, persist_dir=r"C:\Users\H A R I H A R A N\Desktop\My works\Nectar\Project\vector_db"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = None

    def get_or_create_collection(self, name="employee_collection"):
        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}  # cosine similarity for MiniLM
        )

def embed_documents(model, docs: List[Dict[str, Any]]):
    contents = [d["content"] for d in docs]
    ids = [d["id"] for d in docs]
    metadatas = [d["metadata"] for d in docs]

    embeddings = model.encode(contents).tolist()
    return ids, contents, metadatas, embeddings

def insert_into_chroma(collection, ids, contents, metadatas, embeddings):
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=contents,
        metadatas=metadatas,
    )

def ingest_documents(docs: List[Dict[str, Any]], persist_dir=r"C:\Users\H A R I H A R A N\Desktop\My works\Nectar\Project\vector_db"):
    # Load embedding model only once
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Build vector DB
    print("Connecting to ChromaDB...")
    db = VectorDB(persist_dir=persist_dir)
    db.get_or_create_collection("employee_collection")

    # Prepare data
    print("Embedding documents...")
    ids, contents, metadatas, embeddings = embed_documents(model, docs)

    # Insert
    print("Inserting into ChromaDB...")
    insert_into_chroma(db.collection, ids, contents, metadatas, embeddings)

    count = db.collection.count()
    print(f"Successfully ingested {len(ids)} documents into Chroma database.")
    print(f"Total documents in collection: {count}")
    print(f"Database persisted at: {persist_dir}")

if __name__ == "__main__":
    docs = extract_all_employee_documents()
    print(docs)
    ingest_documents(docs)
