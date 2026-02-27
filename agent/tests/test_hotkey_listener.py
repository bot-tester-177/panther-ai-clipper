import os
import sys
from unittest import mock

# make sure the agent package can be imported by adding repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest

from agent.hotkey_listener import HotkeyListener
from agent.config import Config


def test_hotkey_configuration():
    os.environ["HOTKEY"] = "F9"
    cfg = Config.from_env()
    assert cfg.hotkey == "F9"
    del os.environ["HOTKEY"]


def test_start_keyboard_listener_registers_hotkey(monkeypatch):
    os.environ["HOTKEY"] = "ctrl+h"
    cfg = Config.from_env()
    listener = HotkeyListener(cfg)
    listener._connect_ws = lambda: None  # avoid real socket call

    fake_keyboard = mock.Mock()
    # ensure the import statement in the module will pick up our fake
    monkeypatch.setitem(sys.modules, 'keyboard', fake_keyboard)

    listener._start_keyboard_listener()
    fake_keyboard.add_hotkey.assert_called_once_with('ctrl+h', mock.ANY)

    # simulate the hotkey callback being invoked
    cb = fake_keyboard.add_hotkey.call_args[0][1]
    listener._emit_event = mock.Mock()
    cb()
    listener._emit_event.assert_called_with('manual_trigger')

    del os.environ["HOTKEY"]
