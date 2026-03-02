"""Unit tests for StreamingStateManager.

Tests the streaming state detection and coordination logic.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import logging

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


class TestStreamingStateManager(unittest.TestCase):
    """Test cases for StreamingStateManager."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the socketio and Config imports
        with patch("agent.streaming_state_manager.socketio"), patch(
            "agent.streaming_state_manager.Config"
        ) as mock_config:
            mock_instance = MagicMock()
            mock_config.from_env.return_value = mock_instance
            from agent.streaming_state_manager import StreamingStateManager

            self.manager = StreamingStateManager()
            self.manager._sio = Mock()  # Mock websocket

    def test_initial_state(self):
        """Test that streaming state manager starts in not-streaming state."""
        self.assertFalse(self.manager.is_streaming)

    def test_streaming_started_transition(self):
        """Test streaming start transition."""
        self.assertFalse(self.manager.is_streaming)
        self.manager.on_streaming_started()
        self.assertTrue(self.manager.is_streaming)

    def test_streaming_stopped_transition(self):
        """Test streaming stop transition."""
        # First start streaming
        self.manager.on_streaming_started()
        self.assertTrue(self.manager.is_streaming)
        # Then stop
        self.manager.on_streaming_stopped()
        self.assertFalse(self.manager.is_streaming)

    def test_duplicate_streaming_started_ignored(self):
        """Test that duplicate start events are ignored."""
        self.manager.on_streaming_started()
        self.assertTrue(self.manager.is_streaming)
        # Call again - should be ignored
        self.manager.on_streaming_started()
        self.assertTrue(self.manager.is_streaming)

    def test_duplicate_streaming_stopped_ignored(self):
        """Test that duplicate stop events are ignored."""
        # Start first
        self.manager.on_streaming_started()
        self.assertTrue(self.manager.is_streaming)
        # Stop first time
        self.manager.on_streaming_stopped()
        self.assertFalse(self.manager.is_streaming)
        # Stop again - should be ignored
        self.manager.on_streaming_stopped()
        self.assertFalse(self.manager.is_streaming)

    def test_clipping_activated_event_emitted_on_start(self):
        """Test that clipping_activated event is emitted when streaming starts."""
        self.manager.on_streaming_started()
        # Verify websocket emit was called
        self.manager._sio.emit.assert_called()
        call_args = self.manager._sio.emit.call_args
        self.assertEqual(call_args[0][0], "clipping_activated")
        self.assertIn("timestamp", call_args[0][1])

    def test_clipping_paused_event_emitted_on_stop(self):
        """Test that clipping_paused event is emitted when streaming stops."""
        # Start first
        self.manager.on_streaming_started()
        self.manager._sio.emit.reset_mock()
        # Stop streaming
        self.manager.on_streaming_stopped()
        # Verify websocket emit was called with correct event
        self.manager._sio.emit.assert_called()
        call_args = self.manager._sio.emit.call_args
        self.assertEqual(call_args[0][0], "clipping_paused")
        self.assertIn("timestamp", call_args[0][1])

    def test_set_obs_websocket(self):
        """Test setting OBS websocket connection."""
        mock_obs = Mock()
        self.manager.set_obs_websocket(mock_obs)
        self.assertEqual(self.manager._obs_websocket, mock_obs)

    def test_replay_buffer_start_called(self):
        """Test that start replay buffer is called when streaming starts."""
        mock_obs = Mock()
        self.manager.set_obs_websocket(mock_obs)

        with patch("agent.streaming_state_manager.threading"):
            self.manager.on_streaming_started()

        # Verify OBS call was made
        mock_obs.call.assert_called()

    def test_replay_buffer_stop_called(self):
        """Test that stop replay buffer is called when streaming stops."""
        mock_obs = Mock()
        self.manager.set_obs_websocket(mock_obs)

        # Start streaming
        self.manager.on_streaming_started()
        mock_obs.reset_mock()

        # Stop streaming
        self.manager.on_streaming_stopped()

        # Verify OBS call was made
        mock_obs.call.assert_called()

    def test_no_obs_connection_graceful_handling(self):
        """Test that missing OBS connection is handled gracefully."""
        # Don't set OBS websocket
        self.manager._obs_websocket = None

        # Should not raise exception
        self.manager.on_streaming_started()
        self.assertTrue(self.manager.is_streaming)

        self.manager.on_streaming_stopped()
        self.assertFalse(self.manager.is_streaming)


if __name__ == "__main__":
    unittest.main()
