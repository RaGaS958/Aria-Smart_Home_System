<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=13&duration=3000&pause=1500&color=00E5FF&center=true&vCenter=true&width=600&lines=INITIALIZING+ARIA+CORE...;LOADING+MISTRAL+AI+ENGINE...;CONNECTING+SMART+HOME+DEVICES...;SYSTEM+ONLINE" alt="boot sequence" />

<br/>

<!-- 3D ARIA Logo — radial depth + glow rings -->
<svg width="160" height="160" viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="orb" cx="38%" cy="32%" r="65%">
      <stop offset="0%"   stop-color="#00e5ff" stop-opacity="1"/>
      <stop offset="45%"  stop-color="#0077ff" stop-opacity="1"/>
      <stop offset="100%" stop-color="#000d1a" stop-opacity="1"/>
    </radialGradient>
    <radialGradient id="ring1" cx="50%" cy="50%" r="50%">
      <stop offset="70%"  stop-color="#00e5ff" stop-opacity="0"/>
      <stop offset="100%" stop-color="#00e5ff" stop-opacity="0.35"/>
    </radialGradient>
    <radialGradient id="ring2" cx="50%" cy="50%" r="50%">
      <stop offset="70%"  stop-color="#0044ff" stop-opacity="0"/>
      <stop offset="100%" stop-color="#0044ff" stop-opacity="0.18"/>
    </radialGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3.5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="shadow">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#00e5ff" flood-opacity="0.4"/>
    </filter>
  </defs>
  <!-- outer glow rings -->
  <circle cx="80" cy="80" r="78" fill="url(#ring2)"/>
  <circle cx="80" cy="80" r="64" fill="url(#ring1)"/>
  <!-- main orb -->
  <circle cx="80" cy="80" r="52" fill="url(#orb)" filter="url(#shadow)"/>
  <!-- specular highlight -->
  <ellipse cx="64" cy="60" rx="14" ry="9" fill="white" opacity="0.18"/>
  <!-- ARIA text -->
  <text x="80" y="87" text-anchor="middle" font-family="JetBrains Mono, monospace" font-weight="700"
        font-size="22" fill="#00e5ff" filter="url(#glow)" letter-spacing="3">ARIA</text>
  <!-- circuit lines -->
  <line x1="80" y1="132" x2="80" y2="148" stroke="#00e5ff" stroke-width="1.5" opacity="0.6"/>
  <line x1="68" y1="142" x2="92" y2="142" stroke="#00e5ff" stroke-width="1.5" opacity="0.6"/>
  <circle cx="68" cy="142" r="2" fill="#00e5ff" opacity="0.8"/>
  <circle cx="92" cy="142" r="2" fill="#00e5ff" opacity="0.8"/>
</svg>

<br/>

# ARIA — Advanced Responsive Intelligence Assistant

**Full-stack AI smart home system. Holographic pixel-art face, PBR 3D living room,**  
**live weather, real-time news, voice control, Mistral AI reasoning engine.**

<br/>

<!-- Tech stack badges -->
<img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/Mistral_AI-small--2506-ff7000?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIGZpbGw9IiNmZjcwMDAiIHJ4PSI0Ii8+PC9zdmc+&logoColor=white"/>
<img src="https://img.shields.io/badge/React-18-61dafb?style=for-the-badge&logo=react&logoColor=black"/>
<img src="https://img.shields.io/badge/Three.js-PBR-000000?style=for-the-badge&logo=threedotjs&logoColor=white"/>
<img src="https://img.shields.io/badge/TypeScript-5-3178c6?style=for-the-badge&logo=typescript&logoColor=white"/>
<img src="https://img.shields.io/badge/Vite-5-646cff?style=for-the-badge&logo=vite&logoColor=white"/>

<br/><br/>

<img src="https://img.shields.io/badge/Backend-Hugging_Face_Spaces-ffce00?style=for-the-badge&logo=huggingface&logoColor=black"/>
<img src="https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white"/>
<img src="https://img.shields.io/badge/WebSocket-Real--time-4caf50?style=for-the-badge&logo=socketdotio&logoColor=white"/>
<img src="https://img.shields.io/badge/Quality_Score-90%25-00e676?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Tests-36%2F40_Passing-00b0ff?style=for-the-badge"/>

<br/>

<!-- Live links -->
[![Live Demo](https://img.shields.io/badge/LIVE_DEMO-aria--smart--home--system.vercel.app-00e5ff?style=flat-square&logo=vercel)](https://aria-smart-home-system.vercel.app/)
[![API Health](https://img.shields.io/badge/API-ragas111--aria--smarthome--backned.hf.space-ffce00?style=flat-square&logo=huggingface)](https://ragas111-aria-smarthome-backned.hf.space/api/health)

</div>

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Data Flow — WebSocket Protocol](#data-flow--websocket-protocol)
- [Agent Reasoning Loop](#agent-reasoning-loop)
- [Smart Home Tool Matrix](#smart-home-tool-matrix)
- [Emotion System](#emotion-system)
- [Three.js Room Layout](#threejs-room-layout)
- [API Reference](#api-reference)
- [Quality Test Analytics](#quality-test-analytics)
- [Deployment Architecture](#deployment-architecture)
- [File Structure](#file-structure)
- [Environment Setup](#environment-setup)

---

## System Architecture

```mermaid
graph TB
    subgraph CLIENT["CLIENT — Vercel"]
        direction TB
        UI["React 18 + TypeScript"]
        THREE["Three.js PBR Room"]
        FACE["Pixel-Art ARIA Face"]
        VOICE["Web Speech API"]
        UI --> THREE
        UI --> FACE
        UI --> VOICE
    end

    subgraph COMMS["TRANSPORT LAYER"]
        WS["WebSocket /ws/agent"]
        REST["REST /api/chat fallback"]
    end

    subgraph BACKEND["BACKEND — Hugging Face Spaces"]
        direction TB
        FA["FastAPI"]
        AGENT["invoke_agent()"]
        MISTRAL["Mistral SDK\nmistral-small-2506"]
        TOOLS["11 LangChain Tools"]
        SCHED["News Scheduler\n10 min cycle"]

        FA --> AGENT
        AGENT --> MISTRAL
        MISTRAL -->|"tool_calls"| TOOLS
        TOOLS -->|"tool results"| MISTRAL
        SCHED --> FA
    end

    subgraph EXTERNAL["EXTERNAL APIs"]
        OWM["OpenWeatherMap"]
        TAV["Tavily Search"]
        MIS["Mistral API\napi.mistral.ai"]
    end

    CLIENT <-->|"ws:// + city"| WS
    CLIENT <-->|"POST + history"| REST
    WS --> FA
    REST --> FA
    TOOLS --> OWM
    TOOLS --> TAV
    MISTRAL --> MIS

    style CLIENT fill:#0a1628,stroke:#00e5ff,stroke-width:2px,color:#fff
    style BACKEND fill:#0d1f0d,stroke:#00c853,stroke-width:2px,color:#fff
    style COMMS fill:#1a1228,stroke:#7c4dff,stroke-width:2px,color:#fff
    style EXTERNAL fill:#1a1200,stroke:#ffab00,stroke-width:2px,color:#fff
```

---

## Tech Stack

<div align="center">

<!-- Row 1: Backend icons -->
<svg width="760" height="90" viewBox="0 0 760 90" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="cardBg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#141e2e"/>
      <stop offset="100%" stop-color="#0a1020"/>
    </linearGradient>
    <linearGradient id="teal3d" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#26d7c0"/>
      <stop offset="100%" stop-color="#009688"/>
    </linearGradient>
    <linearGradient id="blue3d" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#64b5f6"/>
      <stop offset="100%" stop-color="#1565c0"/>
    </linearGradient>
    <linearGradient id="orange3d" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffb74d"/>
      <stop offset="100%" stop-color="#e65100"/>
    </linearGradient>
    <linearGradient id="purple3d" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#b39ddb"/>
      <stop offset="100%" stop-color="#4527a0"/>
    </linearGradient>
    <linearGradient id="green3d" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#81c784"/>
      <stop offset="100%" stop-color="#1b5e20"/>
    </linearGradient>
    <filter id="card-shadow">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity="0.5"/>
    </filter>
  </defs>

  <!-- FastAPI -->
  <rect x="4" y="8" width="130" height="74" rx="10" fill="url(#cardBg)" filter="url(#card-shadow)" stroke="#009688" stroke-width="1"/>
  <circle cx="34" cy="35" r="14" fill="url(#teal3d)"/>
  <text x="34" y="40" text-anchor="middle" font-family="monospace" font-size="11" font-weight="bold" fill="white">FA</text>
  <text x="69" y="33" font-family="monospace" font-size="11" font-weight="700" fill="#26d7c0">FastAPI</text>
  <text x="69" y="48" font-family="monospace" font-size="9" fill="#546e7a">0.111.0</text>
  <text x="69" y="63" font-family="monospace" font-size="8" fill="#37474f">Python 3.11</text>

  <!-- Mistral -->
  <rect x="144" y="8" width="130" height="74" rx="10" fill="url(#cardBg)" filter="url(#card-shadow)" stroke="#ff7000" stroke-width="1"/>
  <circle cx="174" cy="35" r="14" fill="url(#orange3d)"/>
  <text x="174" y="40" text-anchor="middle" font-family="monospace" font-size="10" font-weight="bold" fill="white">MIS</text>
  <text x="208" y="33" font-family="monospace" font-size="11" font-weight="700" fill="#ffb74d">Mistral AI</text>
  <text x="208" y="48" font-family="monospace" font-size="9" fill="#546e7a">small-2506</text>
  <text x="208" y="63" font-family="monospace" font-size="8" fill="#37474f">Native SDK</text>

  <!-- LangChain -->
  <rect x="284" y="8" width="130" height="74" rx="10" fill="url(#cardBg)" filter="url(#card-shadow)" stroke="#4527a0" stroke-width="1"/>
  <circle cx="314" cy="35" r="14" fill="url(#purple3d)"/>
  <text x="314" y="40" text-anchor="middle" font-family="monospace" font-size="10" font-weight="bold" fill="white">LC</text>
  <text x="348" y="33" font-family="monospace" font-size="11" font-weight="700" fill="#b39ddb">LangChain</text>
  <text x="348" y="48" font-family="monospace" font-size="9" fill="#546e7a">0.2.1</text>
  <text x="348" y="63" font-family="monospace" font-size="8" fill="#37474f">@tool decorators</text>

  <!-- Tavily -->
  <rect x="424" y="8" width="130" height="74" rx="10" fill="url(#cardBg)" filter="url(#card-shadow)" stroke="#1565c0" stroke-width="1"/>
  <circle cx="454" cy="35" r="14" fill="url(#blue3d)"/>
  <text x="454" y="40" text-anchor="middle" font-family="monospace" font-size="10" font-weight="bold" fill="white">TV</text>
  <text x="488" y="33" font-family="monospace" font-size="11" font-weight="700" fill="#64b5f6">Tavily</text>
  <text x="488" y="48" font-family="monospace" font-size="9" fill="#546e7a">Search API</text>
  <text x="488" y="63" font-family="monospace" font-size="8" fill="#37474f">News + Web</text>

  <!-- OpenWeather -->
  <rect x="564" y="8" width="182" height="74" rx="10" fill="url(#cardBg)" filter="url(#card-shadow)" stroke="#1b5e20" stroke-width="1"/>
  <circle cx="594" cy="35" r="14" fill="url(#green3d)"/>
  <text x="594" y="40" text-anchor="middle" font-family="monospace" font-size="9" font-weight="bold" fill="white">OWM</text>
  <text x="618" y="33" font-family="monospace" font-size="11" font-weight="700" fill="#81c784">OpenWeather</text>
  <text x="618" y="48" font-family="monospace" font-size="9" fill="#546e7a">Map API v2.5</text>
  <text x="618" y="63" font-family="monospace" font-size="8" fill="#37474f">Real-time weather</text>
</svg>

</div>

| Layer | Technology | Purpose |
|---|---|---|
| **AI Engine** | Mistral `mistral-small-2506` — native SDK | Reasoning, tool selection, emotion tagging |
| **Backend** | FastAPI + Uvicorn | REST + WebSocket server |
| **Tools** | LangChain `@tool` decorators | Smart home + info tool definitions |
| **Frontend** | React 18 + TypeScript + Vite | SPA with hooks-based architecture |
| **3D Renderer** | Three.js — PBR materials, PCFSoftShadows | Immersive living room scene |
| **Animation** | Framer Motion | Page transitions, chat UI |
| **Voice** | Web Speech API | STT input, single-utterance mode |
| **Search** | Tavily AI Search | News headlines, topic search |
| **Weather** | OpenWeatherMap v2.5 | Real-time conditions + icons |
| **Geolocation** | Nominatim (OpenStreetMap) | Reverse geocode lat/lng to city |
| **Deploy: API** | Hugging Face Spaces — Docker SDK | Port 7860, Python 3.11-slim |
| **Deploy: UI** | Vercel — Vite framework | SPA rewrites, edge CDN |

---

## Features

```mermaid
mindmap
  root((ARIA))
    Smart Home
      Lights on/off/dim
      Curtains open/close
      Fan speed 1-3
      Thermostat C
      TV control
      Music by mood
    Intelligence
      Auto city detection
      Scene inference
      Synonym understanding
      Context memory
      Multi-command chaining
    Conversation
      Emotion-tagged responses
      Concise confirmations
      Graceful fallbacks
      Multi-turn math
      Personality
    3D Room
      PBR materials
      Mouse orbit 360deg
      Pinch zoom touch
      Animated curtains
      TV scanlines
      VU meter bounce
      Music note sprites
      ARIA orb pulses
    Real-time
      WebSocket duplex
      REST fallback
      News scheduler 10min
      Weather polling
      Voice STT
```

---

## Data Flow — WebSocket Protocol

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant WS as WebSocket /ws/agent
    participant AG as invoke_agent()
    participant MIS as Mistral API
    participant TL as Tool Executor

    B->>WS: {type:"set_city", city:"Lucknow"}
    WS-->>B: {type:"city_set", city:"Lucknow"}

    B->>WS: {type:"chat", message:"Turn on the fan.", city:"Lucknow"}
    WS-->>B: {type:"emotion", emotion:"thinking"}

    WS->>AG: invoke_agent(msg, history, "Lucknow")
    AG->>MIS: chat.complete(messages, tools=MISTRAL_TOOLS)
    MIS-->>AG: tool_calls: [control_fan(room="living room", action="on", speed=2)]

    AG->>TL: asyncio.wait_for(tool.invoke(args), 8s)
    TL-->>AG: "[HOME] Fan in the living room is ON — speed: Medium"

    AG->>MIS: chat.complete(messages + tool_result)
    MIS-->>AG: "[EMOTION:happy] Fan is running on medium speed!"

    AG-->>WS: {response, emotion:"happy", condition:null}
    WS-->>B: {type:"response", message:"...", emotion:"happy"}
    B->>B: inferHomeState() updates fanOn=true, fanSpeed=2
    B->>B: Three.js fan starts spinning
```

---

## Agent Reasoning Loop

```mermaid
flowchart TD
    A([User Input]) --> B[Build messages array\nSYSTEM + history + user]
    B --> C{Round counter\nmax 3}
    C -->|round 1-3| D[Mistral chat.complete\ntimeout 18s]
    D --> E{tool_calls\nin response?}
    E -->|No| F[parse_response\nstrip EMOTION tag\nextract condition]
    F --> G([Return result dict\nresponse + emotion + condition])
    E -->|Yes| H[Append assistant message\nwith tool_call IDs]
    H --> I[For each tool_call\ntimeout 8s per tool]
    I --> J{Tool found\nin _tool_map?}
    J -->|Yes| K[asyncio.to_thread\ntool.invoke args]
    J -->|No| L[Unknown tool error string]
    K --> M[Append tool result\nrole: tool]
    L --> M
    M --> C
    C -->|limit reached| N[force_text=True\nfinal Mistral call]
    N --> G

    style A fill:#00e5ff,color:#000,font-weight:bold
    style G fill:#00c853,color:#000,font-weight:bold
    style D fill:#1a237e,color:#fff
    style N fill:#b71c1c,color:#fff
```

---

## Smart Home Tool Matrix

```mermaid
flowchart LR
    subgraph INPUT["User Input"]
        U1["Turn on the fan"]
        U2["Open the curtains"]
        U3["Dim the lights"]
        U4["Movie night"]
        U5["Play jazz"]
        U6["Set temp 22C"]
    end

    subgraph PARSE["Mistral Parses Intent"]
        I1["control_fan\nroom=living room\naction=on speed=2"]
        I2["control_curtains\nroom=living room\naction=open"]
        I3["control_lights\nroom=living room\naction=dim brightness=40"]
        I4["control_tv + control_lights\n+ control_curtains\nSCENE chain"]
        I5["play_music\nmood=jazz"]
        I6["control_thermostat\ntemp=22 mode=auto"]
    end

    subgraph TOOLS["Tool Execution"]
        T1["[HOME] Fan ON — Medium"]
        T2["[HOME] Curtains opened"]
        T3["[HOME] Lights dim 40%"]
        T4["[HOME] TV ON\n[HOME] Lights 30%\n[HOME] Curtains closed"]
        T5["[HOME] Now playing: Late Night Jazz"]
        T6["[HOME] Thermostat 22C auto"]
    end

    U1 --> I1 --> T1
    U2 --> I2 --> T2
    U3 --> I3 --> T3
    U4 --> I4 --> T4
    U5 --> I5 --> T5
    U6 --> I6 --> T6

    style INPUT fill:#0d1b2a,stroke:#00e5ff,color:#fff
    style PARSE fill:#1a0d2e,stroke:#7c4dff,color:#fff
    style TOOLS fill:#0d200d,stroke:#00c853,color:#fff
```

### All 11 Tools

| Tool | Parameters | Default |
|---|---|---|
| `get_weather` | `city: str` | uses detected city |
| `get_current_time` | — | system clock |
| `get_latest_news` | `topic: str = "world"` | world headlines |
| `set_timer` | `label: str, minutes: int` | — |
| `tell_joke` | — | random tech joke |
| `control_lights` | `room, action, brightness=100` | living room |
| `control_curtains` | `room, action` | living room |
| `control_fan` | `room, action, speed=2` | living room, medium |
| `control_thermostat` | `temperature, mode="auto"` | auto mode |
| `play_music` | `mood="chill"` | lo-fi chill |
| `control_tv` | `action, channel=None` | — |

---

## Emotion System

```mermaid
stateDiagram-v2
    direction LR

    [*] --> idle : startup
    idle --> thinking : tool call initiated
    idle --> happy : task completed
    idle --> speaking : giving info
    idle --> sad : error / user upset
    idle --> excited : cool discovery
    idle --> surprised : unexpected event
    idle --> sleeping : 30s silence

    thinking --> happy : tool success
    thinking --> speaking : info returned
    thinking --> sad : tool timeout / error

    sad --> idle : next interaction
    sleeping --> idle : user speaks
    happy --> idle : confirmed
    speaking --> idle : done
    excited --> happy : follow-up
    surprised --> speaking : elaborates

    note right of thinking
        Emitted to WS as:
        type:"emotion" emotion:"thinking"
        BEFORE Mistral call completes
    end note

    note right of sad
        Trigger: user says
        "I feel awful / sad /
        terrible / depressed"
        No jokes — empathy only
    end note
```

**Format in every Mistral response:**

```
[EMOTION:happy] Fan is running at medium speed!
  ^─ canonical tag stripped by parse_response()
```

`parse_response()` handles: `[EMOTION:happy]` / `[EMOTION: happy]` / `[happy]` shorthand — all normalised to the same output dict.

---

## Three.js Room Layout

```mermaid
graph TD
    subgraph ROOM["Living Room  14 x 14 units"]
        direction LR
        WIN["Window\n-4.92, 2.8, -1.5\nleft wall"]
        CURT["Curtains\nopen: z -3.05 / -0.05\nclosed: z -1.9 / -1.1"]
        SOFA["Sofa\n-1.0, 0, -3.0"]
        TV["TV + Console\n3.1, 0, -4.38\nback wall right"]
        BOOK["Bookshelf\n4.6, 0, 0.5\nright wall -90deg"]
        DESK["Desk + ARIA Orb\n2.2, 0, 0.8"]
        COF["Coffee Table + Stereo\n-0.8, 0, 0.8"]
        LAMP["Arc Floor Lamp\n-2.8, 0, 0.5"]

        WIN --- CURT
        LAMP --- COF
        COF --- SOFA
        SOFA --- TV
        DESK --- BOOK
    end

    subgraph ANIM["Animated Objects"]
        A1["Curtains — lerp + lining"]
        A2["Ceiling fan — *0.04"]
        A3["Table fan — *0.09"]
        A4["Lamp — intensity lerp"]
        A5["TV — colour cycling + scanlines"]
        A6["Stereo — VU meter bounce"]
        A7["Music notes — 12 sprites float"]
        A8["ARIA orb — emotion colour + pulse"]
    end

    subgraph CAMERA["Camera Controls"]
        C1["Left drag — orbit 360 H / +/-0.28 V"]
        C2["Right drag — pan lookAt x:-4..4 y:0..3.5"]
        C3["Scroll/Pinch — zoom 1.5..12m factor 0.93/1.08"]
        C4["RESET btn — snap default z=6.8"]
    end

    style ROOM fill:#0a1628,stroke:#00e5ff,color:#ccc
    style ANIM fill:#1a0d00,stroke:#ff7000,color:#ccc
    style CAMERA fill:#0d1f0d,stroke:#00c853,color:#ccc
```

**Renderer config:** `ACESFilmicToneMapping` — `PCFSoftShadowMap` — `exposure=0.95` — `FOV=62°`

---

## API Reference

```mermaid
graph LR
    subgraph REST["REST Endpoints"]
        H["GET /api/health\nstatus + version"]
        C["POST /api/chat\nbody: message history city\nreturns: response emotion condition"]
        W["GET /api/weather/:city\ntemp feels_like desc condition icon"]
        N["GET /api/news\ncached Tavily articles"]
        T["GET /api/time\ntime date hour is_night"]
    end

    subgraph WS["WebSocket /ws/agent"]
        direction TB
        CS["CLIENT sends"]
        SR["SERVER sends"]
        CS --- c1["type:chat  message city"]
        CS --- c2["type:set_city  city"]
        CS --- c3["type:ping"]
        CS --- c4["type:clear_history"]
        SR --- s1["type:emotion  emotion:thinking"]
        SR --- s2["type:response  message emotion condition"]
        SR --- s3["type:city_set  city"]
        SR --- s4["type:pong"]
        SR --- s5["type:news_update  data:articles"]
    end

    style REST fill:#0a1628,stroke:#00e5ff,color:#ccc
    style WS fill:#0d1f0d,stroke:#00c853,color:#ccc
```

---

## Quality Test Analytics

**40 test cases across 6 categories — run via `python test_aria_quality.py`**

```mermaid
pie title Test Results by Category (36/40 Passing — 90%)
    "Tools — 8/10" : 8
    "Intelligence — 9/10" : 9
    "Conversation — 8/8" : 8
    "Emotion — 4/5" : 4
    "Edge Cases — 4/4" : 4
    "Multi-step — 3/3" : 3
```

```mermaid
xychart-beta
    title "Response Time by Test (ms) — avg 1614ms, 0 slow above 6s"
    x-axis ["T14","T20","T11","T02","T12","T30","T13","T01","T28","T06"]
    y-axis "ms" 0 --> 6000
    bar [5475, 4795, 4424, 4325, 3828, 2969, 2486, 2321, 2163, 1870]
    line [1614, 1614, 1614, 1614, 1614, 1614, 1614, 1614, 1614, 1614]
```

```mermaid
quadrantChart
    title Test Failure Analysis — Fixed vs Pending
    x-axis "Low Impact" --> "High Impact"
    y-axis "Hard to Fix" --> "Easy to Fix"
    quadrant-1 Quick Wins
    quadrant-2 Strategic
    quadrant-3 Backlog
    quadrant-4 Major Effort
    T04 Curtains OPEN: [0.6, 0.8]
    T06 Fan default speed: [0.65, 0.75]
    T31 Sad emotion: [0.55, 0.85]
    T17 Movie scene warn: [0.7, 0.7]
```

**Resolved failures** — SYSTEM_PROMPT patches in `main.py`:

| Test | Input | Before | After |
|---|---|---|---|
| [04] | "Open the curtains." | Fan suggestion instead | `control_curtains("open")` fires immediately |
| [06] | "Turn on the fan." | Weather commentary | `control_fan("on", 2)` fires immediately |
| [31] | "I feel really awful today." | Joke + `happy` emotion | Empathy + `sad` emotion |
| [17] | "Set up a movie night." | 1 device only | TV + dim lights + curtains chained |

---

## Deployment Architecture

```mermaid
graph TB
    subgraph DEV["Local Development"]
        LBACK["uvicorn main:app\nlocalhost:8000"]
        LFRONT["npm run dev\nlocalhost:5173"]
        LBACK <-->|"ws://localhost:8000/ws/agent"| LFRONT
    end

    subgraph GIT["GitHub Repository"]
        ROOT["/ root\n.gitignore"]
        BDIR["backend/\nDockerfile\n.dockerignore\nmain.py\nrequirements.txt"]
        FDIR["frontend/\nvercel.json\nsrc/App.tsx"]
        ROOT --> BDIR
        ROOT --> FDIR
    end

    subgraph CICD["CI / CD"]
        HF["Hugging Face Spaces\nDocker build\npython:3.11-slim\nport 7860"]
        VER["Vercel\nnpm run build\nVite output /dist\nSPA rewrites"]
    end

    subgraph PROD["Production"]
        PBACK["ragas111-aria-smarthome-backned\n.hf.space\nMISTRAL_API_KEY\nOPENWEATHER_API_KEY\nTAVILY_API_KEY"]
        PFRONT["aria-smart-home-system\n.vercel.app\nVITE_API_URL\nVITE_WS_URL"]
        PBACK <-->|"wss:// WebSocket"| PFRONT
    end

    GIT --> CICD
    CICD --> PROD

    style DEV fill:#1a1a00,stroke:#ffab00,color:#ccc
    style GIT fill:#0a1628,stroke:#6e6e6e,color:#ccc
    style CICD fill:#1a0d2e,stroke:#7c4dff,color:#ccc
    style PROD fill:#0d1f0d,stroke:#00c853,color:#ccc
```

---

## File Structure

```
ARIA/
├── .gitignore                     # root — covers backend + frontend
│
├── backend/                       # Hugging Face Spaces repo root
│   ├── Dockerfile                 # python:3.11-slim, port 7860
│   ├── .dockerignore              # excludes tests, htmlcov, venv
│   ├── README.md                  # HF Spaces YAML frontmatter
│   ├── requirements.txt           # production deps only
│   ├── requirements-test.txt      # pytest, ruff, mypy, coverage
│   ├── .env                       # secrets — never committed
│   ├── .env.example               # template — safe to commit
│   │
│   ├── main.py                    # FastAPI app — 620 lines
│   │   ├── 11 LangChain @tools
│   │   ├── SYSTEM_PROMPT          # emotion + device rules
│   │   ├── parse_response()       # strips EMOTION tags
│   │   ├── _sanitize_history()    # alternating roles, 8-msg cap
│   │   ├── invoke_agent()         # Mistral loop, 3 rounds max
│   │   ├── news_scheduler()       # Tavily every 10 min
│   │   └── WebSocket /ws/agent    # full-duplex with city support
│   │
│   ├── test_aria_quality.py       # 40 quality test cases
│   ├── test_backend.py            # 107 assertions
│   └── debug_aria.py              # deep diagnostic tool
│
└── frontend/                      # Vercel repo root
    ├── vercel.json                # SPA rewrites + security headers
    ├── .env.production            # VITE_API_URL → hf.space
    ├── .env.development           # localhost:8000
    ├── .env.example               # template
    │
    ├── src/
    │   └── App.tsx                # entire frontend — 2639 lines
    │       ├── LoadingScreen      # boot log, sessionStorage skip
    │       ├── HomePage           # ARIA face + feature badges
    │       ├── RoomPage           # 68% Three.js + 32% UI
    │       ├── AboutPage          # tech stack
    │       ├── useAgent()         # WS + REST hook, auto-reconnect
    │       ├── useWeather()       # 10 min polling
    │       ├── inferHomeState()   # regex → device state sync
    │       └── Three.js PBR Room  # full scene with all animations
    │
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    └── vite.config.ts
```

---

## Environment Setup

### Backend — local

```bash
cd backend
python -m venv Aria-backend
source Aria-backend/bin/activate        # Windows: Aria-backend\Scripts\activate
pip install -r requirements-test.txt

# create .env from template
cp .env.example .env
# fill in MISTRAL_API_KEY, OPENWEATHER_API_KEY, TAVILY_API_KEY

uvicorn main:app --reload --port 8000
```

### Frontend — local

```bash
cd frontend
npm install
cp .env.example .env.development        # already points to localhost:8000
npm run dev
```

### Run quality tests

```bash
cd backend
python test_aria_quality.py              # all 40 cases
python test_aria_quality.py --cat tools  # category filter
python test_aria_quality.py --only 31    # single test
python test_aria_quality.py --verbose --save report.json
```

### Docker — local preview

```bash
cd backend
docker build -t aria-backend .
docker run -p 7860:7860 \
  -e MISTRAL_API_KEY=... \
  -e OPENWEATHER_API_KEY=... \
  -e TAVILY_API_KEY=... \
  aria-backend
```

---

## Known Issues / Roadmap

```mermaid
gantt
    title ARIA Roadmap
    dateFormat  YYYY-MM
    section Stability
    Thermostat stale state fix        :done,    s1, 2026-05, 1d
    WebSocket reconnect hardening     :done,    s2, 2026-05, 1d
    Dependency conflict resolution    :done,    s3, 2026-05, 1d
    section Quality
    Test score 90 percent             :done,    q1, 2026-05, 1d
    SYSTEM_PROMPT device vs weather   :done,    q2, 2026-05, 1d
    Target 100 percent tests          :active,  q3, 2026-05, 2026-06
    section Accessibility
    aria-label mic and send buttons   :         a1, 2026-06, 1d
    prefers-reduced-motion check      :         a2, 2026-06, 1d
    WCAG AA contrast inactive icons   :         a3, 2026-06, 1d
    section Performance
    InstancedMesh music notes 12x     :         p1, 2026-06, 1d
    Throttle mousemove orbit rAF      :         p2, 2026-06, 1d
    Dispose Three.js geometries       :         p3, 2026-06, 1d
    section Features
    TTS speechSynthesis ARIA voice    :         f1, 2026-07, 1d
    Continuous voice hands-free mode  :         f2, 2026-07, 1d
    Persistent chat localStorage      :         f3, 2026-07, 1d
    Day night sky cycle Three.js      :         f4, 2026-07, 1d
    ARIA idle animations 30s          :         f5, 2026-07, 1d
    Rate limit api chat 20 per min    :         f6, 2026-07, 1d
```

---

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=11&duration=4000&pause=2000&color=00E5FF&center=true&vCenter=true&width=500&lines=Built+with+FastAPI+%C2%B7+Mistral+AI+%C2%B7+React+%C2%B7+Three.js;Deployed+on+Hugging+Face+Spaces+%2B+Vercel;90%25+quality+score+%C2%B7+36%2F40+tests+passing" alt="footer" />

<br/>

[![Live](https://img.shields.io/badge/LIVE-aria--smart--home--system.vercel.app-00e5ff?style=for-the-badge)](https://aria-smart-home-system.vercel.app/)

</div>
