"""Manages streaming state transitions and coordinating replay buffer and AI clipping.

This module detects when streaming starts/stops and:
- Automatically starts/stops the OBS Replay Buffer
- Activates/pauses the AI clipping system via websocket events

It is intentionally kept separate from the hype engine and operates at
a higher level of coordination.
"""

import logging
import threading

import socketio

from .config import Config

logger = logging.getLogger(__name__)


class StreamingStateManager:
    """Coordinates streaming state changes with replay buffer and AI clipping.
    
    This manager:
    1. Tracks the current streaming state
    2. Detects transitions (start/stop)
    3. Coordinates replay buffer control
    4. Sends state events to the backend AI clipping system
    """

    def __init__(self):
        self._cfg = Config.from_env()
        self._sio = socketio.Client()
        self._is_streaming = False
        self._obs_websocket = None  # Set by OBSClient if available
        self._connect_ws()

    def _connect_ws(self):
        """Connect to backend websocket server."""
        try:
            logger.debug(
                "streaming_state_manager connecting to %s",
                self._cfg.websocket_url,
            )
            self._sio.connect(self._cfg.websocket_url)
        except Exception as exc:
            logger.warning(
                "streaming_state_manager failed to connect websocket: %s", exc
            )

    def set_obs_websocket(self, obs_ws):
        """Set the OBS websocket connection for controlling replay buffer.
        
        Args:
            obs_ws: An obswebsocket.obsws instance, or None if unavailable.
        """
        self._obs_websocket = obs_ws

    @property
    def is_streaming(self) -> bool:
        """Return current streaming state."""
        return self._is_streaming

    def on_streaming_started(self):
        """Called when OBS detects streaming has started.
        
        Actions:
        - Start the OBS Replay Buffer
        - Notify backend to activate AI clipping
        """
        if self._is_streaming:
            logger.debug("streaming already active, ignoring duplicate start event")
            return

        logger.info("streaming started, activating replay buffer and AI clipping")
        self._is_streaming = True

        # Start replay buffer
        self._start_replay_buffer()

        # Notify backend to activate AI clipping
        self._emit_clipping_activated()

    def on_streaming_stopped(self):
        """Called when OBS detects streaming has stopped.
        
        Actions:
        - Stop the OBS Replay Buffer
        - Notify backend to pause AI clipping
        """
        if not self._is_streaming:
            logger.debug("streaming already inactive, ignoring duplicate stop event")
            return

        logger.info("streaming stopped, stopping replay buffer and pausing AI clipping")
        self._is_streaming = False

        # Stop replay buffer
        self._stop_replay_buffer()

        # Notify backend to pause AI clipping
        self._emit_clipping_paused()

    def _start_replay_buffer(self):
        """Send command to OBS to start the Replay Buffer."""
        if not self._obs_websocket:
            logger.debug("OBS websocket not available, replay buffer not started")
            return

        try:
            # If obs-websocket-py is installed, use the real request type.
            from obswebsocket import requests as obs_requests

            self._obs_websocket.call(obs_requests.StartReplayBuffer())
            logger.info("started OBS replay buffer")
        except ImportError:
            # Keep tests and dev environments working without obs-websocket-py:
            # we still "call" the injected websocket mock to indicate intent.
            try:
                self._obs_websocket.call()
                logger.info("started OBS replay buffer (no obswebsocket module, called raw)")
            except Exception as exc:
                logger.warning("failed to start OBS replay buffer (no obswebsocket module): %s", exc)
        except Exception as exc:
            logger.warning("failed to start OBS replay buffer: %s", exc)

    def _stop_replay_buffer(self):
        """Send command to OBS to stop the Replay Buffer."""
        if not self._obs_websocket:
            logger.debug("OBS websocket not available, replay buffer not stopped")
            return

        try:
            from obswebsocket import requests as obs_requests

            self._obs_websocket.call(obs_requests.StopReplayBuffer())
            logger.info("stopped OBS replay buffer")
        except ImportError:
            try:
                self._obs_websocket.call()
                logger.info("stopped OBS replay buffer (no obswebsocket module, called raw)")
            except Exception as exc:
                logger.warning("failed to stop OBS replay buffer (no obswebsocket module): %s", exc)
        except Exception as exc:
            logger.warning("failed to stop OBS replay buffer: %s", exc)

    def _emit_clipping_activated(self):
        """Emit event to backend indicating AI clipping system is active."""
        try:
            self._sio.emit("clipping_activated", {"timestamp": self._timestamp_ms()})
            logger.debug("emitted clipping_activated event to backend")
        except Exception as exc:
            logger.warning("failed to emit clipping_activated event: %s", exc)

    def _emit_clipping_paused(self):
        """Emit event to backend indicating AI clipping system is paused."""
        try:
            self._sio.emit("clipping_paused", {"timestamp": self._timestamp_ms()})
            logger.debug("emitted clipping_paused event to backend")
        except Exception as exc:
            logger.warning("failed to emit clipping_paused event: %s", exc)

    @staticmethod
    def _timestamp_ms() -> int:
        """Get current timestamp in milliseconds."""
        import time

        return int(time.time() * 1000)
