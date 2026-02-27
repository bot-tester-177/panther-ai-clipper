import os
import sys
from unittest import mock

# ensure agent package is importable (add repo root to path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agent.obs_client import OBSClient


def test_obs_client_socket_connection(monkeypatch):
    # patch socketio client to inspect calls
    fake_sio_module = mock.Mock()
    fake_client = mock.Mock()
    fake_sio_module.Client.return_value = fake_client
    # patch the attribute used by OBSClient rather than sys.modules entry
    monkeypatch.setattr('agent.obs_client.socketio', fake_sio_module)

    client = OBSClient(replay_dir="/tmp")
    client._cfg = client._cfg  # no change
    client.connect()
    fake_client.connect.assert_called_once()
    fake_client.on.assert_called_once_with('trigger_clip', client._on_trigger_clip)


def test_on_trigger_clip_invokes_obs(monkeypatch):
    client = OBSClient(replay_dir="/tmp")
    client._obs = mock.Mock()
    client._obs.call = mock.Mock()

    # simulate obswebsocket module so the import inside _on_trigger_clip succeeds
    fake_obs = mock.Mock()
    fake_obs.requests = mock.Mock()
    fake_obs.requests.SaveReplayBuffer = lambda: "buff"
    monkeypatch.setitem(sys.modules, 'obswebsocket', fake_obs)
    monkeypatch.setitem(sys.modules, 'obswebsocket.requests', fake_obs.requests)

    # call with score data
    client._on_trigger_clip({'score': 5})
    assert client._obs.call.called
