# Simple OBS client integration for triggering replay saves when the
# hype threshold is reached.  In a production deployment this would hook
# into the official OBS WebSocket plugin; here we support both receiving
# a server-side "trigger_clip" event and optionally talking to OBS via
# ``obs-websocket-py`` if the library is installed.

import os
import logging

import socketio

from .clip_manager import ClipManager
from .config import Config

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
        if file_path is None:
            # fall back to latest file in watch directory
            file_path = self._clip_mgr.get_latest_clip()
        if not file_path:
            logger.warning("no replay file available to upload")
            return None
        logger.info("processing replay file %s", file_path)
        return self._clip_mgr.process_clip(file_path, hype_score)

