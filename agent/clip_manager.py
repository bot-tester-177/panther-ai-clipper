import os
import glob
import time
import logging

import socketio
import requests

from .storage.uploader import S3Uploader
from .config import Config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ClipManager:
    """Handles discovery, upload, and notification for saved replay clips.

    Usage is intentionally decoupled from OBS-specific logic; the caller is
    responsible for detecting when a replay file exists and invoking
    :py:meth:`process_clip` or :py:meth:`process_latest_clip`.
    """

    def __init__(self, watch_dir: str | None = None):
        self.config = Config.from_env()
        self.watch_dir = (
            watch_dir
            or self.config.clip_dir
            or os.getenv("CLIP_DIR")
            or os.getcwd()
        )
        self.uploader = S3Uploader()
        self._sio = socketio.Client()
        self._connect_ws()

    def _connect_ws(self):
        try:
            logger.debug("connecting socket.io client to %s", self.config.websocket_url)
            self._sio.connect(self.config.websocket_url)
        except Exception as exc:
            logger.warning("failed to connect websocket client: %s", exc)

    def get_latest_clip(self) -> str | None:
        """Return the path to the most recently modified file in *watch_dir*.

        If the directory is empty or contains no files, ``None`` is returned.
        """
        pattern = os.path.join(self.watch_dir, "*")
        files = [f for f in glob.glob(pattern) if os.path.isfile(f)]
        if not files:
            return None
        return max(files, key=os.path.getmtime)

    def process_latest_clip(self, hype_score: int = 0) -> dict | None:
        """Upload the latest clip found in *watch_dir* and notify backend."""
        clip_path = self.get_latest_clip()
        if not clip_path:
            logger.warning("no clip found in %s", self.watch_dir)
            return None
        return self.process_clip(clip_path, hype_score)

    def process_clip(self, clip_path: str, hype_score: int = 0) -> dict:
        """Upload *clip_path* and send metadata to the server.

        ``hype_score`` is included in the metadata payload. A timestamp is added
        automatically.
        """
        file_name = os.path.basename(clip_path)
        try:
            url = self.uploader.upload_file(clip_path, key=file_name)
        except Exception as exc:
            logger.error("upload failed for %s: %s", clip_path, exc)
            return None

        metadata = {
            "fileName": file_name,
            "url": url,
            "hypeScore": hype_score,
            "timestamp": int(time.time()),
        }
        self._send_metadata(metadata)
        return metadata

    def _send_metadata(self, metadata: dict):
        """Attempt to notify the backend about an uploaded clip.

        The preferred channel is a socket.io websocket.  If a connection can't be
        established, the method falls back to an HTTP POST to the same base URL
        with a `/api/clips` path.  Caller code may also invoke
        :meth:`send_metadata_rest` explicitly.
        """
        if not self._sio.connected:
            self._connect_ws()
        if self._sio.connected:
            try:
                self._sio.emit("clip_uploaded", metadata)
                logger.info("sent clip metadata via websocket %s", metadata)
                return
            except Exception as exc:
                logger.warning("websocket metadata send failed: %s", exc)
        # websocket unavailable, fallback to REST
        self.send_metadata_rest(metadata)

    def send_metadata_rest(self, metadata: dict):
        """POST clip metadata to the backend's REST API.

        The target URL is inferred from ``self.config.websocket_url`` by
        replacing the protocol and path with ``/api/clips``.  For example,
        ``http://localhost:3001`` -> ``http://localhost:3001/api/clips``.
        """
        base = self.config.websocket_url.rstrip("/")
        # replace ws:// or http:// etc
        if base.startswith("ws://"):
            base = "http://" + base[len("ws://"):]
        elif base.startswith("wss://"):
            base = "https://" + base[len("wss://"):]
        url = f"{base}/api/clips"
        try:
            resp = requests.post(url, json=metadata, timeout=5)
            resp.raise_for_status()
            logger.info("sent clip metadata via REST %s", metadata)
        except Exception as exc:
            logger.warning("REST metadata send failed (%s): %s", url, exc)


# module-level convenience functions

def get_latest_clip(dir_path: str | None = None) -> str | None:
    mgr = ClipManager(watch_dir=dir_path)
    return mgr.get_latest_clip()


def upload_clip(path: str, hype_score: int = 0) -> dict | None:
    mgr = ClipManager()
    return mgr.process_clip(path, hype_score)


def upload_latest(hype_score: int = 0, dir_path: str | None = None) -> dict | None:
    mgr = ClipManager(watch_dir=dir_path)
    return mgr.process_latest_clip(hype_score)
