from fastapi import FastAPI
import asyncio
from sync import sync_vector_db

app = FastAPI(title="Vector Sync Service")

async def sync_loop():
    while True:
        print("[SYNC SERVICE] Running background sync...")
        try:
            sync_vector_db()
        except Exception as e:
            print("[SYNC ERROR]", e)
        await asyncio.sleep(2 * 60)  # 30 minutes


@app.on_event("startup")
async def start_background_sync():
    asyncio.create_task(sync_loop())

@app.get("/sync/manual")
def manual_sync():
    try:
        result = sync_vector_db()
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}