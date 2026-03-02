import os
import sys
from unittest import mock

# ensure agent package importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agent.chat_listener import ChatListener, start_listener
from agent.audio_detector import AudioDetector, start_detector
from agent.streaming_state_manager import StreamingStateManager
from agent.config import Config


def test_chat_listener_drops_events_when_not_streaming():
    cfg = Config.from_env()
    mgr = mock.Mock()
    mgr.is_streaming = False
    listener = ChatListener(cfg, streaming_state_mgr=mgr)
    listener._sio = mock.Mock()

    listener._emit_event("chat_keyword", {"foo": "bar"})
    listener._sio.emit.assert_not_called()


def test_chat_listener_allows_events_when_streaming():
    cfg = Config.from_env()
    mgr = mock.Mock()
    mgr.is_streaming = True
    listener = ChatListener(cfg, streaming_state_mgr=mgr)
    listener._sio = mock.Mock()

    listener._emit_event("chat_keyword", {"foo": "bar"})
    listener._sio.emit.assert_called_once()


def test_audio_detector_drops_events_when_not_streaming():
    cfg = Config.from_env()
    mgr = mock.Mock()
    mgr.is_streaming = False
    detector = AudioDetector(cfg, streaming_state_mgr=mgr)
    detector._sio = mock.Mock()

    detector._emit_event("audio_spike", 1)
    detector._sio.emit.assert_not_called()


def test_audio_detector_allows_events_when_streaming():
    cfg = Config.from_env()
    mgr = mock.Mock()
    mgr.is_streaming = True
    detector = AudioDetector(cfg, streaming_state_mgr=mgr)
    detector._sio = mock.Mock()

    detector._emit_event("audio_spike", 1)
    detector._sio.emit.assert_called_once()


def test_start_helpers_pass_streaming_state_mgr():
    cfg = Config.from_env()
    mgr = mock.Mock()

    lst = start_listener(streaming_state_mgr=mgr)
    if lst:
        assert lst._streaming_state_mgr is mgr

    det = start_detector(streaming_state_mgr=mgr)
    if det:
        assert det._streaming_state_mgr is mgr
