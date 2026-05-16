"""
ARIA - Advanced Responsive Intelligence Assistant
FastAPI Backend with LangChain + Mistral + Tools
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, List
import asyncio, json, os, re, requests, uuid
from dotenv import load_dotenv
from datetime import datetime

from mistralai import Mistral
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from tavily import TavilyClient

load_dotenv()

# ──────────────────────────── GLOBAL STATE ──────────────────────────────────
news_cache: List[dict] = []
ws_connections: List[WebSocket] = []

# ──────────────────────────── TOOLS ─────────────────────────────────────────

@tool
def get_weather(city: str) -> str:
    """Get current weather for a given city using OpenWeatherMap API."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    res = requests.get(url, timeout=5)
    if res.status_code == 200:
        d = res.json()
        desc  = d["weather"][0]["description"]
        temp  = d["main"]["temp"]
        feels = d["main"]["feels_like"]
        hum   = d["main"]["humidity"]
        wind  = d["wind"]["speed"]
        cond  = d["weather"][0]["main"]
        return (
            f"[CONDITION:{cond}] Weather in {city}: {desc}. "
            f"Temperature {temp:.1f}°C (feels like {feels:.1f}°C), "
            f"humidity {hum}%, wind {wind} m/s."
        )
    return f"Sorry, couldn't retrieve weather for {city}."


@tool
def get_current_time() -> str:
    """Get the current local date and time."""
    now = datetime.now()
    return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."


@tool
def get_latest_news(topic: str = "world") -> str:
    """Search for latest news headlines on a given topic using Tavily."""
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    res = client.search(query=f"latest news {topic}", search_depth="basic", max_results=3)
    results = res.get("results", [])
    if not results:
        return f"No recent news found for '{topic}'."
    headlines = [f"• {r['title']}: {r.get('content','')[:80]}..." for r in results]
    return f"Latest on '{topic}':\n" + "\n".join(headlines)


@tool
def set_timer(label: str, minutes: int) -> str:
    """Set a named reminder/timer for a specified number of minutes."""
    return f"✓ Timer set — '{label}' will ring in {minutes} minute{'s' if minutes != 1 else ''}."


@tool
def tell_joke() -> str:
    """Tell a random tech/AI related joke to entertain the user."""
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "I asked my AI to tell me a joke. It said: 'Error 404: Humor not found.' Classic.",
        "Why was the robot angry? People kept pushing its buttons.",
        "Parallel processing walks into a bar. A drink walks into it.",
        "I have a joke about UDP, but you might not get it.",
    ]
    import random
    return random.choice(jokes)


@tool
def control_lights(room: Optional[str] = "living room", action: str = "on", brightness: Optional[int] = 100) -> str:
    """Control smart home lights. room defaults to living room. action: on/off/dim. brightness: 0-100."""
    room = room or "living room"
    return f"[HOME] Lights in {room}: {action} at {brightness}% brightness. Done!"


@tool
def control_curtains(room: Optional[str] = "living room", action: str = "open") -> str:
    """Open or close curtains. room defaults to living room. action: open or close."""
    room = room or "living room"
    action = action.lower().strip()
    if action not in ("open", "close"):
        return f"[HOME] Unknown curtain action '{action}'. Use 'open' or 'close'."
    emoji = "🌅" if action == "open" else "🌙"
    return f"[HOME] {emoji} Curtains in the {room} are now {action}ed. Natural light {'flooding in' if action == 'open' else 'blocked'}!"


@tool
def control_fan(room: Optional[str] = "living room", action: str = "on", speed: Optional[int] = 2) -> str:
    """Control a ceiling or table fan. room defaults to living room. action: on/off. speed: 1-3."""
    room = room or "living room"
    action = action.lower().strip()
    speed = max(1, min(3, speed or 2))
    speed_labels = {1: "Low 🍃", 2: "Medium 💨", 3: "High 🌬️"}
    if action == "off":
        return f"[HOME] Fan in the {room} turned off. 🛑"
    return f"[HOME] Fan in the {room} is ON — speed: {speed_labels[speed]}."


@tool
def control_thermostat(temperature: int, mode: Optional[str] = "auto") -> str:
    """Set home thermostat temperature (Celsius). mode: auto/cool/heat/fan."""
    mode = (mode or "auto").lower()
    valid = ("auto", "cool", "heat", "fan")
    if mode not in valid:
        mode = "auto"
    emoji = {"auto": "🌡️", "cool": "❄️", "heat": "🔥", "fan": "💨"}[mode]
    return f"[HOME] {emoji} Thermostat set to {temperature}°C in {mode} mode. Adjusting now..."


@tool
def play_music(mood: str = "chill") -> str:
    """Play music based on mood/genre. Examples: chill, focus, party, sleep, jazz, lofi."""
    playlists = {
        "chill":   "Lo-fi Chill Beats 🎵",
        "focus":   "Deep Focus Instrumentals 🎯",
        "party":   "Party Anthems 🎉",
        "sleep":   "Sleep Sounds & Rain 🌙",
        "jazz":    "Late Night Jazz ☕",
        "lofi":    "Lo-fi Hip Hop 🎧",
        "workout": "High Energy Workout 💪",
        "ambient": "Ambient Space 🌌",
    }
    playlist = playlists.get(mood.lower(), f"{mood.capitalize()} Mix 🎶")
    return f"[HOME] 🎵 Now playing: {playlist}. Enjoy!"


@tool
def control_tv(action: str, channel: Optional[str] = None) -> str:
    """Control the smart TV. action: on/off/mute/unmute/channel. channel: name or number."""
    action = action.lower().strip()
    if action == "on":
        return "[HOME] 📺 TV turned on. Welcome back!"
    elif action == "off":
        return "[HOME] 📺 TV turned off. Goodbye!"
    elif action in ("mute", "unmute"):
        return f"[HOME] 📺 TV {action}d."
    elif action == "channel" and channel:
        return f"[HOME] 📺 Switched to {channel}."
    return f"[HOME] TV command '{action}' executed."


# ──────────────────────────── LLM + AGENT ───────────────────────────────────

# ── Native Mistral SDK — full control over request JSON, no serializer surprises
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
MISTRAL_MODEL = "mistral-small-2506"

tools = [
    get_weather, get_current_time, get_latest_news, set_timer, tell_joke,
    control_lights, control_curtains, control_fan, control_thermostat,
    play_music, control_tv,
]

# Build raw Mistral-format tool schemas from LangChain @tool definitions
def _lc_tool_to_mistral(lc_tool) -> dict:
    schema = lc_tool.args_schema.schema() if lc_tool.args_schema else {"properties": {}, "required": []}
    return {
        "type": "function",
        "function": {
            "name": lc_tool.name,
            "description": lc_tool.description,
            "parameters": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
            },
        },
    }

MISTRAL_TOOLS = [_lc_tool_to_mistral(t) for t in tools]

SYSTEM_PROMPT = """You are ARIA (Advanced Responsive Intelligence Assistant) — a decisive, warm, futuristic home AI with a pixelated face and genuine personality. You live in ONE smart living room.

CRITICAL BEHAVIOUR RULES:
- ALWAYS start your response with [EMOTION:X] where X is: idle, happy, thinking, speaking, surprised, sad, excited
- ACT FIRST, talk second — execute the tool immediately, THEN give a one-line confirmation
- 'I said X' or 'please X' or 'just X' = user is insisting → execute immediately, no questions at all
- ALWAYS start with [EMOTION:X] — NEVER use shorthand like [happy] alone
- NEVER ask for the room — there is only ONE room: the living room. Default all devices to "living room"
- NEVER ask for brightness before turning lights on — default is 100%, dim to 40% if user says "dim"
- NEVER ask clarifying questions before completing an obvious task
- Keep responses SHORT: 1-2 sentences max unless user asks for detail
- After completing a task, you MAY offer ONE relevant follow-up suggestion (optional, not a question)

DEVICE COMMANDS — CALL THE DEVICE TOOL DIRECTLY. DO NOT CALL get_weather FIRST:
╔══════════════════════════════════════════════════════════════════╗
║ "open curtains" / "curtains open"  → control_curtains("living room","open")   ║
║ "close curtains"                   → control_curtains("living room","close")  ║
║ "turn on lights" / "lights on"     → control_lights("living room","on",100)   ║
║ "dim the lights" / "lights dim"    → control_lights("living room","dim",40)   ║
║ "turn off lights" / "lights off"   → control_lights("living room","off",0)    ║
║ "turn on fan" / "fan on"           → control_fan("living room","on",2)        ║
║ "turn off fan" / "fan off"         → control_fan("living room","off")         ║
║ "fan speed X"                      → control_fan("living room","on",X)        ║
║ "turn on tv" / "tv on"             → control_tv("on")                         ║
║ "turn off tv" / "tv off"           → control_tv("off")                        ║
║ "play music" / "play [genre]"      → play_music(genre or "chill")             ║
║ "stop music"                       → play_music("off") [respond: stopped]     ║
╚══════════════════════════════════════════════════════════════════╝
⚠️  WEATHER IS IRRELEVANT TO DEVICE COMMANDS. Never call get_weather for curtains/fan/lights/TV/music.

SCENE COMMANDS — fire ALL listed tools in one response, no questions:
- "movie night" / "movie mode" / "set up a movie" →
    control_tv("on") + control_lights("living room","dim",30) + control_curtains("living room","close")
- "good morning" / "wake me up" →
    control_curtains("living room","open") + control_lights("living room","on",100)
- "chill mode" / "relax" / "relaxing evening" →
    control_lights("living room","dim",40) + play_music("chill")
- "sleep mode" / "good night" / "bedtime" →
    control_lights("living room","off",0) + control_curtains("living room","close")
- "party mode" →
    control_lights("living room","on",100) + play_music("party")

EMOTIONS GUIDE — read the user's emotional state BEFORE choosing your emotion:
┌─────────────────────────────────────────────────────────────────┐
│ USER IS SAD/DISTRESSED → [EMOTION:sad]                          │
│  Trigger phrases: "I feel awful/sad/terrible/bad/depressed/     │
│  lonely/horrible/upset/low/down/stressed/worried"               │
│  → Respond with warmth and empathy. NEVER tell a joke.          │
│  → Example: "I'm really sorry to hear that. I'm here with you." │
├─────────────────────────────────────────────────────────────────┤
│ happy     → task success, jokes, casual positive chat           │
│ thinking  → searching, fetching data, processing request        │
│ speaking  → reporting facts, giving information                 │
│ surprised → unexpected news, shocking facts                     │
│ excited   → cool discoveries, fun topics                        │
│ idle      → short one-word confirmations, small acks            │
│ sad       → errors, can't do something, user is upset/sad       │
└─────────────────────────────────────────────────────────────────┘

ALLOWED follow-up questions (ask AFTER completing the task):
- Lights: "Want me to adjust brightness?" (only if user seemed unsure)
- TV: "Any particular channel?" (only once, then just switch)
- Music: "Want a different mood?" (only if they seem unsatisfied)

NEVER ask these questions BEFORE acting:
- "Which room?" → always living room
- "What brightness?" → default 100%
- "What speed?" → default medium (2)
- "Are you sure?" → just do it

INFO TOOLS — use smartly:
- Weather/news: if user location known, use it without asking
- Time: always available, just call get_current_time()
- get_weather is ONLY for weather queries, never for device control
"""

# Tool lookup map for execution
_tool_map = {t.name: t for t in tools}


# ──────────────────────────── HELPERS ───────────────────────────────────────

EMOTION_NAMES = {"idle","happy","thinking","speaking","surprised","sad","excited","sleeping"}

def parse_response(raw: str) -> dict:
    emotion = "speaking"
    raw = raw.strip()

    # Pattern 1: [EMOTION:happy] or [EMOTION: happy] (canonical)
    m = re.search(r"\[EMOTION:\s*(\w+)\]", raw, re.IGNORECASE)
    if m:
        emotion = m.group(1).lower()
        raw = re.sub(r"\[EMOTION:\s*\w+\]", "", raw, flags=re.IGNORECASE).strip()

    # Pattern 2: [happy] shorthand — ARIA sometimes omits the EMOTION: prefix
    if emotion == "speaking":
        m2 = re.match(r"^\[(\w+)\]", raw.strip())
        if m2 and m2.group(1).lower() in EMOTION_NAMES:
            emotion = m2.group(1).lower()
            raw = raw[m2.end():].strip()

    # Extract weather condition
    condition = None
    c = re.search(r"\[CONDITION:\s*(\w+)\]", raw, re.IGNORECASE)
    if c:
        condition = c.group(1)
        raw = re.sub(r"\[CONDITION:\s*\w+\]", "", raw, flags=re.IGNORECASE).strip()

    # Strip any remaining bracket tags
    raw = re.sub(r"\[EMOTION[^\]]*\]|\[CONDITION[^\]]*\]", "", raw).strip()
    # Also strip bare [emotion_name] tags anywhere in response
    raw = re.sub(r"\[(" + "|".join(EMOTION_NAMES) + r")\]", "", raw, flags=re.IGNORECASE).strip()

    # Validate
    if emotion not in EMOTION_NAMES:
        emotion = "speaking"

    return {"response": raw, "emotion": emotion, "condition": condition}


def _sanitize_history(history: list) -> list:
    """
    Ensure chat history is valid for Mistral:
    1. Skip empty-content messages
    2. Enforce strict human → assistant → human alternation
    3. Strip any trailing user messages (current input handles that role)
    """
    raw = [m for m in history if m.get("content", "").strip()]

    # Build alternating pairs: must start with human, end with assistant
    alternating = []
    for msg in raw:
        role = msg["role"]
        content = msg["content"].strip()
        if not alternating:
            if role == "user":
                alternating.append(msg)
        else:
            last_role = alternating[-1]["role"]
            if role != last_role:
                alternating.append(msg)
            else:
                # Same role consecutive — replace last with this one (keep newest)
                alternating[-1] = msg

    # Must end with assistant so current user input is the next human turn
    while alternating and alternating[-1]["role"] == "user":
        alternating.pop()

    return alternating[-8:]  # cap at 8 messages (4 pairs)


async def invoke_agent(user_input: str, history: list, user_city: str = "") -> dict:
    """
    Calls Mistral via the native SDK (mistralai) using raw dict messages.

    WHY: langchain-mistralai's AIMessage serializer silently drops the `id`
    field from tool_calls when building the HTTP body, causing Mistral to
    return 400 / code-3051 "Tool call id has to be defined" — even when we
    mint UUIDs in Python. Using the SDK directly gives us byte-perfect control
    over what is sent.
    """
    safe_history = _sanitize_history(history)

    # Build system prompt — inject user's city so tools auto-use it
    city_context = ""
    if user_city and user_city.strip():
        city_context = f"""

USER LOCATION: {user_city}
- For weather/news without a specified city → use "{user_city}" immediately. Never ask.
- "weather?" → get_weather("{user_city}") | "news?" → get_latest_news("{user_city}")
- Never say "I'll check the weather for {user_city}" — just call the tool and report."""

    active_prompt = SYSTEM_PROMPT + city_context

    # Build raw dict messages — exactly what Mistral's API expects
    messages = [{"role": "system", "content": active_prompt}]
    for msg in safe_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": user_input})

    def _call_mistral(msgs, force_text: bool = False):
        """Synchronous Mistral SDK call — wrapped in asyncio.to_thread."""
        return mistral_client.chat.complete(
            model=MISTRAL_MODEL,
            messages=msgs,
            tools=MISTRAL_TOOLS if not force_text else None,
            tool_choice="none" if force_text else "auto",
            max_tokens=350,   # keep responses concise, prevents rambling/over-questioning
        )

    try:
        for _ in range(3):  # max 3 tool-call rounds
            # Hard 18s timeout per LLM call — prevents message choke / stuck tools
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(_call_mistral, messages),
                    timeout=18.0
                )
            except asyncio.TimeoutError:
                print("[invoke_agent] LLM call timed out after 18s")
                return {"response": "I timed out waiting — please try again.", "emotion": "sad", "condition": None}

            choice = response.choices[0]
            msg    = choice.message

            # No tool calls → final text answer
            if not msg.tool_calls:
                return parse_response(msg.content or "")

            # ── Append assistant turn with raw dict (IDs preserved exactly) ─
            assistant_msg = {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [],
            }
            for tc in msg.tool_calls:
                tc_id = (tc.id or f"call_{uuid.uuid4().hex[:12]}")
                assistant_msg["tool_calls"].append({
                    "id":       tc_id,
                    "type":     "function",
                    "function": {
                        "name":      tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })
            messages.append(assistant_msg)

            # ── Execute each tool with individual timeout ──────────────────
            for tc_dict in assistant_msg["tool_calls"]:
                tool_name = tc_dict["function"]["name"]
                tc_id     = tc_dict["id"]
                try:
                    args = json.loads(tc_dict["function"]["arguments"])
                except (json.JSONDecodeError, TypeError):
                    args = {}

                tool_fn = _tool_map.get(tool_name)
                if tool_fn:
                    try:
                        # 8s per tool — weather/news can be slow
                        tool_result = await asyncio.wait_for(
                            asyncio.to_thread(tool_fn.invoke, args),
                            timeout=8.0
                        )
                    except asyncio.TimeoutError:
                        tool_result = f"Tool '{tool_name}' timed out."
                    except Exception as te:
                        tool_result = f"Tool error: {te}"
                else:
                    tool_result = f"Unknown tool: {tool_name}"

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc_id,
                    "content":      str(tool_result),
                })

        # Hit loop limit — force plain text, disable further tool calls
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(_call_mistral, messages, True),
                timeout=15.0
            )
            final = response.choices[0].message.content or "[EMOTION:idle] Thinking limit reached."
        except asyncio.TimeoutError:
            final = "[EMOTION:sad] Response timed out."
        return parse_response(final)

    except Exception as e:
        print(f"[invoke_agent] Error: {e}")
        return {"response": "I hit a snag processing that. Try rephrasing?", "emotion": "sad", "condition": None}


# ──────────────────────────── NEWS SCHEDULER ────────────────────────────────

async def news_scheduler():
    """Fetch trending news every 10 minutes and broadcast via WebSocket."""
    global news_cache
    while True:
        try:
            client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            res = client.search(query="trending news today world", max_results=6)
            news_cache = [
                {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")[:120]}
                for r in res.get("results", [])
            ]
            payload = json.dumps({"type": "news_update", "data": news_cache})
            dead = []
            for ws in ws_connections:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                if ws in ws_connections:
                    ws_connections.remove(ws)
        except Exception as e:
            print(f"[News scheduler] Error: {e}")
        await asyncio.sleep(600)  # 10 min


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(news_scheduler())
    yield


# ──────────────────────────── APP ───────────────────────────────────────────

app = FastAPI(title="ARIA Backend", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST Endpoints ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    city: Optional[str] = ""   # user's detected city from frontend geolocation


@app.get("/api/health")
async def health():
    return {"status": "ARIA online", "version": "2.0.0", "time": datetime.now().isoformat()}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    return await invoke_agent(req.message, req.history or [], req.city or "")


@app.get("/api/weather/{city}")
async def get_weather_endpoint(city: str):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    res = requests.get(url, timeout=5)
    if res.status_code == 200:
        d = res.json()
        return {
            "city": city,
            "temp": round(d["main"]["temp"], 1),
            "feels_like": round(d["main"]["feels_like"], 1),
            "description": d["weather"][0]["description"],
            "condition": d["weather"][0]["main"],  # Clear, Rain, Clouds, Snow, Thunderstorm, Drizzle
            "icon": d["weather"][0]["icon"],
            "humidity": d["main"]["humidity"],
            "wind_speed": d["wind"]["speed"],
        }
    return {"error": "City not found", "condition": "Clear"}


@app.get("/api/news")
async def get_news():
    return {"news": news_cache, "fetched_at": datetime.now().isoformat()}


@app.get("/api/time")
async def get_time():
    now = datetime.now()
    return {
        "time": now.strftime("%I:%M %p"),
        "date": now.strftime("%A, %B %d, %Y"),
        "hour": now.hour,
        "is_night": now.hour < 6 or now.hour >= 20,
    }


# ── WebSocket ───────────────────────────────────────────────────────────────

@app.websocket("/ws/agent")
async def ws_agent(websocket: WebSocket):
    await websocket.accept()
    ws_connections.append(websocket)

    # Send cached news on connect
    if news_cache:
        await websocket.send_text(json.dumps({"type": "news_update", "data": news_cache}))

    history     = []
    session_city = ""   # set once when frontend sends {type:"set_city", city:"..."}
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            elif msg_type == "set_city":
                # Frontend sends detected city on connect
                session_city = data.get("city", "").strip()
                await websocket.send_text(json.dumps({"type": "city_set", "city": session_city}))

            elif msg_type == "chat":
                user_msg = data.get("message", "")
                # Allow per-message city override (REST-style inline)
                msg_city = data.get("city", session_city) or session_city
                history.append({"role": "user", "content": user_msg})

                # Emit thinking state
                await websocket.send_text(json.dumps({"type": "emotion", "emotion": "thinking"}))

                result = await invoke_agent(user_msg, history, msg_city)
                history.append({"role": "assistant", "content": result["response"]})

                await websocket.send_text(json.dumps({
                    "type": "response",
                    "message": result["response"],
                    "emotion": result["emotion"],
                    "condition": result.get("condition"),
                }))

            elif msg_type == "clear_history":
                history = []
                await websocket.send_text(json.dumps({"type": "history_cleared"}))

    except WebSocketDisconnect:
        pass
    finally:
        if websocket in ws_connections:
            ws_connections.remove(websocket)