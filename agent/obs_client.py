# Placeholder for OBS client integration.
# In a real implementation this module would register callbacks with the OBS
# WebSocket plugin or similar.  For now we provide a minimal helper that
# delegates clip handling to :mod:`clip_manager` so that the upload logic
# remains modular and testable.

import os
import logging

from .clip_manager import ClipManager

logger = logging.getLogger(__name__)


class OBSClient:
    def __init__(self, replay_dir: str | None = None):
        # directory where OBS saves replay buffer files; can be overridden by
        # caller or via CLIP_DIR environment variable.
        self.replay_dir = replay_dir or os.getenv("CLIP_DIR")
        self._clip_mgr = ClipManager(watch_dir=self.replay_dir)

    def connect(self):
        # connect to OBS WebSocket, register event handlers, etc.
        # This is intentionally left as a stub; the important logic lives in
        # clip_manager.  When a replay save event is received, the caller
        # should invoke ``self.handle_replay_saved()``.
        pass

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

