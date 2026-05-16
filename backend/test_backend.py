"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         ARIA — BACKEND TEST SUITE  (test_backend.py)                       ║
║                                                                             ║
║  Tests every tool, endpoint, WebSocket flow, timeout, and edge case.       ║
║                                                                             ║
║  Usage:                                                                    ║
║    python test_backend.py              # full suite                        ║
║    python test_backend.py --fast       # skip slow live-LLM tests          ║
║    python test_backend.py --only 4     # run only section 4                ║
║    python test_backend.py --ws         # include WebSocket tests           ║
║                                                                             ║
║  Requires server running:  uvicorn main:app --reload --port 8000           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys, os, json, time, asyncio, argparse, traceback, re
from dotenv import load_dotenv
load_dotenv()

# ── Colours ──────────────────────────────────────────────────────────────────
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; B = "\033[94m"
C = "\033[96m"; W = "\033[97m"; DIM = "\033[2m"; RST = "\033[0m"

passed = failed = warned = 0

def hdr(t):
    print(f"\n{B}{'─'*70}{RST}\n{W}  {t}{RST}\n{B}{'─'*70}{RST}")

def ok(msg, detail=""):
    global passed; passed += 1
    print(f"  {G}✅ PASS{RST}  {msg}" + (f"  {DIM}{detail}{RST}" if detail else ""))

def fail(msg, detail=""):
    global failed; failed += 1
    print(f"  {R}❌ FAIL{RST}  {msg}" + (f"\n       {R}{detail}{RST}" if detail else ""))

def warn(msg, detail=""):
    global warned; warned += 1
    print(f"  {Y}⚠️  WARN{RST}  {msg}" + (f"  {DIM}{detail}{RST}" if detail else ""))

def info(msg):
    print(f"  {C}ℹ️  INFO{RST}  {DIM}{msg}{RST}")

BASE = "http://localhost:8000"

# ══════════════════════════════════════════════════════════════════════════════
# 1. ENV + IMPORTS
# ══════════════════════════════════════════════════════════════════════════════
def test_env():
    hdr("1 · ENVIRONMENT & IMPORTS")
    for key, minlen in [("MISTRAL_API_KEY",30),("OPENWEATHER_API_KEY",20),("TAVILY_API_KEY",15)]:
        v = os.getenv(key,"")
        if not v:         fail(f"{key} — NOT SET")
        elif len(v)<minlen: warn(f"{key} — suspiciously short", f"{len(v)} chars")
        else:             ok(f"{key}", f"{v[:8]}…")

    for pkg in ["fastapi","uvicorn","mistralai","langchain","tavily","requests","websockets"]:
        try:
            __import__(pkg.replace("-","_"))
            ok(f"import {pkg}")
        except ImportError as e:
            fail(f"import {pkg}", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 2. TOOL UNIT TESTS (offline — no real API)
# ══════════════════════════════════════════════════════════════════════════════
def test_tools_offline():
    hdr("2 · TOOL UNIT TESTS (offline)")
    try:
        import main as m
    except Exception as e:
        fail("Cannot import main.py", str(e)); return

    cases = [
        # (tool_fn, args, checks, label)
        (m.get_current_time,  {},
         [lambda r: re.search(r"\d{1,2}:\d{2}", r)],
         "get_current_time → contains time"),

        (m.set_timer, {"label":"pasta","minutes":5},
         [lambda r: "5" in r, lambda r: "pasta" in r.lower()],
         "set_timer(pasta, 5min)"),

        (m.tell_joke, {},
         [lambda r: len(r) > 15],
         "tell_joke → non-empty"),

        (m.control_lights, {"room":"kitchen","action":"on","brightness":80},
         [lambda r: "kitchen" in r.lower(), lambda r: "80" in r],
         "control_lights(kitchen, on, 80%)"),

        (m.control_lights, {"room":"bedroom","action":"off","brightness":0},
         [lambda r: "bedroom" in r.lower()],
         "control_lights(bedroom, off)"),

        (m.control_curtains, {"room":"living room","action":"open"},
         [lambda r: "open" in r.lower()],
         "control_curtains(open)"),

        (m.control_curtains, {"room":"living room","action":"close"},
         [lambda r: "close" in r.lower() or "clos" in r.lower()],
         "control_curtains(close)"),

        (m.control_curtains, {"room":"hall","action":"invalid"},
         [lambda r: "use" in r.lower() or "unknown" in r.lower()],
         "control_curtains(invalid) → graceful error"),

        (m.control_fan, {"room":"hall","action":"on","speed":1},
         [lambda r: "Low" in r],
         "control_fan(on, speed=1 → Low)"),

        (m.control_fan, {"room":"hall","action":"on","speed":2},
         [lambda r: "Medium" in r],
         "control_fan(on, speed=2 → Medium)"),

        (m.control_fan, {"room":"hall","action":"on","speed":3},
         [lambda r: "High" in r],
         "control_fan(on, speed=3 → High)"),

        (m.control_fan, {"room":"hall","action":"off","speed":1},
         [lambda r: "off" in r.lower()],
         "control_fan(off)"),

        (m.control_fan, {"room":"hall","action":"on","speed":99},
         [lambda r: "High" in r],
         "control_fan(speed=99 → clamped to 3)"),

        (m.control_thermostat, {"temperature":22,"mode":"cool"},
         [lambda r: "22" in r, lambda r: "cool" in r.lower()],
         "control_thermostat(22°C, cool)"),

        (m.control_thermostat, {"temperature":18,"mode":"heat"},
         [lambda r: "heat" in r.lower()],
         "control_thermostat(18°C, heat)"),

        (m.control_thermostat, {"temperature":20,"mode":"badmode"},
         [lambda r: "auto" in r.lower()],
         "control_thermostat(badmode → auto fallback)"),

        (m.play_music, {"mood":"jazz"},
         [lambda r: "jazz" in r.lower()],
         "play_music(jazz)"),

        (m.play_music, {"mood":"sleep"},
         [lambda r: "sleep" in r.lower()],
         "play_music(sleep)"),

        (m.play_music, {"mood":"unknown_vibe_xyz"},
         [lambda r: "playing" in r.lower()],
         "play_music(unknown mood → generic playlist)"),

        (m.control_tv, {"action":"on"},
         [lambda r: "on" in r.lower()],
         "control_tv(on)"),

        (m.control_tv, {"action":"off"},
         [lambda r: "off" in r.lower()],
         "control_tv(off)"),

        (m.control_tv, {"action":"mute"},
         [lambda r: "mute" in r.lower()],
         "control_tv(mute)"),

        (m.control_tv, {"action":"channel","channel":"BBC News"},
         [lambda r: "BBC" in r],
         "control_tv(channel, BBC News)"),

        (m.control_tv, {"action":"channel","channel":"10"},
         [lambda r: "10" in r],
         "control_tv(channel, 10)"),
    ]

    for fn, args, checks, label in cases:
        try:
            result = fn.invoke(args)
            if not isinstance(result, str):
                fail(label, f"returned {type(result).__name__}, want str")
            elif not all(c(result) for c in checks):
                fail(label, f"check failed — got: {result[:80]!r}")
            else:
                ok(label, result[:60])
        except Exception as e:
            fail(label, traceback.format_exc(limit=1).strip())


# ══════════════════════════════════════════════════════════════════════════════
# 3. parse_response EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════
def test_parse_response():
    hdr("3 · parse_response EDGE CASES")
    try:
        import main as m
    except Exception as e:
        fail("Cannot import main", str(e)); return

    cases = [
        # (raw_input, expected_emotion, expected_response_contains, label)
        ("[EMOTION:happy] Hello there!",         "happy",    "Hello there!",    "basic tag"),
        ("[EMOTION: happy] Space after colon",   "happy",    "Space after",     "space after colon"),
        ("[EMOTION:THINKING] Caps emotion",      "thinking", "Caps emotion",    "uppercase emotion"),
        ("[EMOTION:speaking][CONDITION:Rain] Wet","speaking", "Wet",             "both tags"),
        ("[CONDITION:Snow][EMOTION:idle] Cold",   "idle",     "Cold",            "condition first"),
        ("No tags at all",                        "speaking", "No tags",         "no tags → default speaking"),
        ("[EMOTION:sad]",                         "sad",      "",                "emotion only, empty response"),
        ("[EMOTION:unknowntag] Text",             "speaking", "Text",            "invalid emotion → speaking"),
        ("[EMOTION:happy] [EMOTION:sad] Double",  "happy",    "Double",          "double emotion → first wins"),
        ("   [EMOTION:excited]   Padded   ",      "excited",  "Padded",          "leading/trailing whitespace"),
        ("[EMOTION:happy]\n\nMultiline\nResponse","happy",    "Multiline",       "multiline response"),
    ]

    for raw, exp_emo, exp_in_resp, label in cases:
        try:
            r = m.parse_response(raw)
            if r["emotion"] != exp_emo:
                fail(f"parse: {label}", f"emotion={r['emotion']!r} want={exp_emo!r}")
            elif exp_in_resp and exp_in_resp not in r["response"]:
                fail(f"parse: {label}", f"response={r['response']!r} should contain {exp_in_resp!r}")
            elif "[EMOTION" in r["response"] or "[CONDITION" in r["response"]:
                fail(f"parse: {label}", f"tag leaked into response: {r['response'][:60]!r}")
            else:
                ok(f"parse: {label}", f"emo={r['emotion']} resp={r['response'][:40]!r}")
        except Exception as e:
            fail(f"parse: {label}", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 4. _sanitize_history
# ══════════════════════════════════════════════════════════════════════════════
def test_sanitize():
    hdr("4 · _sanitize_history EDGE CASES")
    try:
        import main as m
    except Exception as e:
        fail("Cannot import main", str(e)); return

    san = m._sanitize_history

    cases = [
        ([], [],
         "empty → empty"),

        ([{"role":"user","content":"hi"}],
         lambda r: len(r)==0,
         "single user (trailing) → stripped"),

        ([{"role":"user","content":"q"},{"role":"assistant","content":"a"}],
         lambda r: len(r)==2 and r[0]["role"]=="user",
         "valid pair → kept"),

        ([{"role":"assistant","content":"hi"},{"role":"user","content":"yo"},{"role":"assistant","content":"ok"}],
         lambda r: r[0]["role"]=="user",
         "leading assistant → stripped"),

        ([{"role":"user","content":"   "},{"role":"user","content":"real"}],
         lambda r: all(x["content"].strip() for x in r),
         "blank content → filtered"),

        ([{"role":"user","content":"a"},{"role":"user","content":"b"},{"role":"assistant","content":"c"}],
         lambda r: len([x for x in r if x["role"]=="user"]) == 1,
         "consecutive user msgs → keep latest"),

        ([{"role":"user" if i%2==0 else "assistant","content":f"m{i}"} for i in range(20)],
         lambda r: len(r) <= 8,
         "20 msgs → capped at 8"),

        ([{"role":"user","content":"q"},{"role":"assistant","content":"a"},{"role":"user","content":"trailing"}],
         lambda r: r[-1]["role"]=="assistant",
         "trailing user stripped"),
    ]

    for inp, expected, label in cases:
        try:
            result = san(inp)
            if callable(expected):
                passed_check = expected(result)
            else:
                passed_check = result == expected

            if passed_check:
                ok(f"sanitize: {label}", f"{len(result)} msgs")
            else:
                fail(f"sanitize: {label}", f"got {result}")
        except Exception as e:
            fail(f"sanitize: {label}", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 5. MISTRAL TOOL SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════
def test_tool_schemas():
    hdr("5 · MISTRAL TOOL SCHEMAS")
    try:
        import main as m
    except Exception as e:
        fail("Cannot import main", str(e)); return

    ok(f"MISTRAL_TOOLS count: {len(m.MISTRAL_TOOLS)}")

    expected_tools = [
        "get_weather","get_current_time","get_latest_news","set_timer","tell_joke",
        "control_lights","control_curtains","control_fan","control_thermostat",
        "play_music","control_tv",
    ]

    found_names = [s["function"]["name"] for s in m.MISTRAL_TOOLS]
    for name in expected_tools:
        if name in found_names:
            ok(f"Tool registered: {name}")
        else:
            fail(f"Tool MISSING: {name}")

    for schema in m.MISTRAL_TOOLS:
        name = schema["function"]["name"]
        fn   = schema["function"]
        issues = []
        if schema.get("type") != "function":   issues.append("type != function")
        if not fn.get("description"):          issues.append("missing description")
        if fn["parameters"].get("type") != "object": issues.append("params type != object")
        if "properties" not in fn["parameters"]: issues.append("missing properties")
        if issues: fail(f"Schema {name}", ", ".join(issues))
        else:       ok(f"Schema valid: {name}", f"{len(fn['parameters'].get('properties',{}))} params")

    try:
        json.dumps(m.MISTRAL_TOOLS)
        ok("All schemas JSON-serialisable")
    except Exception as e:
        fail("Schema JSON serialisation", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 6. LIVE API KEYS
# ══════════════════════════════════════════════════════════════════════════════
def test_live_apis():
    hdr("6 · LIVE API KEY VALIDATION")
    import requests as req

    # OpenWeatherMap
    key = os.getenv("OPENWEATHER_API_KEY","")
    if not key:
        warn("OpenWeather skipped — key not set")
    else:
        try:
            t0 = time.time()
            r = req.get(f"http://api.openweathermap.org/data/2.5/weather?q=London&appid={key}&units=metric", timeout=8)
            ms = int((time.time()-t0)*1000)
            if r.status_code == 200:
                d = r.json()
                ok(f"OpenWeather API", f"{d['main']['temp']}°C, {d['weather'][0]['description']} — {ms}ms")
            elif r.status_code == 401:
                fail("OpenWeather — 401 Unauthorized (bad key)")
            else:
                warn(f"OpenWeather — status {r.status_code}")
        except Exception as e:
            fail("OpenWeather", str(e))

    # Tavily
    key = os.getenv("TAVILY_API_KEY","")
    if not key:
        warn("Tavily skipped — key not set")
    else:
        try:
            from tavily import TavilyClient
            t0 = time.time()
            res = TavilyClient(api_key=key).search(query="test", max_results=1, search_depth="basic")
            ms = int((time.time()-t0)*1000)
            ok(f"Tavily API", f"{len(res.get('results',[]))} results — {ms}ms")
        except Exception as e:
            fail("Tavily", str(e))

    # Mistral
    key = os.getenv("MISTRAL_API_KEY","")
    if not key:
        warn("Mistral skipped — key not set")
    else:
        try:
            import httpx
            from mistralai import Mistral
            # Use a fresh httpx client to avoid NoneType/build_request issues on some SDK versions
            t0 = time.time()
            with httpx.Client() as _:
                client = Mistral(api_key=key)
                r = client.chat.complete(
                    model="mistral-small-2506",
                    messages=[{"role":"user","content":"Reply with just: OK"}],
                    max_tokens=5,
                )
            ms = int((time.time()-t0)*1000)
            ok(f"Mistral API", f"reply={r.choices[0].message.content!r} — {ms}ms")
        except ImportError:
            # httpx not available, try direct
            try:
                from mistralai import Mistral
                t0 = time.time()
                r = Mistral(api_key=key).chat.complete(
                    model="mistral-small-2506",
                    messages=[{"role":"user","content":"Reply: OK"}],
                    max_tokens=5,
                )
                ms = int((time.time()-t0)*1000)
                ok(f"Mistral API", f"reply={r.choices[0].message.content!r} — {ms}ms")
            except Exception as e:
                fail("Mistral", str(e))
        except Exception as e:
            fail("Mistral", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 7. TOOL-CALL ROUND-TRIP (the 400/3051 bug check)
# ══════════════════════════════════════════════════════════════════════════════
def test_tool_roundtrip():
    hdr("7 · MISTRAL TOOL-CALL ROUND-TRIP (core bug check)")
    key = os.getenv("MISTRAL_API_KEY","")
    if not key:
        warn("Skipped — key not set"); return

    try:
        import main as m
        from mistralai import Mistral
        client = Mistral(api_key=key)

        # Round 1: time tool (deterministic)
        msgs = [
            {"role":"system","content":"You are a helpful assistant."},
            {"role":"user",  "content":"What time is it right now?"},
        ]
        info("→ Sending tool-capable request…")
        t0 = time.time()
        resp = client.chat.complete(model=m.MISTRAL_MODEL, messages=msgs, tools=m.MISTRAL_TOOLS, tool_choice="auto")
        ms1  = int((time.time()-t0)*1000)

        msg = resp.choices[0].message
        if not msg.tool_calls:
            warn("No tool call returned — model answered directly", f"reply: {msg.content[:60]}")
            return

        ok(f"Round 1: {len(msg.tool_calls)} tool call(s)", f"{ms1}ms")

        null_ids = [tc for tc in msg.tool_calls if not tc.id]
        if null_ids:
            warn(f"{len(null_ids)} tool call(s) had null IDs — UUID fallback required")
        else:
            ok("All tool_call IDs non-null from Mistral")

        # Build assistant turn with UUID fallback
        safe_calls = []
        for tc in msg.tool_calls:
            import uuid
            tc_id = tc.id or f"call_{uuid.uuid4().hex[:12]}"
            safe_calls.append({"id":tc_id,"type":"function","function":{"name":tc.function.name,"arguments":tc.function.arguments}})

        msgs.append({"role":"assistant","content":msg.content or "","tool_calls":safe_calls})

        for tc_dict in safe_calls:
            try:
                args = json.loads(tc_dict["function"]["arguments"])
            except Exception:
                args = {}
            tool_fn = m._tool_map.get(tc_dict["function"]["name"])
            result  = tool_fn.invoke(args) if tool_fn else "unknown tool"
            ok(f"Tool executed: {tc_dict['function']['name']}", result[:60])
            msgs.append({"role":"tool","tool_call_id":tc_dict["id"],"content":str(result)})

        info("→ Sending tool results back…")
        t0 = time.time()
        resp2 = client.chat.complete(model=m.MISTRAL_MODEL, messages=msgs, tools=m.MISTRAL_TOOLS, tool_choice="auto")
        ms2   = int((time.time()-t0)*1000)
        ok("Round-trip complete — no 400 error!", f"{ms2}ms")
        ok(f"Final reply", resp2.choices[0].message.content[:80])

    except Exception as e:
        fail("Tool round-trip", str(e))
        if "400" in str(e) and "3051" in str(e):
            print(f"\n  {R}  ↳ THIS IS THE ORIGINAL 400/3051 BUG — tool_call_id still broken!{RST}")


# ══════════════════════════════════════════════════════════════════════════════
# 8. invoke_agent END-TO-END (no server needed)
# ══════════════════════════════════════════════════════════════════════════════
def test_invoke_agent():
    hdr("8 · invoke_agent END-TO-END")
    key = os.getenv("MISTRAL_API_KEY","")
    if not key:
        warn("Skipped — key not set"); return

    try:
        import main as m
    except Exception as e:
        fail("Cannot import main", str(e)); return

    cases = [
        # (label, user_input, history, checks)
        ("Plain chat",
         "Say exactly: Hello world",
         [],
         [lambda r: isinstance(r.get("response"),str) and len(r["response"])>0,
          lambda r: r.get("emotion") in m.EMOTION_VALID]),

        ("Time tool",
         "What time is it right now?",
         [],
         [lambda r: re.search(r"\d{1,2}:\d{2}", r.get("response","")),
          lambda r: r.get("emotion") in m.EMOTION_VALID]),

        ("Joke tool",
         "Tell me a joke.",
         [],
         [lambda r: len(r.get("response","")) > 10]),

        ("Light control",
         "Turn on the bedroom lights.",
         [],
         [lambda r: any(w in r.get("response","").lower() for w in ["light","bedroom","on"])]),

        ("Curtain control",
         "Close the living room curtains.",
         [],
         [lambda r: any(w in r.get("response","").lower() for w in ["curtain","clos"])]),

        ("Fan control",
         "Turn on the fan at speed 2.",
         [],
         [lambda r: any(w in r.get("response","").lower() for w in ["fan","speed","medium"])]),

        ("TV control",
         "Turn on the TV.",
         [],
         [lambda r: "tv" in r.get("response","").lower() or "television" in r.get("response","").lower()]),

        ("Music control",
         "Play some chill music.",
         [],
         [lambda r: any(w in r.get("response","").lower() for w in ["music","playing","chill"])]),

        ("Thermostat",
         "Set the thermostat to 24 degrees.",
         [],
         [lambda r: any(w in r.get("response","").lower() for w in ["24","thermostat","temperature"])]),

        ("History threading",
         "What did I just tell you?",
         [{"role":"user","content":"My name is Riya."},
          {"role":"assistant","content":"[EMOTION:happy] Nice to meet you, Riya!"}],
         [lambda r: "riya" in r.get("response","").lower() or "name" in r.get("response","").lower()]),

        ("Empty input recovery",
         " ",
         [],
         [lambda r: isinstance(r.get("response"),str)]),

        ("Emotion tag not in response",
         "Hello",
         [],
         [lambda r: "[EMOTION" not in r.get("response",""),
          lambda r: "[CONDITION" not in r.get("response","")]),
    ]

    for label, user_input, history, checks in cases:
        info(f"Testing: {label}…")
        try:
            t0 = time.time()
            result = asyncio.run(m.invoke_agent(user_input, history))
            ms = int((time.time()-t0)*1000)

            if not isinstance(result, dict):
                fail(label, f"returned {type(result)}, want dict"); continue

            for key2 in ("response","emotion","condition"):
                if key2 not in result:
                    fail(label, f"missing key '{key2}'"); break
            else:
                all_ok = True
                for i, chk in enumerate(checks):
                    if not chk(result):
                        fail(label, f"check #{i+1} failed — {result}")
                        all_ok = False; break
                if all_ok:
                    ok(label, f"emo={result['emotion']} {ms}ms: {result['response'][:50]!r}")
        except Exception as e:
            fail(label, traceback.format_exc(limit=2).strip())

# Patch: add EMOTION_VALID to main if missing
try:
    import main as _m
    if not hasattr(_m, 'EMOTION_VALID'):
        _m.EMOTION_VALID = {"idle","happy","thinking","speaking","surprised","sad","excited","sleeping"}
except Exception:
    pass


# ══════════════════════════════════════════════════════════════════════════════
# 9. REST ENDPOINTS (needs server)
# ══════════════════════════════════════════════════════════════════════════════
def test_rest_endpoints():
    hdr("9 · REST ENDPOINTS (server must be running on :8000)")
    import requests as req

    try:
        r = req.get(f"{BASE}/api/health", timeout=4)
        if r.status_code == 200:
            d = r.json()
            ok("/api/health", f"status={d.get('status')} version={d.get('version')}")
        else:
            fail("/api/health", f"status {r.status_code}"); return
    except Exception as e:
        warn("/api/health — server not reachable", str(e))
        info("Start server:  uvicorn main:app --reload --port 8000"); return

    # /api/time
    try:
        r = req.get(f"{BASE}/api/time", timeout=4)
        d = r.json()
        ok("/api/time", f"time={d.get('time')} is_night={d.get('is_night')}")
    except Exception as e:
        fail("/api/time", str(e))

    # /api/news
    try:
        r = req.get(f"{BASE}/api/news", timeout=4)
        d = r.json()
        ok(f"/api/news", f"{len(d.get('news',[]))} articles cached")
    except Exception as e:
        fail("/api/news", str(e))

    # /api/weather — valid city
    try:
        r = req.get(f"{BASE}/api/weather/London", timeout=8)
        d = r.json()
        if "temp" in d:
            ok(f"/api/weather/London", f"temp={d['temp']}°C condition={d.get('condition')}")
        else:
            warn("/api/weather/London", str(d))
    except Exception as e:
        fail("/api/weather/London", str(e))

    # /api/weather — invalid city → graceful error
    try:
        r = req.get(f"{BASE}/api/weather/FakeCityXYZ99", timeout=8)
        d = r.json()
        if "error" in d or r.status_code >= 400:
            ok("/api/weather/FakeCityXYZ — graceful error")
        else:
            warn("/api/weather/FakeCityXYZ — no error field", str(d))
    except Exception as e:
        fail("/api/weather/FakeCityXYZ", str(e))

    # /api/chat — no-tool response
    try:
        t0 = time.time()
        r = req.post(f"{BASE}/api/chat",
                     json={"message":"Say only: TEST_OK","history":[]},
                     timeout=30)
        ms = int((time.time()-t0)*1000)
        d  = r.json()
        if r.status_code == 200 and "response" in d and "emotion" in d:
            if "[EMOTION" in d["response"]:
                fail("/api/chat — emotion tag leaked into response", d["response"][:80])
            else:
                ok(f"/api/chat plain", f"{ms}ms emo={d['emotion']} resp={d['response'][:40]!r}")
        else:
            fail("/api/chat plain", f"status={r.status_code} body={r.text[:100]}")
    except Exception as e:
        fail("/api/chat plain", str(e))

    # /api/chat — tool call (time)
    try:
        t0 = time.time()
        r = req.post(f"{BASE}/api/chat",
                     json={"message":"What time is it right now?","history":[]},
                     timeout=35)
        ms = int((time.time()-t0)*1000)
        d  = r.json()
        if r.status_code == 200 and re.search(r"\d{1,2}:\d{2}", d.get("response","")):
            ok(f"/api/chat time tool", f"{ms}ms → {d['response'][:50]!r}")
        elif r.status_code == 200:
            warn(f"/api/chat time tool — no time in response", d.get("response","")[:60])
        else:
            fail(f"/api/chat time tool", f"status={r.status_code}")
    except Exception as e:
        fail("/api/chat time tool", str(e))

    # /api/chat — smart home tool
    try:
        t0 = time.time()
        r = req.post(f"{BASE}/api/chat",
                     json={"message":"Turn on the living room lights.","history":[]},
                     timeout=35)
        ms = int((time.time()-t0)*1000)
        d  = r.json()
        if r.status_code == 200:
            resp_lower = d.get("response","").lower()
            if any(w in resp_lower for w in ["light","living","on"]):
                ok(f"/api/chat lights tool", f"{ms}ms → {d['response'][:50]!r}")
            else:
                warn("/api/chat lights tool — unexpected response", d.get("response","")[:60])
        else:
            fail(f"/api/chat lights", f"status={r.status_code}")
    except Exception as e:
        fail("/api/chat lights", str(e))

    # CORS
    try:
        r = req.options(f"{BASE}/api/health", headers={"Origin":"http://localhost:5173"}, timeout=5)
        cors = r.headers.get("access-control-allow-origin","")
        ok("CORS headers", f"allow-origin={cors!r}") if cors else warn("CORS — no allow-origin")
    except Exception as e:
        warn("CORS check", str(e))

    # 404
    try:
        r = req.get(f"{BASE}/api/doesnotexist", timeout=5)
        ok("Unknown route → 404") if r.status_code==404 else warn(f"Unknown route → {r.status_code}")
    except Exception as e:
        warn("404 check", str(e))

    # Message body validation
    try:
        r = req.post(f"{BASE}/api/chat", json={}, timeout=5)
        ok("Empty body → 422") if r.status_code==422 else warn(f"Empty body → {r.status_code} (expected 422)")
    except Exception as e:
        warn("Validation check", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 10. MESSAGE CHOKE / TIMEOUT RESILIENCE
# ══════════════════════════════════════════════════════════════════════════════
def test_choke_resilience():
    hdr("10 · MESSAGE CHOKE & TIMEOUT RESILIENCE")
    key = os.getenv("MISTRAL_API_KEY","")
    if not key:
        warn("Skipped — key not set"); return

    try:
        import main as m
    except Exception as e:
        fail("Cannot import main", str(e)); return

    # 10a: Verify timeout wrappers exist in source
    src = open(os.path.join(os.path.dirname(__file__), "main.py"), encoding='utf-8').read()
    if "asyncio.wait_for" in src:
        ok("wait_for timeout wrappers present in main.py")
    else:
        fail("wait_for timeouts MISSING — messages can choke forever")

    if "timeout=18" in src:
        ok("18s LLM call timeout configured")
    else:
        warn("18s LLM timeout not found — check main.py")

    if "timeout=8" in src or "timeout=8.0" in src:
        ok("8s tool call timeout configured")
    else:
        warn("8s tool timeout not found")

    if "force_text" in src or "tool_choice.*none" in src or '"none"' in src:
        ok("force_text fallback prevents infinite tool loop")
    else:
        warn("force_text/tool_choice=none fallback not found")

    # 10b: Rapid sequential calls (no queue blocking)
    info("Testing 3 rapid sequential invoke_agent calls…")
    times = []
    for i in range(3):
        try:
            t0 = time.time()
            r = asyncio.run(m.invoke_agent(f"Say: RAPID_{i}", []))
            ms = int((time.time()-t0)*1000)
            times.append(ms)
            if isinstance(r, dict) and r.get("response"):
                ok(f"Rapid call #{i+1}", f"{ms}ms — {r['response'][:40]!r}")
            else:
                fail(f"Rapid call #{i+1}", str(r))
        except Exception as e:
            fail(f"Rapid call #{i+1}", str(e))

    if times and max(times) < 30000:
        ok(f"All rapid calls completed", f"max={max(times)}ms avg={sum(times)//len(times)}ms")
    elif times:
        warn(f"Slow rapid calls", f"max={max(times)}ms — may indicate latency issues")

    # 10c: History overflow (more than 8 messages)
    long_history = [
        {"role": "user" if i%2==0 else "assistant", "content": f"message {i}"}
        for i in range(16)
    ]
    try:
        r = asyncio.run(m.invoke_agent("Hello", long_history))
        ok("Long history (16 msgs) handled without crash",
           f"emo={r.get('emotion')} resp={r.get('response','')[:40]!r}")
    except Exception as e:
        fail("Long history overflow", str(e))

    # 10d: Concurrent calls (simulate two users)
    info("Testing concurrent invoke_agent calls…")
    async def _concurrent():
        tasks = [
            m.invoke_agent("What time is it?", []),
            m.invoke_agent("Tell me a joke.", []),
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    try:
        t0 = time.time()
        results = asyncio.run(_concurrent())
        ms = int((time.time()-t0)*1000)
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            fail("Concurrent calls", str(errors[0]))
        else:
            ok(f"2 concurrent calls completed", f"{ms}ms total, {len(results)} results")
    except Exception as e:
        fail("Concurrent calls", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 11. WEBSOCKET (needs server)
# ══════════════════════════════════════════════════════════════════════════════
def test_websocket():
    hdr("11 · WEBSOCKET TESTS (server must be running)")
    try:
        import websockets
    except ImportError:
        warn("websockets not installed", "pip install websockets"); return

    async def _ws():
        url = "ws://localhost:8000/ws/agent"
        try:
            async with websockets.connect(url, open_timeout=5) as ws:
                ok("WebSocket connected")

                # Ping/pong
                await ws.send(json.dumps({"type":"ping"}))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                d   = json.loads(raw)
                if d.get("type") == "pong":
                    ok("ping → pong")
                elif d.get("type") == "news_update":
                    ok("news_update on connect (expected)")
                    raw = await asyncio.wait_for(ws.recv(), timeout=5)
                    d   = json.loads(raw)
                    ok("ping → pong (after news)") if d.get("type")=="pong" else fail("pong missing", str(d))
                else:
                    fail("ping → pong", f"got {d}")

                # clear_history
                await ws.send(json.dumps({"type":"clear_history"}))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                d   = json.loads(raw)
                ok("clear_history → history_cleared") if d.get("type")=="history_cleared" else fail("history_cleared", str(d))

                # Chat round-trip
                await ws.send(json.dumps({"type":"chat","message":"What time is it?"}))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                d   = json.loads(raw)
                ok("chat → emotion:thinking") if d.get("type")=="emotion" and d.get("emotion")=="thinking" else warn("Expected thinking first", str(d))

                raw = await asyncio.wait_for(ws.recv(), timeout=40)
                d   = json.loads(raw)
                if d.get("type") == "response":
                    if "[EMOTION" in d.get("message",""):
                        fail("WS response — emotion tag leaked", d["message"][:60])
                    else:
                        ok("chat → response", f"emo={d.get('emotion')} msg={d.get('message','')[:50]!r}")
                else:
                    fail("chat response", f"got {d}")

                # Smart home tool via WS
                await ws.send(json.dumps({"type":"chat","message":"Turn on the lights."}))
                # drain thinking
                for _ in range(2):
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=40)
                        d   = json.loads(raw)
                        if d.get("type") == "response":
                            ok("WS smart home response", d.get("message","")[:50])
                            break
                    except asyncio.TimeoutError:
                        warn("WS smart home — timed out"); break

        except (ConnectionRefusedError, OSError):
            warn("WS not reachable — start server first")
        except asyncio.TimeoutError:
            fail("WS — response timed out")
        except Exception as e:
            fail("WS unexpected error", str(e))

    asyncio.run(_ws())


# ══════════════════════════════════════════════════════════════════════════════
# 12. FINE-TUNE SUGGESTIONS
# ══════════════════════════════════════════════════════════════════════════════
def test_suggestions():
    hdr("12 · FINE-TUNE & ACCESSIBILITY SUGGESTIONS")

    src = ""
    try:
        src = open(os.path.join(os.path.dirname(__file__), "main.py"), encoding='utf-8').read()
    except Exception as _e:
        warn("Cannot read main.py for analysis", str(_e))

    checks = [
        # (pattern_that_should_exist, suggestion_if_missing)
        ("asyncio.wait_for",
         "Add timeout wrappers to prevent indefinite hangs on slow API calls"),
        ('"none"',
         "Add tool_choice='none' on final fallback to break infinite tool loops"),
        ("re.IGNORECASE",
         "parse_response regex should use IGNORECASE so [EMOTION: HAPPY] works"),
        ("_sanitize_history",
         "History sanitiser prevents Mistral 400 from malformed alternation"),
        ("uuid.uuid4",
         "UUID fallback prevents 400/3051 when Mistral returns null tool_call_id"),
        ("asyncio.TimeoutError",
         "Catch TimeoutError separately to return a user-friendly message"),
    ]

    for pattern, suggestion in checks:
        if src and pattern in src:
            ok(f"✔ {suggestion[:60]}")
        else:
            warn(f"Missing: {suggestion}")

    print(f"\n  {C}── GENERAL FINE-TUNE RECOMMENDATIONS ───────────────────{RST}")
    recs = [
        ("TOOL STABILITY",   "Add retry(max=2) on Tavily/OpenWeather calls — they occasionally 5xx"),
        ("TOOL STABILITY",   "Cache weather results for 10min to reduce API calls on repeat queries"),
        ("TOOL STABILITY",   "Validate tool args before invoke() — Mistral can send null/wrong types"),
        ("MESSAGE CHOKE",    "Set max_tokens=800 on Mistral to prevent runaway long responses"),
        ("MESSAGE CHOKE",    "Keep history to 6 pairs max — longer context increases latency significantly"),
        ("EMOTION PARSING",  "Strip ALL bracket tags in parse_response, not just EMOTION/CONDITION"),
        ("EMOTION PARSING",  "Add [SPEAKING] as alias for 'speaking' — Mistral sometimes uses it"),
        ("ACCESSIBILITY",    "Add aria-label to all icon-only buttons (mic, send, clear)"),
        ("ACCESSIBILITY",    "Smart home panel needs keyboard navigation (Tab + Enter)"),
        ("ACCESSIBILITY",    "Brightness slider needs aria-label='Lamp brightness 80%'"),
        ("ACCESSIBILITY",    "Contrast check: #2a4050 text on dark bg may fail WCAG AA"),
        ("ACCESSIBILITY",    "News ticker should pause on hover (prefers-reduced-motion)"),
        ("PERFORMANCE",      "Dispose Three.js geometries/materials on unmount to prevent VRAM leak"),
        ("PERFORMANCE",      "Throttle mouse-orbit to 60fps — currently runs at render frame rate"),
        ("PERFORMANCE",      "Music note particles: use InstancedMesh instead of 12 separate meshes"),
        ("UX",               "Add 'ARIA is typing…' to browser tab title while loading=true"),
        ("UX",               "Voice: set recog.lang based on detected browser locale, not hardcoded en-US"),
        ("UX",               "Debounce on thermostat currently uses stale state for decrements"),
        ("SECURITY",         "Set CORS allowed_origins to ['http://localhost:5173'] not '*' in production"),
        ("SECURITY",         "Rate-limit /api/chat to 20 req/min per IP to prevent abuse"),
    ]

    for category, rec in recs:
        print(f"  {DIM}[{category:16}]{RST} {rec}")


# ══════════════════════════════════════════════════════════════════════════════
# REPORT
# ══════════════════════════════════════════════════════════════════════════════
def report():
    bar = "═" * 70
    print(f"\n{B}{bar}{RST}")
    print(f"{W}  ARIA BACKEND TEST REPORT{RST}")
    print(f"{B}{bar}{RST}")
    print(f"  {G}Passed : {passed:>4}{RST}")
    print(f"  {R}Failed : {failed:>4}{RST}")
    print(f"  {Y}Warned : {warned:>4}{RST}")
    print(f"  {DIM}Total  : {passed+failed+warned:>4}{RST}")
    print(f"{B}{bar}{RST}")
    if failed == 0:
        print(f"\n  {G}🎉 All tests passed!{RST}\n")
    else:
        print(f"\n  {R}🔥 {failed} failure(s) — fix before deploying.{RST}\n")
    return failed


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--fast",   action="store_true", help="Skip live LLM/API tests")
    p.add_argument("--ws",     action="store_true", help="Include WebSocket tests")
    p.add_argument("--only",   type=int,            help="Run only section N")
    args = p.parse_args()

    live_sections = {6, 7, 8, 9, 10}
    ws_sections   = {11}

    all_tests = [
        (1,  test_env),
        (2,  test_tools_offline),
        (3,  test_parse_response),
        (4,  test_sanitize),
        (5,  test_tool_schemas),
        (6,  test_live_apis),
        (7,  test_tool_roundtrip),
        (8,  test_invoke_agent),
        (9,  test_rest_endpoints),
        (10, test_choke_resilience),
        (11, test_websocket),
        (12, test_suggestions),
    ]

    print(f"\n{C}  {'='*60}{RST}")
    print(f"{C}  ARIA Backend Test Suite{RST}")
    print(f"{C}  {'='*60}{RST}\n")

    for num, fn in all_tests:
        if args.only and args.only != num: continue
        if args.fast and num in live_sections:
            hdr(f"{num} · [SKIPPED — --fast]"); continue
        if num in ws_sections and not args.ws:
            hdr(f"{num} · WebSocket [SKIPPED — pass --ws]"); continue
        try:
            fn()
        except Exception as e:
            fail(f"Section {num} crashed", traceback.format_exc(limit=3))

    sys.exit(report())
