import socket
import threading
import time
import re
import logging

import socketio

from .config import Config


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ChatListener:
    """Listens to a Twitch chat channel over IRC and generates hype events.

    The listener performs a few responsibilities:

    * Connect to Twitch's IRC endpoint and join a channel
    * Keep a sliding window of messages to detect "chat spam" events
    * Scan each message for keywords defined in the configuration
    * Emit events to the server via a socket.io websocket connection
    """

    IRCSERVER = "irc.chat.twitch.tv"
    IRCPORT = 6667

    def __init__(self, config: Config):
        self.config = config
        self._sock = None
        self._running = False

        # sliding window of recent message timestamps (seconds since epoch)
        self._timestamps = []

        # socket.io client to talk to the WebSocket server
        self._sio = socketio.Client()

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

    def _track_message(self):
        now = time.time()
        self._timestamps.append(now)
        # drop anything older than 60s
        cutoff = now - 60
        self._timestamps = [t for t in self._timestamps if t >= cutoff]
        if len(self._timestamps) >= self.config.chat_frequency_threshold:
            logger.info("chat spam detected (%d messages/60s)", len(self._timestamps))
            self._emit_event("chat_spam", {"count": len(self._timestamps)})
            # clear so we don't spam the server repeatedly
            self._timestamps.clear()

    def _check_keywords(self, message: str):
        for kw in self.config.chat_keywords:
            if kw and kw.lower() in message.lower():
                logger.info("keyword '%s' found in message", kw)
                self._emit_event("keyword", {"keyword": kw, "message": message})

    def _parse_line(self, line: str):
        # Example PRIVMSG line:
        # :nickname!nickname@nickname.tmi.twitch.tv PRIVMSG #channel :the message text
        if "PRIVMSG" in line:
            try:
                msg = line.split("PRIVMSG", 1)[1]
                # split off the leading ":"
                msg = msg.split(":", 1)[1]
            except IndexError:
                return
            self._track_message()
            self._check_keywords(msg)

    def _irc_loop(self):
        self._sock = socket.socket()
        self._sock.connect((self.IRCSERVER, self.IRCPORT))
        # authentication
        self._sock.send(f"PASS {self.config.twitch_oauth_token}\r\n".encode("utf-8"))
        self._sock.send(f"NICK {self.config.twitch_nick}\r\n".encode("utf-8"))
        self._sock.send(f"JOIN #{self.config.twitch_channel}\r\n".encode("utf-8"))
        logger.info("joined channel #%s", self.config.twitch_channel)

        buffer = ""
        while self._running:
            try:
                data = self._sock.recv(2048).decode("utf-8")
                if not data:
                    break
                buffer += data
                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    logger.debug("irc> %s", line)
                    if line.startswith("PING"):
                        self._sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
                        continue
                    self._parse_line(line)
            except Exception as exc:
                logger.warning("irc loop exception: %s", exc)
                break
        self._sock.close()
        self._sock = None

    def start(self):
        """Start the listener in a background thread."""
        if self._running:
            return
        self._running = True
        # establish websocket connection before joining chat
        self._connect_ws()
        thread = threading.Thread(target=self._irc_loop, daemon=True)
        thread.start()

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass


# convenience entrypoint for the rest of the agent


def start_listener():
    cfg = Config.from_env()
    if not cfg.twitch_oauth_token or not cfg.twitch_nick or not cfg.twitch_channel:
        logger.warning("insufficient twitch configuration, chat listener will not start")
        return None
    listener = ChatListener(cfg)
    listener.start()
    return listener

