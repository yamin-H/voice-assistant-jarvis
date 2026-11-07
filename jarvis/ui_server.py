"""Tiny local server: serves the ui/ folder and pushes live events over a WebSocket."""
import asyncio
import json
import threading
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

UI_DIR = Path(__file__).resolve().parent.parent / "ui"


class Hub:
    def __init__(self):
        self.loop = None
        self.clients = set()
        self.last_state = {"type": "state", "state": "sleeping"}

    def emit(self, type, **data):
        """Safe to call from any thread. Does nothing until the server is up."""
        msg = {"type": type, **data}
        if type == "state":
            self.last_state = msg
        if self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._broadcast(msg), self.loop)

    async def _broadcast(self, msg):
        text = json.dumps(msg)
        for ws in list(self.clients):
            try:
                await ws.send_text(text)
            except Exception:
                self.clients.discard(ws)


hub = Hub()
app = FastAPI()


@app.on_event("startup")
async def _startup():
    hub.loop = asyncio.get_running_loop()


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    hub.clients.add(websocket)
    await websocket.send_text(json.dumps(hub.last_state))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        hub.clients.discard(websocket)


app.mount("/", StaticFiles(directory=UI_DIR, html=True, check_dir=False), name="ui")


def start_ui_server(port=8765):
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    threading.Thread(target=uvicorn.Server(config).run, daemon=True).start()
    print(f"UI: http://localhost:{port}")