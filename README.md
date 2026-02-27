# Panther AI Platform

This repository contains the Panther AI Platform project, separated into three main components:

- **agent**: Python-based service for interacting with external systems (OBS, chat, audio, etc.)
- **server**: Node.js + Express backend responsible for API and websockets
- **web**: Next.js frontend application

## Structure

```
panther-ai-platform/
│
├── agent/
│   ├── main.py
│   ├── obs_client.py
│   ├── audio_detector.py
│   ├── chat_listener.py
│   ├── hotkey_listener.py
│   └── config.py
│
├── server/
│   ├── src/
│   │   ├── index.js
│   │   ├── routes/
│   │   ├── services/
│   │   ├── websocket/
│   │   └── utils/
│   ├── package.json
│   └── .env.example
│
├── web/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md
```

## Getting Started

This is phase 1 of the project: scaffolding only. Install dependencies and start each component individually.

### Agent

The agent process is a small FastAPI server that also manages background tasks such as
listening to Twitch chat and handling OBS replay clips.  Before starting, set the following environment variables
(as appropriate for your stream/channel):

- `TWITCH_OAUTH_TOKEN` – OAuth token for the bot account (``oauth:...`` format)
- `TWITCH_NICK` – the Twitch username of the bot
- `TWITCH_CHANNEL` – the channel to join (without `#`)
- `CHAT_KEYWORDS` – comma-separated list of words/phrases to watch for in chat
- `CHAT_FREQ_THRESHOLD` – number of messages in 60s required to classify as spam
- `WEBSOCKET_URL` – address of the server websocket endpoint (defaults to
  `http://localhost:3001`)
- `CLIP_DIR` – directory where OBS saves replay buffer files (optional)

Audio-related variables remain the same:

- `AUDIO_THRESHOLD` – RMS amplitude (0.0–1.0) above which an `audio_spike`
  event is generated (default `0.1`).
- `AUDIO_SAMPLERATE` – sample rate for the microphone input (default
  `44100`).
- `AUDIO_BLOCKSIZE` – frame size used when computing RMS (default `1024`).

Additionally, for uploading clips to S3-compatible storage set:

- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` – credentials for the bucket
- `S3_BUCKET_NAME` – the target bucket name
- `S3_ENDPOINT_URL` – (optional) custom endpoint for R2 or other providers

The agent exposes the following modules for clip handling:

- ``storage/uploader.py`` – encapsulates boto3 upload logic
- ``clip_manager.py`` – locates latest clip, uploads it, and notifies the backend
- ``obs_client.py`` – stub OBS integration that delegates to clip_manager

Example setup (Windows):

```powershell
cd agent
python -m venv venv
.\venv\Scripts\activate
set TWITCH_OAUTH_TOKEN=oauth:yourtokenhere
set TWITCH_NICK=yourbotname
set TWITCH_CHANNEL=yourchannel
set CHAT_KEYWORDS=clip, hype, win
pip install -r requirements.txt
python main.py
```

With the configuration in place the chat listener will automatically connect and
emit `hype_event` messages to the backend when keywords are spotted or the
message rate exceeds the configured threshold.

```bash
# original snippet preserved for reference
# cd agent
# python -m venv venv
# source venv/bin/activate  # or .\\venv\\Scripts\\activate on Windows
# pip install -r requirements.txt
# python main.py
```

### Server

```bash
cd server
npm install
npm run dev
```

### Web

```bash
cd web
npm install
npm run dev
```

Once the web server is running (default port 3000) you can visit `/dashboard` to open the new Live Hype Dashboard. It uses Socket.io to talk to the backend and includes:

- a real-time hype meter
- an event feed showing incoming hype events
- a settings panel with a threshold slider that syncs with the server
- debug buttons for generating sample hype events

Make sure the server (port 3001) is started before connecting.

Further development will add actual logic and inter-component communication.

