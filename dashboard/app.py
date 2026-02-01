"""
FastAPI Dashboard for Open Decision Engine.

Provides a live feed of ledger entries with WebSocket support for real-time updates.
"""
import os
import json
import asyncio
from pathlib import Path
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Open Decision Engine - Live Feed")

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Track connected WebSocket clients
connected_clients: List[WebSocket] = []

def get_ledger_entries() -> List[dict]:
    """Read all entries from the ledger file."""
    # Get the project root (parent of dashboard directory)
    project_root = Path(__file__).parent.parent
    ledger_file = project_root / os.getenv("LEDGER_FILE", "ledger/entries.jsonl")
    entries = []
    if ledger_file.exists():
        with open(ledger_file, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    return entries


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard."""
    return FileResponse(static_dir / "index.html")

@app.get("/api/entries")
async def get_entries():
    """Return all ledger entries as JSON."""
    return get_ledger_entries()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        # Send current entries on connect
        entries = get_ledger_entries()
        await websocket.send_json({"type": "init", "entries": entries})
        
        # Keep connection alive and watch for new entries
        last_count = len(entries)
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            current_entries = get_ledger_entries()
            if len(current_entries) > last_count:
                new_entries = current_entries[last_count:]
                for entry in new_entries:
                    await websocket.send_json({"type": "new", "entry": entry})
                last_count = len(current_entries)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
