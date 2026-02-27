import os
import sys

# ensure agent package is importable by adding repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agent.config import Config


def test_default_config_values():
    # make sure no environment variables cause errors
    for var in ["HOTKEY", "OBS_WEBSOCKET_URL", "OBS_WEBSOCKET_PASSWORD"]:
        if var in os.environ:
            del os.environ[var]
    cfg = Config.from_env()
    assert cfg.websocket_url == "http://localhost:3001"
    assert cfg.hotkey == ""
    assert cfg.obs_websocket_url == ""
    assert cfg.obs_websocket_password == ""


def test_config_hotkey_and_obs():
    os.environ["HOTKEY"] = "ctrl+alt+h"
    os.environ["OBS_WEBSOCKET_URL"] = "ws://localhost:4444"
    os.environ["OBS_WEBSOCKET_PASSWORD"] = "secret"
    cfg = Config.from_env()
    assert cfg.hotkey == "ctrl+alt+h"
    assert cfg.obs_websocket_url == "ws://localhost:4444"
    assert cfg.obs_websocket_password == "secret"
    # cleanup
    for var in ["HOTKEY", "OBS_WEBSOCKET_URL", "OBS_WEBSOCKET_PASSWORD"]:
        del os.environ[var]
