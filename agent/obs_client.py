# Simple OBS client integration for triggering replay saves when the
# hype threshold is reached.  In a production deployment this would hook
# into the official OBS WebSocket plugin; here we support both receiving
# a server-side "trigger_clip" event and optionally talking to OBS via
# ``obs-websocket-py`` if the library is installed.

import os
import logging
import threading

import socketio

from .clip_manager import ClipManager
from .config import Config
from .streaming_state_manager import StreamingStateManager

logger = logging.getLogger(__name__)


class OBSClient:
    def __init__(self, replay_dir: str | None = None):
        cfg = Config.from_env()
        # directory where OBS saves replay buffer files; can be overridden by
        # caller or via CLIP_DIR environment variable.
        self.replay_dir = replay_dir or cfg.clip_dir or os.getenv("CLIP_DIR")
        self._clip_mgr = ClipManager(watch_dir=self.replay_dir)
        self._sio = socketio.Client()
        self._obs = None  # optional obs-websocket client
        self._cfg = cfg
        # Streaming state manager for coordinating replay buffer and AI clipping
        self._streaming_state_mgr = StreamingStateManager()
        self._obs_event_thread = None

    def connect(self):
        """Establish connections to the backend websocket and optionally OBS."""
        # connect to server for trigger_clip notifications
        try:
            logger.info("connecting OBS client socket.io to %s", self._cfg.websocket_url)
            self._sio.connect(self._cfg.websocket_url)
            # register handler
            self._sio.on('trigger_clip', self._on_trigger_clip)
        except Exception as exc:
            logger.warning("OBSClient failed to connect to websocket: %s", exc)

        # if OBS websocket info is available, try to connect
        if self._cfg.obs_websocket_url:
            try:
                from obswebsocket import obsws, requests as obs_requests
                self._obs = obsws(self._cfg.obs_websocket_url, 4444, self._cfg.obs_websocket_password)
                self._obs.connect()
                logger.info("connected to OBS websocket at %s", self._cfg.obs_websocket_url)
                
                # Pass OBS websocket to streaming state manager
                self._streaming_state_mgr.set_obs_websocket(self._obs)
                
                # Start listening for streaming state changes in background thread
                self._obs_event_thread = threading.Thread(
                    target=self._listen_streaming_events,
                    daemon=True
                )
                self._obs_event_thread.start()
                logger.info("started streaming state listener")
            except ImportError:
                logger.warning("obs-websocket-py not installed; OBS features disabled")
                self._obs = None
            except Exception as exc:
                logger.warning("failed to connect to OBS websocket: %s", exc)
                self._obs = None

    def _on_trigger_clip(self, data):
        """Callback invoked when the server notifies that the hype threshold
        was crossed.  ``data`` may include a ``score`` property."""
        score = None
        if isinstance(data, dict):
            score = data.get('score')
        
        # Only process trigger if streaming is active
        if not self._streaming_state_mgr.is_streaming:
            logger.warning(
                "received trigger_clip event but not streaming (score=%s), ignoring",
                score
            )
            return
        
        logger.info("received trigger_clip event from server (score=%s)", score)
        # if we have an OBS websocket connection, ask OBS to save the replay
        if self._obs:
            try:
                from obswebsocket import requests as obs_requests
                self._obs.call(obs_requests.SaveReplayBuffer())
                logger.info("requested OBS to save replay buffer")
            except Exception as exc:
                logger.warning("failed to request OBS replay: %s", exc)
        # else, nothing to do; we assume OBS is configured separately to save
        # when the trigger occurs and will later call ``handle_replay_saved``.

    def handle_replay_saved(self, file_path: str = None, hype_score: int = 0):
        """Called when OBS has finished writing a replay file.

        ``file_path`` may be given explicitly by OBS.  If omitted the
        most-recent file in the replay directory is used.

        ``hype_score`` is an optional numeric value that will be included in
        the metadata sent to the backend.
        """
        # Only save clips if streaming is active
        if not self._streaming_state_mgr.is_streaming:
            logger.warning("clip trigger received but not streaming, ignoring replay save")
            return None
        
        if file_path is None:
            # fall back to latest file in watch directory
            file_path = self._clip_mgr.get_latest_clip()
        if not file_path:
            logger.warning("no replay file available to upload")
            return None
        logger.info("processing replay file %s", file_path)
        return self._clip_mgr.process_clip(file_path, hype_score)

    def _listen_streaming_events(self):
        """Background thread that listens for OBS streaming state changes.
        
        This thread monitors the OBS websocket connection for StreamStateChanged
        events and notifies the streaming state manager of transitions.
        """
        if not self._obs:
            logger.warning("OBS websocket not available, cannot listen for events")
            return

        try:
            from obswebsocket import EventListener

            listener = EventListener(self._obs)

            logger.debug("starting OBS event listener for streaming state")
            while True:
                try:
                    event = listener.wait_for_event(timeout=30)
                    if event is None:
                        # Timeout, connection may be dead
                        logger.debug("OBS event listener timeout, reconnecting...")
                        continue

                    event_type = event.type

                    # Handle StreamStateChanged event (new API)
                    if event_type == "StreamStateChanged":
                        output_active = event.data.get("output_active", False)
                        logger.info(
                            "OBS streaming state changed: output_active=%s",
                            output_active,
                        )
                        if output_active:
                            self._streaming_state_mgr.on_streaming_started()
                        else:
                            self._streaming_state_mgr.on_streaming_stopped()

                    # Handle legacy StreamStarting/StreamStopping events
                    elif event_type == "StreamStarting":
                        logger.info("OBS stream starting (legacy event)")
                        self._streaming_state_mgr.on_streaming_started()
                    elif event_type == "StreamStopping":
                        logger.info("OBS stream stopping (legacy event)")
                        self._streaming_state_mgr.on_streaming_stopped()

                except Exception as exc:
                    logger.warning("error processing OBS event: %s", exc)
                    # Continue listening on error
                    continue

        except Exception as exc:
            logger.warning("failed to start OBS event listener: %s", exc)

