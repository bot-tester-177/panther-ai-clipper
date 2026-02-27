import logging
import threading

import socketio

from .config import Config


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class HotkeyListener:
    """Listens for a configured key combination and emits a hype event.

    The hotkey string comes from ``Config.hotkey`` and should use the same
    syntax as ``keyboard.add_hotkey`` (e.g. "ctrl+alt+h").  When the hotkey is
    pressed a ``manual_trigger`` event is sent to the backend via websocket.
    """

    def __init__(self, config: Config):
        self.config = config
        self._sio = socketio.Client()
        self._running = False

    def _connect_ws(self):
        try:
            logger.info("connecting socket.io client to %s", self.config.websocket_url)
            self._sio.connect(self.config.websocket_url)
        except Exception as exc:
            logger.warning("failed to connect websocket client: %s", exc)

    def _emit_event(self, event_type: str):
        if not self._sio.connected:
            self._connect_ws()
        try:
            self._sio.emit("hype_event", {"type": event_type})
            logger.debug("emitted hype_event %s", event_type)
        except Exception as exc:
            logger.warning("failed to emit event %s: %s", event_type, exc)

    def _start_keyboard_listener(self):
        try:
            import keyboard
        except ImportError:
            logger.error("keyboard module not installed; hotkey listener disabled")
            return

        def callback():
            logger.info("hotkey %s pressed", self.config.hotkey)
            self._emit_event("manual_trigger")

        try:
            keyboard.add_hotkey(self.config.hotkey, callback)
            logger.info("hotkey listener started for %s", self.config.hotkey)
        except Exception as exc:
            logger.error("failed to register hotkey %s: %s", self.config.hotkey, exc)
            self._running = False

    def start(self):
        if self._running:
            return
        if not self.config.hotkey:
            logger.warning("hotkey not configured, listener will not start")
            return
        self._running = True
        self._connect_ws()
        thread = threading.Thread(target=self._start_keyboard_listener, daemon=True)
        thread.start()

    def stop(self):
        if not self._running:
            return
        try:
            import keyboard
            keyboard.remove_hotkey(self.config.hotkey)
        except Exception:
            pass
        self._running = False


def start_hotkey():
    cfg = Config.from_env()
    listener = HotkeyListener(cfg)
    listener.start()
    return listener
