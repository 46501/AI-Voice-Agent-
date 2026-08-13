# VoxAI — Intelligent Voice Assistant

VoxAI is a modern, production-ready AI Voice Agent web application. It allows you to talk naturally with an AI agent using your microphone. 

## Features
- **Real-Time Voice Interaction:** Uses WebSockets for low-latency communication.
- **Voice Activity Detection (VAD):** Automatically detects when you stop speaking.
- **Modular AI Pipeline:** Integrates OpenAI Whisper (STT), GPT-4o-mini (LLM), and TTS.
- **Tool Calling:** The agent can access external tools (Calculator, Weather, Time, Web Search) to augment its intelligence.
- **Modern UI:** Premium SaaS-style interface with a responsive glassmorphic design and real-time audio visualization.

## Architecture
- **Frontend:** React, TypeScript, Vite. Uses the Web Audio API for VAD and visualization.
- **Backend:** Python, FastAPI. Provides real-time WebSocket orchestration.

## Setup & Installation

### Prerequisites
- Node.js (v18+)
- Python 3.10+
- OpenAI API Key

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` file in the `backend` folder based on `.env.example`:
```
OPENAI_API_KEY=your_key_here
```

Run the backend:
```bash
uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Docker Setup
You can also run the entire application using Docker Compose:
```bash
# Ensure your backend/.env is populated with your API key first
docker-compose up --build
```
*Note: Depending on your browser, accessing microphone via `http://localhost` might be restricted. If so, ensure you use `http://127.0.0.1` or set up HTTPS.*

## API Endpoints
- `GET /api/health` - Health check.
- `POST /api/chat` - REST endpoint for testing text-based chat and tools.
- `WS /ws/voice` - Primary WebSocket connection for voice streaming.

## Future Improvements
- Add persistent database (PostgreSQL) for session memory.
- Implement more robust client-side VAD (e.g., using Silero VAD WASM).
- Support for multiple LLM providers.
