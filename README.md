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

```bash
cd agent
python -m venv venv
source venv/bin/activate  # or .\\venv\\Scripts\\activate on Windows
pip install -r requirements.txt
python main.py
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

Further development will add actual logic and inter-component communication.

