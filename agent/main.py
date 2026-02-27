from fastapi import FastAPI
import asyncio

from .chat_listener import start_listener
from .audio_detector import start_detector
from .hotkey_listener import start_hotkey
from .obs_client import OBSClient

app = FastAPI()


@app.on_event("startup")
async def _startup():
    # kick off background services; the chat listener runs in its own thread
    logger = __import__("logging").getLogger(__name__)
    logger.info("agent starting up, launching background services")
    # start_listener/start_detector return None if configuration is missing
    start_listener()
    start_detector()
    # hotkey listener is optional
    start_hotkey()
    # OBS client monitors trigger_clip events and can also drive OBS directly
    obs = OBSClient()
    obs.connect()


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent.main:app", host="127.0.0.1", port=8000, reload=True)
