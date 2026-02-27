import logging
import os

import numpy as np
import sounddevice as sd
import socketio

from .config import Config


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AudioDetector:
    """Captures microphone input and emits hype events when sound spikes.

    Uses :pyclass:`sounddevice.InputStream` to read audio from the default
    input device in a background thread.  RMS amplitude is computed for each
    block of samples; if the level exceeds ``config.audio_threshold`` an
    ``audio_spike`` event is sent to the websocket server.
    """

    def __init__(self, config: Config):
        self.config = config
        self._sio = socketio.Client()
        self._running = False
        self.stream = None

    def _connect_ws(self):
        try:
            logger.info("connecting socket.io client to %s", self.config.websocket_url)
            self._sio.connect(self.config.websocket_url)
        except Exception as exc:
            logger.warning("failed to connect websocket client: %s", exc)

    def _emit_event(self, event_type: str, data=None):
        if not self._sio.connected:
            # try to reconnect once
            self._connect_ws()
        payload = {"type": event_type}
        if data is not None:
            payload["value"] = data
        try:
            self._sio.emit("hype_event", payload)
            logger.debug("emitted hype_event %s", payload)
        except Exception as exc:
            logger.warning("failed to emit event %s: %s", payload, exc)

    def _audio_callback(self, indata, frames, time, status):
        # called in the sounddevice audio thread
        if status:
            logger.warning("input stream status: %s", status)

        # flatten to mono if more than one channel
        data = indata
        if data.ndim > 1:
            data = data.mean(axis=1)

        # compute RMS amplitude
        rms = float(np.sqrt(np.mean(data ** 2)))
        if rms >= self.config.audio_threshold:
            logger.info("audio spike detected (rms=%.3f)", rms)
            self._emit_event("audio_spike", {"rms": rms})

    def start(self):
        if self._running:
            return
        self._running = True
        self._connect_ws()
        try:
            self.stream = sd.InputStream(
                channels=1,
                samplerate=self.config.audio_samplerate,
                blocksize=self.config.audio_blocksize,
                callback=self._audio_callback,
            )
            self.stream.start()
            logger.info("audio detector started (threshold=%s)", self.config.audio_threshold)
        except Exception as exc:
            logger.error("failed to start audio stream: %s", exc)
            self._running = False

    def stop(self):
        self._running = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None


# convenience entrypoint for the rest of the agent

def start_detector():
    cfg = Config.from_env()
    # if threshold is 0 or negative, treat as disabled
    if cfg.audio_threshold <= 0:
        logger.warning("audio threshold disabled or not configured, detector will not start")
        return None
    detector = AudioDetector(cfg)
    detector.start()
    return detector
