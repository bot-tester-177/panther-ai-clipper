from fastapi import FastAPI
import asyncio

from .chat_listener import start_listener
from .audio_detector import start_detector

app = FastAPI()


@app.on_event("startup")
async def _startup():
    # kick off background services; the chat listener runs in its own thread
    logger = __import__("logging").getLogger(__name__)
    logger.info("agent starting up, launching chat listener and audio detector if configured")
    # start_listener/start_detector return None if configuration is missing
    start_listener()
    start_detector()


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent.main:app", host="127.0.0.1", port=8000, reload=True)
