import os
import sys
from unittest import mock

# ensure agent package is importable (add repo root to path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agent.obs_client import OBSClient

# prevent ClipManager from opening real websocket connections during tests
from agent import obs_client
obs_client.ClipManager = mock.Mock()

# also replace StreamingStateManager with dummy to avoid real websocket during OBSClient init
obs_client.StreamingStateManager = mock.Mock(return_value=mock.Mock(
    is_streaming=False,
    set_obs_websocket=lambda x: None,
))


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
    # Set streaming to active so trigger_clip proceeds
    client._streaming_state_mgr.is_streaming = True

    # simulate obswebsocket module so the import inside _on_trigger_clip succeeds
    fake_obs = mock.Mock()
    fake_obs.requests = mock.Mock()
    fake_obs.requests.SaveReplayBuffer = lambda: "buff"
    monkeypatch.setitem(sys.modules, 'obswebsocket', fake_obs)
    monkeypatch.setitem(sys.modules, 'obswebsocket.requests', fake_obs.requests)

    # call with score data
    client._on_trigger_clip({'score': 5})
    assert client._obs.call.called

def test_on_trigger_clip_ignored_when_not_streaming(monkeypatch):
    """Verify that trigger_clip is ignored when not streaming."""
    client = OBSClient(replay_dir="/tmp")
    client._obs = mock.Mock()
    client._obs.call = mock.Mock()
    # Ensure streaming is NOT active (default state)
    client._streaming_state_mgr.is_streaming = False


    # simulate obswebsocket module
    fake_obs = mock.Mock()
    fake_obs.requests = mock.Mock()
    fake_obs.requests.SaveReplayBuffer = lambda: "buff"
    monkeypatch.setitem(sys.modules, 'obswebsocket', fake_obs)
    monkeypatch.setitem(sys.modules, 'obswebsocket.requests', fake_obs.requests)

    # call with score data
    client._on_trigger_clip({'score': 5})
    # verify OBS.call was NOT invoked
    assert not client._obs.call.called


def test_handle_replay_saved_drops_when_not_streaming():
    client = OBSClient(replay_dir="/tmp")
    # stub clip manager so we can see if process_clip is called
    client._clip_mgr = mock.Mock()
    client._streaming_state_mgr._is_streaming = False
    result = client.handle_replay_saved(file_path="/tmp/foo.mp4", hype_score=10)
    assert result is None
    client._clip_mgr.process_clip.assert_not_called()