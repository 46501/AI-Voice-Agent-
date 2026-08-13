# VoxAI - Intelligent Voice Assistant

VoxAI is a production-grade, bidirectional AI voice assistant built with React, FastAPI, and OpenAI. It features ultra-low latency streaming, true barge-in (interruption), and a robust tool-calling architecture.

## Features

- **Ultra-Low Latency:** Sentence-level chunking and streaming TTS means the AI starts speaking almost instantly.
- **True Interruption (Barge-in):** Speak over the AI at any time. The system immediately halts playback, flushes the audio queue, and cancels backend generation tasks.
- **Tool Registry:** The AI can autonomously use tools to fetch weather, search the web, calculate math, check the time, or save notes.
- **Persistence:** PostgreSQL database stores users, conversations, and messages.
- **Authentication:** JWT-based user authentication.
- **Developer Metrics:** Live latency tracking (STT, LLM First Token, TTS, TTFB).
- **Modern UI:** Premium SaaS-style interface with a Sidebar, Auth Modals, and an interactive VoiceOrb.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system diagrams and pipeline flow.

## Prerequisites

- Docker and Docker Compose
- API Keys:
  - OpenAI API Key (`OPENAI_API_KEY`)
  - OpenWeather API Key (`WEATHER_API_KEY`) - *Optional*
  - Tavily Search API Key (`TAVILY_API_KEY`) - *Optional*

## Quick Start (Docker)

1. Clone the repository.
2. Copy `backend/.env.example` to `backend/.env` and add your API keys.
3. Start the application using Docker Compose:
   ```bash
   docker-compose up --build
   ```
4. Access the frontend at `http://localhost:5173`.
5. Access the backend API at `http://localhost:8000/docs`.

## Local Development (Without Docker)

### Backend
1. `cd backend`
2. `python -m venv venv`
3. Activate the virtual environment (`venv\Scripts\activate` on Windows).
4. `pip install -r requirements.txt`
5. `uvicorn app.main:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`
