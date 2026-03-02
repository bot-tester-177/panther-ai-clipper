"""
Streaming State Management System

OVERVIEW
========
The streaming state management system monitors OBS streaming state changes and
automatically coordinates:
1. OBS Replay Buffer control (start/stop)
2. AI clipping system activation/pause via websocket events

This system is intentionally separated from the hype engine and operates at
a higher coordination level.

ARCHITECTURE
============

StreamingStateManager (streaming_state_manager.py)
---------------------------------------------------
Core module responsible for:
- Tracking current streaming state (streaming/not streaming)
- Detecting state transitions
- Coordinating replay buffer via OBS websocket
- Sending state events to backend via websocket

Key Methods:
- on_streaming_started(): Called when streaming begins
  - Starts the OBS Replay Buffer
  - Emits 'clipping_activated' event to backend
  
- on_streaming_stopped(): Called when streaming ends
  - Stops the OBS Replay Buffer
  - Emits 'clipping_paused' event to backend

OBSClient (obs_client.py)
----------------------------
Modified to:
- Create and initialize a StreamingStateManager instance
- Pass OBS websocket connection to streaming state manager
- Start a background thread (_listen_streaming_events) that:
  - Listens for OBS streaming state changes
  - Calls appropriate methods on StreamingStateManager
  - Handles both new and legacy OBS event APIs

Event Flow Diagram
-------------------

    OBS WebSocket Events
           |
           v
    _listen_streaming_events() [background thread]
           |
           +-- StreamStateChanged (output_active=true)
           |   -> on_streaming_started()
           |
           +-- StreamStarting (legacy)
           |   -> on_streaming_started()
           |
           +-- StreamStateChanged (output_active=false)
           |   -> on_streaming_stopped()
           |
           +-- StreamStopping (legacy)
               -> on_streaming_stopped()

    StreamingStateManager
           |
           +-- _start_replay_buffer()
           |   -> OBS.call(StartReplayBuffer())
           |
           +-- _emit_clipping_activated()
           |   -> websocket.emit('clipping_activated', {...})
           |
           +-- _stop_replay_buffer()
           |   -> OBS.call(StopReplayBuffer())
           |
           +-- _emit_clipping_paused()
               -> websocket.emit('clipping_paused', {...})


ENVIRONMENT VARIABLES REQUIRED
==============================
OBS_WEBSOCKET_URL       - URL of OBS websocket plugin (e.g., ws://localhost:4455)
OBS_WEBSOCKET_PASSWORD  - Password for OBS websocket (if configured)
WEBSOCKET_URL           - Backend websocket URL for state events

INTEGRATION WITH EXISTING SYSTEMS
===================================

Does NOT interfere with:
- HypeEngine: Streaming state detection is independent
- ChatListener: Uses separate event system
- AudioDetector: Operates independently
- HotKeyListener: Separate triggering mechanism

Works alongside:
- ClipManager: Handles clip processing (independent)
- trigger_clip event handler: Still works as before

KEY DESIGN DECISIONS
====================

1. Separation of Concerns
   - Streaming state management is separate from hype detection
   - Each system has clear responsibilities
   
2. Thread Safety
   - Event listener runs in daemon thread
   - State transitions protected with simple flags
   - No complex synchronization needed for low-frequency events

3. Error Resilience
   - Failures in replay buffer control don't crash the system
   - Missing OBS connection handled gracefully
   - Event listener continues on individual event errors

4. API Compatibility
   - Supports both new OBS WebSocket API (5.0+)
   - Supports legacy OBS WebSocket API (4.x)
   - Graceful degradation if obs-websocket-py not installed

USAGE
=====

The system starts automatically when main.py initializes OBSClient:

    from agent.obs_client import OBSClient
    
    obs = OBSClient()
    obs.connect()  # Starts streaming state listener automatically

The streaming state manager will:
1. Connect to OBS via websocket
2. Start background event listener
3. Automatically manage replay buffer and AI clipping based on stream state

BACKEND EVENTS
==============

The following events are emitted to the backend:

1. clipping_activated
   - Emitted: When stream starts
   - Data: { "timestamp": <milliseconds> }
   - Purpose: Signal backend to activate AI clipping system

2. clipping_paused
   - Emitted: When stream stops
   - Data: { "timestamp": <milliseconds> }
   - Purpose: Signal backend to pause AI clipping system

TESTING
=======

Unit tests are provided in tests/test_streaming_state_manager.py:

    python -m pytest agent/tests/test_streaming_state_manager.py -v

Tests cover:
- State transitions
- Duplicate event handling
- OBS command execution
- Websocket event emission
- Graceful error handling

TROUBLESHOOTING
===============

Streaming events not detected:
- Verify OBS_WEBSOCKET_URL is correct
- Check OBS_WEBSOCKET_PASSWORD if set
- Ensure obs-websocket-py is installed
- Check agent logs for connection errors

Replay buffer not starting:
- Verify Replay Buffer is enabled in OBS
- Check OBS websocket permissions
- Monitor agent logs for OBS call errors

Events not reaching backend:
- Verify WEBSOCKET_URL is correct
- Check backend server is running
- Monitor agent logs for emit errors

FUTURE ENHANCEMENTS
===================

Possible improvements:
1. Persistent state store for recovery
2. Retry logic for failed OBS commands
3. Metrics/monitoring for streaming events
4. Configuration for custom buffer durations
5. Integration with scene detection for advanced logic
"""
