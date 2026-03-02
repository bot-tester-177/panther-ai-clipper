"""Main entry point for the Panther AI Agent.

Coordinates initialization of:
- OBS WebSocket connection for streaming state monitoring
- Backend WebSocket connection for events and commands
- Detection modules (audio, chat, hotkey) with streaming state control
- Clip manager for clip processing

Architecture:
1. OBS connection is established first and monitors streaming state
2. Backend WebSocket connection receives trigger_clip events
3. Detection modules are started, but only emit events when streaming is active
4. Streaming state transitions control replay buffer and backend AI clipping system
"""

import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import FastAPI

from .audio_detector import AudioDetector
from .chat_listener import ChatListener
from .config import Config
from .hotkey_listener import HotkeyListener
from .obs_client import OBSClient
from .streaming_state_manager import StreamingStateManager

logger = logging.getLogger(__name__)

app = FastAPI()


@dataclass
class DetectionModules:
    chat: Optional[ChatListener] = None
    audio: Optional[AudioDetector] = None
    hotkey: Optional[HotkeyListener] = None

    def stop(self):
        for mod in (self.chat, self.audio, self.hotkey):
            if mod:
                try:
                    mod.stop()
                except Exception:
                    logger.exception("error stopping detection module %r", mod)


class AgentOrchestrator:
    """Orchestrates connections and activates detection modules only while streaming."""

    def __init__(self):
        self._cfg = Config.from_env()
        self._obs_client: Optional[OBSClient] = None
        self._streaming_state_mgr: Optional[StreamingStateManager] = None
        self._detectors = DetectionModules()
        self._gate_thread: Optional[threading.Thread] = None
        self._stop_evt = threading.Event()
        self._last_streaming: Optional[bool] = None

    @property
    def streaming_state_manager(self) -> Optional[StreamingStateManager]:
        return self._streaming_state_mgr

    def start(self):
        """Start connections and begin gating detection modules based on streaming state."""
        logger.info("=" * 60)
        logger.info("AGENT STARTUP: Initializing connections and orchestrator")
        logger.info("=" * 60)

        # 1) Initialize OBS + streaming state management (must be first)
        self._init_obs_and_streaming_state()

        # 2) Initialize backend websocket connection (OBSClient already connects to server WS)
        #    (If OBS isn't available, we still allow agent to run; streaming state will remain false.)
        self._init_backend_ws()

        # 3) Start gate loop that starts/stops detection modules based on streaming state
        self._start_streaming_gate_loop()

        logger.info("=" * 60)
        logger.info("AGENT STARTUP COMPLETE")
        logger.info("Detection modules will only run while streaming is active")
        logger.info("=" * 60)

    def stop(self):
        """Stop detection modules and disconnect sockets."""
        self._stop_evt.set()

        if self._detectors:
            self._detectors.stop()

        try:
            if self._obs_client:
                if getattr(self._obs_client, "_sio", None) and self._obs_client._sio.connected:
                    self._obs_client._sio.disconnect()
                    logger.info("✓ Backend WebSocket disconnected")
                if getattr(self._obs_client, "_obs", None):
                    self._obs_client._obs.disconnect()
                    logger.info("✓ OBS WebSocket disconnected")
        except Exception as exc:
            logger.warning("error during shutdown: %s", exc)

        logger.info("AGENT SHUTDOWN COMPLETE")

    def _init_obs_and_streaming_state(self):
        try:
            logger.info("step 1: initializing OBS connection...")
            self._obs_client = OBSClient()
            self._obs_client.connect()

            # Get the streaming state manager from OBSClient
            self._streaming_state_mgr = self._obs_client._streaming_state_mgr
            logger.info("✓ OBS connection established")
            logger.info("✓ Streaming state manager initialized")
            logger.info("✓ Streaming state manager is_streaming: %s", self._streaming_state_mgr.is_streaming)
        except Exception as exc:
            logger.error("✗ failed to initialize OBS connection: %s", exc)
            logger.warning("continuing without OBS integration")
            self._obs_client = None
            self._streaming_state_mgr = None

    def _init_backend_ws(self):
        # OBSClient handles connecting to server websocket for trigger_clip events.
        # StreamingStateManager separately connects to websocket to emit clipping_activated/paused.
        if self._obs_client is None:
            return
        if getattr(self._obs_client, "_sio", None) and self._obs_client._sio.connected:
            logger.info("✓ Backend WebSocket connection established (via OBSClient)")
        else:
            logger.warning("⚠ Backend WebSocket not connected (via OBSClient)")

    def _start_streaming_gate_loop(self):
        self._gate_thread = threading.Thread(target=self._gate_loop, daemon=True)
        self._gate_thread.start()

    def _gate_loop(self):
        """Poll streaming state and start/stop detection modules on transitions.

        This avoids wiring callbacks through StreamingStateManager while keeping main.py clean.
        """
        poll_interval_s = 0.5
        while not self._stop_evt.is_set():
            is_streaming = self._streaming_state_mgr.is_streaming if self._streaming_state_mgr else False

            if self._last_streaming is None:
                self._last_streaming = is_streaming

            if is_streaming != self._last_streaming:
                if is_streaming:
                    logger.info("streaming became active -> starting detection modules")
                    self._start_detection_modules()
                else:
                    logger.info("streaming became inactive -> stopping detection modules")
                    self._stop_detection_modules()
                self._last_streaming = is_streaming

            time.sleep(poll_interval_s)

    def _start_detection_modules(self):
        # idempotent start: if already started, do nothing
        if self._detectors.chat or self._detectors.audio or self._detectors.hotkey:
            return

        try:
            logger.info("starting chat listener...")
            if self._cfg.twitch_oauth_token and self._cfg.twitch_nick and self._cfg.twitch_channel:
                self._detectors.chat = ChatListener(self._cfg, streaming_state_mgr=self._streaming_state_mgr)
                self._detectors.chat.start()
                logger.info("✓ Chat listener started")
            else:
                logger.warning("⚠ Chat listener not started (missing config)")

            logger.info("starting audio detector...")
            if self._cfg.audio_threshold > 0:
                self._detectors.audio = AudioDetector(self._cfg, streaming_state_mgr=self._streaming_state_mgr)
                self._detectors.audio.start()
                logger.info("✓ Audio detector started")
            else:
                logger.warning("⚠ Audio detector not started (missing config)")

            logger.info("starting hotkey listener...")
            self._detectors.hotkey = HotkeyListener(self._cfg, streaming_state_mgr=self._streaming_state_mgr)
            self._detectors.hotkey.start()
            logger.info("✓ Hotkey listener started")
        except Exception as exc:
            logger.error("✗ failed to start detection modules: %s", exc)

    def _stop_detection_modules(self):
        self._detectors.stop()
        self._detectors = DetectionModules()


# Global orchestrator reference for clean shutdown + endpoints
_orchestrator: Optional[AgentOrchestrator] = None


@app.on_event("startup")
async def _startup():
    """Initialize all agent components on FastAPI startup."""
    global _orchestrator
    _orchestrator = AgentOrchestrator()
    _orchestrator.start()


@app.on_event("shutdown")
async def _shutdown():
    """Clean up resources on FastAPI shutdown."""
    logger.info("AGENT SHUTDOWN: Cleaning up resources...")
    global _orchestrator
    if _orchestrator:
        _orchestrator.stop()
        _orchestrator = None


@app.get("/health")
async def health():
    """Health check endpoint.
    
    Returns:
        dict: Status information including streaming state
    """
    mgr = _orchestrator.streaming_state_manager if _orchestrator else None
    is_streaming = mgr.is_streaming if mgr else None
    obs_connected = (
        _orchestrator is not None
        and getattr(_orchestrator, "_obs_client", None) is not None
        and getattr(_orchestrator._obs_client, "_obs", None) is not None
    )
    return {"status": "ok", "streaming": is_streaming, "obs_connected": obs_connected}


@app.get("/streaming-state")
async def get_streaming_state():
    """Get current streaming state.
    
    Returns:
        dict: Current streaming state and manager status
    """
    mgr = _orchestrator.streaming_state_manager if _orchestrator else None
    if not mgr:
        return {"status": "error", "message": "streaming state manager not initialized"}

    return {"is_streaming": mgr.is_streaming, "timestamp": mgr._timestamp_ms()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent.main:app", host="127.0.0.1", port=8000, reload=True)
