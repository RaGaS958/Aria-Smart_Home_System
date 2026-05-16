---
title: ARIA Backend
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# ARIA — Backend API

FastAPI backend for the ARIA smart home assistant.

**Endpoints:**
- `GET  /api/health` — status check
- `POST /api/chat` — main agent endpoint
- `GET  /api/weather/{city}`
- `GET  /api/news`
- `GET  /api/time`
- `WS   /ws/agent` — WebSocket
