# ARIA — Advanced Responsive Intelligence Assistant

Full-stack AI smart home assistant with holographic face, 3D living room, voice control, and real-time smart home device management.

## Tech Stack
- **Backend**: FastAPI · Mistral AI (native SDK) · LangChain tools · Tavily · OpenWeatherMap
- **Frontend**: React 18 · TypeScript · Three.js · Framer Motion · Web Speech API

## Quick Start

### Backend
```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # fill in your API keys
uvicorn main:app --reload --port 8000
```

### Frontend
```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

### Tests
```powershell
# Backend
python debug_aria.py        # deep diagnostic
python test_backend.py --ws # full test suite

# Frontend
npx tsx test_frontend.ts    # full test suite
```

## Features
- 🤖 Mistral AI agent with 11 smart home tools
- 🏠 3D PBR living room with real-time device animations
- 🎤 Voice control (Web Speech API)
- 📍 Auto geolocation → weather/news for your city
- 🌤️ Live weather + real-time news ticker
- 💡 Lights, curtains, fan, TV, music, thermostat
- 🔌 WebSocket + REST fallback
- 🎵 Retro music player with floating note sprites

## API Keys Required
- [Mistral AI](https://console.mistral.ai/) — free tier available
- [OpenWeatherMap](https://openweathermap.org/api) — free tier
- [Tavily](https://tavily.com/) — free tier

## See ARIA_HANDOFF_v2.md for full technical documentation.
