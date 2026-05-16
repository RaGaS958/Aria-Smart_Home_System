"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              ARIA — DEEP DIAGNOSTIC SUITE  (debug_aria.py)                 ║
║  Runs OFFLINE + LIVE checks across every layer of the backend.             ║
║  Usage:  python debug_aria.py                                              ║
║  Flags:  --no-live   skip real API calls (env/schema checks only)          ║
║          --ws        include WebSocket live test (needs server running)    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys, os, re, json, uuid, time, asyncio, importlib, traceback, argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Colour helpers ────────────────────────────────────────────────────────────
G  = "\033[92m"   # green
R  = "\033[91m"   # red
Y  = "\033[93m"   # yellow
B  = "\033[94m"   # blue
C  = "\033[96m"   # cyan
W  = "\033[97m"   # white bold
DIM= "\033[2m"
RST= "\033[0m"

OK   = f"{G}✅ PASS{RST}"
FAIL = f"{R}❌ FAIL{RST}"
WARN = f"{Y}⚠️  WARN{RST}"
INFO = f"{C}ℹ️  INFO{RST}"

passed = failed = warned = 0

def hdr(title: str):
    bar = "─" * 70
    print(f"\n{B}{bar}{RST}")
    print(f"{W}  {title}{RST}")
    print(f"{B}{bar}{RST}")

def ok(msg, detail=""):
    global passed; passed += 1
    suffix = f"  {DIM}{detail}{RST}" if detail else ""
    print(f"  {OK}  {msg}{suffix}")

def fail(msg, detail=""):
    global failed; failed += 1
    suffix = f"\n       {R}{detail}{RST}" if detail else ""
    print(f"  {FAIL}  {msg}{suffix}")

def warn(msg, detail=""):
    global warned; warned += 1
    suffix = f"  {DIM}{detail}{RST}" if detail else ""
    print(f"  {WARN}  {msg}{suffix}")

def info(msg):
    print(f"  {INFO}  {DIM}{msg}{RST}")

def section_score():
    print()


# ══════════════════════════════════════════════════════════════════════════════
# 1. ENVIRONMENT VARIABLES
# ══════════════════════════════════════════════════════════════════════════════
def test_env():
    hdr("1 · ENVIRONMENT VARIABLES")
    required = {
        "MISTRAL_API_KEY":     (None,    32),   # Mistral keys have no fixed prefix
        "OPENWEATHER_API_KEY": (None,    30),
        "TAVILY_API_KEY":      ("tvly-", 20),
    }
    optional = ["VITE_DEFAULT_CITY"]

    for key, (prefix, min_len) in required.items():
        val = os.getenv(key, "")
        if not val:
            fail(f"{key} — NOT SET")
        elif len(val) < min_len:
            warn(f"{key} — suspiciously short ({len(val)} chars)", "may be invalid")
        elif prefix and not val.startswith(prefix):
            warn(f"{key} — unexpected prefix", f"got '{val[:8]}…' expected '{prefix}…'")
        else:
            ok(f"{key}", f"{val[:8]}…")

    for key in optional:
        val = os.getenv(key, "")
        info(f"{key} = {val or '(not set)'}")

    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# 2. PACKAGE IMPORTS
# ══════════════════════════════════════════════════════════════════════════════
def test_imports():
    hdr("2 · PACKAGE IMPORTS")
    packages = [
        ("fastapi",            "FastAPI"),
        ("uvicorn",            None),      # uvicorn has no importable attr, just check module
        ("mistralai",          "Mistral"),   # v1.0+  (old SDK: MistralClient)
        ("langchain.tools",    "tool"),
        ("langchain_core.messages", "HumanMessage"),
        ("tavily",             "TavilyClient"),
        ("dotenv",             "load_dotenv"),
        ("pydantic",           "BaseModel"),
        ("requests",           None),
        ("websockets",         None),   # needed for WS test
    ]
    missing = []
    for mod, attr in packages:
        try:
            m = importlib.import_module(mod)
            if attr:
                try:
                    getattr(m, attr)
                    ok(f"import {mod}", attr)
                except AttributeError:
                    # Special case: old mistralai (<v1.0) has MistralClient not Mistral
                    if mod == "mistralai" and attr == "Mistral":
                        try:
                            getattr(m, "MistralClient")
                            fail(f"import mistralai — OLD SDK installed",
                                 "Has MistralClient but needs Mistral.  Run: pip install --upgrade mistralai")
                        except AttributeError:
                            fail(f"import {mod} — neither Mistral nor MistralClient found",
                                 "Run: pip install --upgrade mistralai")
                    elif mod == "uvicorn":
                        ok(f"import uvicorn", "module present")  # no top-level attr to check
                    else:
                        warn(f"import {mod} — attr '{attr}' missing")
            else:
                ok(f"import {mod}")
        except ImportError as e:
            fail(f"import {mod}", str(e))
            missing.append(mod)

    if missing:
        print(f"\n  {Y}  Run:  pip install {' '.join(missing)}{RST}")

    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# 3. MAIN.PY — STATIC ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
def test_static():
    hdr("3 · MAIN.PY — STATIC ANALYSIS")
    path = os.path.join(os.path.dirname(__file__), "main.py")

    if not os.path.exists(path):
        fail("main.py not found", path)
        return

    with open(path, encoding="utf-8") as f:
        src = f.read()

    # Syntax check
    import ast
    try:
        ast.parse(src)
        ok("Python syntax valid")
    except SyntaxError as e:
        fail("Syntax error", str(e)); return

    # Banned patterns
    banned = [
        ("AgentExecutor",          "old LangChain agent — causes tool_call_id bug"),
        ("create_tool_calling_agent", "old pattern — causes tool_call_id bug"),
        ("agent_executor.invoke",  "patching fails against Pydantic v1"),
        ("ChatMistralAI",          "LangChain wrapper — serializer drops tool IDs"),
    ]
    for pat, reason in banned:
        hits = [i+1 for i, l in enumerate(src.splitlines()) if pat in l and not l.strip().startswith("#")]
        if hits:
            fail(f"Found '{pat}' on line(s) {hits}", reason)
        else:
            ok(f"No banned pattern: '{pat}'")

    # Required patterns
    required = [
        ("mistral_client.chat.complete",  "native SDK call"),
        ("tool_call_id",                  "tool result ID threading"),
        ("uuid.uuid4()",                  "UUID fallback for null IDs"),
        ("_sanitize_history",             "history sanitizer"),
        ("parse_response",                "emotion/condition parser"),
        ("MISTRAL_TOOLS",                 "raw tool schema list"),
        ("/api/health",                   "health endpoint"),
        ("/api/chat",                     "chat endpoint"),
        ("/api/weather",                  "weather endpoint"),
        ("/ws/agent",                     "WebSocket endpoint"),
        ("news_scheduler",                "background news task"),
    ]
    for pat, label in required:
        if pat in src:
            ok(f"Found: {label}", f"'{pat}'")
        else:
            fail(f"Missing: {label}", f"'{pat}' not found in main.py")

    # EMOTION tag check in SYSTEM_PROMPT
    if "[EMOTION:" in src:
        ok("SYSTEM_PROMPT contains [EMOTION:X] instruction")
    else:
        warn("SYSTEM_PROMPT missing [EMOTION:X] instruction")

    # Check tool list completeness
    expected_tools = [
        "get_weather", "get_current_time", "get_latest_news", "set_timer",
        "tell_joke", "control_lights", "control_curtains", "control_fan",
        "control_thermostat", "play_music", "control_tv",
    ]
    for t in expected_tools:
        if t in src:
            ok(f"Tool defined: {t}")
        else:
            fail(f"Tool missing: {t}")

    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# 4. TOOL SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════
def test_tool_schemas():
    hdr("4 · MISTRAL TOOL SCHEMAS")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        import main as m
    except Exception as e:
        fail("Could not import main.py", str(e))
        return

    schemas = m.MISTRAL_TOOLS
    ok(f"MISTRAL_TOOLS has {len(schemas)} tools")

    for schema in schemas:
        name = schema.get("function", {}).get("name", "?")
        fn   = schema.get("function", {})
        issues = []

        if schema.get("type") != "function":
            issues.append("type != 'function'")
        if not fn.get("name"):
            issues.append("missing name")
        if not fn.get("description"):
            issues.append("missing description")
        params = fn.get("parameters", {})
        if params.get("type") != "object":
            issues.append("parameters.type != 'object'")
        if "properties" not in params:
            issues.append("missing parameters.properties")

        if issues:
            fail(f"Schema [{name}]", ", ".join(issues))
        else:
            ok(f"Schema [{name}]", f"{len(params.get('properties', {}))} params")

    # Serialisability check — must be JSON-safe (what Mistral receives)
    try:
        json.dumps(schemas)
        ok("All schemas are JSON-serialisable")
    except Exception as e:
        fail("Schema JSON serialisation failed", str(e))

    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# 5. HELPER FUNCTIONS (offline)
# ══════════════════════════════════════════════════════════════════════════════
def test_helpers():
    hdr("5 · HELPER FUNCTIONS (offline)")
    try:
        import main as m
    except Exception as e:
        fail("Cannot import main", str(e)); return

    # ── parse_response ──────────────────────────────────────────────────────
    cases = [
        ("[EMOTION:happy] Hello!",                  "happy",    None,    "Hello!"),
        ("[EMOTION:thinking] [CONDITION:Rain] Wet.", "thinking", "Rain",  "Wet."),
        ("No tags here.",                            "speaking", None,    "No tags here."),
        ("[EMOTION:sad]",                            "sad",      None,    ""),
        ("[EMOTION:EXCITED] Caps test",              "excited",  None,    "Caps test"),
        ("[CONDITION:Snow] [EMOTION:idle] Brr.",     "idle",     "Snow",  "Brr."),
    ]
    for raw, exp_emo, exp_cond, exp_resp in cases:
        r = m.parse_response(raw)
        if r["emotion"] != exp_emo:
            fail(f"parse_response emotion", f"input={raw!r}  got={r['emotion']!r}  want={exp_emo!r}")
        elif r["condition"] != exp_cond:
            fail(f"parse_response condition", f"input={raw!r}  got={r['condition']!r}  want={exp_cond!r}")
        elif r["response"].strip() != exp_resp.strip():
            fail(f"parse_response response", f"input={raw!r}  got={r['response']!r}  want={exp_resp!r}")
        else:
            ok(f"parse_response: {raw[:40]!r}")

    # ── _sanitize_history ───────────────────────────────────────────────────
    san = m._sanitize_history

    # Empty
    r = san([])
    if r == []:
        ok("sanitize: empty history → []")
    else:
        fail("sanitize: empty history", f"got {r}")

    # Starts with assistant → leading assistant msg dropped, valid pair kept
    r = san([
        {"role": "assistant", "content": "hi"},   # ← should be stripped (no leading user)
        {"role": "user",      "content": "yo"},
        {"role": "assistant", "content": "sure"},  # ← pair now valid, ends with assistant
    ])
    if r and r[0]["role"] == "user" and r[-1]["role"] == "assistant":
        ok("sanitize: leading assistant msg stripped")
    else:
        fail("sanitize: leading assistant msg not stripped", str(r))

    # Consecutive same roles → merge to latest
    r = san([
        {"role": "user",      "content": "first"},
        {"role": "user",      "content": "second"},
        {"role": "assistant", "content": "reply"},
    ])
    user_msgs = [x for x in r if x["role"] == "user"]
    if len(user_msgs) == 1 and user_msgs[0]["content"] == "second":
        ok("sanitize: consecutive user msgs → keep latest")
    else:
        fail("sanitize: consecutive user msgs", str(r))

    # Trailing user stripped (current turn handled separately)
    r = san([
        {"role": "user",      "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user",      "content": "q2"},
    ])
    if r and r[-1]["role"] == "assistant":
        ok("sanitize: trailing user msg stripped")
    else:
        fail("sanitize: trailing user msg NOT stripped", str(r))

    # Cap at 8 messages
    long = [{"role": "user" if i%2==0 else "assistant", "content": f"msg{i}"} for i in range(20)]
    r = san(long)
    if len(r) <= 8:
        ok(f"sanitize: capped at 8 msgs (got {len(r)})")
    else:
        fail(f"sanitize: cap failed — got {len(r)} msgs")

    # Empty content filtered
    r = san([{"role": "user", "content": "   "}, {"role": "user", "content": "real"}])
    contents = [x["content"] for x in r]
    if "   " not in contents:
        ok("sanitize: blank-content msgs filtered")
    else:
        fail("sanitize: blank-content msg survived", str(r))

    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# 6. TOOLS (offline — no real API)
# ══════════════════════════════════════════════════════════════════════════════
def test_tools_offline():
    hdr("6 · TOOL EXECUTION (offline / no API)")
    try:
        import main as m
    except Exception as e:
        fail("Cannot import main", str(e)); return

    # Tools that need no external API
    offline_cases = [
        (m.get_current_time, {},                           lambda r: re.search(r"\d{1,2}:\d{2}", r)),
        (m.set_timer,        {"label":"pasta","minutes":5},lambda r: "5" in r and "pasta" in r.lower()),
        (m.tell_joke,        {},                           lambda r: len(r) > 10),
        (m.control_lights,   {"room":"kitchen","action":"on","brightness":80},
                                                           lambda r: "kitchen" in r.lower()),
        (m.control_curtains, {"room":"bedroom","action":"open"},  lambda r: "bedroom" in r.lower()),
        (m.control_curtains, {"room":"bedroom","action":"close"}, lambda r: "bedroom" in r.lower()),
        (m.control_curtains, {"room":"hall","action":"invalid"},  lambda r: "use" in r.lower()),
        (m.control_fan,      {"room":"hall","action":"on","speed":3},   lambda r: "High" in r),
        (m.control_fan,      {"room":"hall","action":"off","speed":1},  lambda r: "off" in r.lower()),
        (m.control_thermostat,{"temperature":22,"mode":"cool"},  lambda r: "22" in r),
        (m.control_thermostat,{"temperature":18,"mode":"badmode"},lambda r: "auto" in r.lower()),
        (m.play_music,       {"mood":"jazz"},              lambda r: "jazz" in r.lower()),
        (m.play_music,       {"mood":"unknown_vibe"},      lambda r: "unknown_vibe" in r.lower() or "mix" in r.lower()),
        (m.control_tv,       {"action":"on"},              lambda r: "on" in r.lower()),
        (m.control_tv,       {"action":"channel","channel":"BBC"}, lambda r: "BBC" in r),
        (m.control_tv,       {"action":"mute"},            lambda r: "mute" in r.lower()),
    ]

    for fn, args, check in offline_cases:
        label = f"{fn.name}({', '.join(f'{k}={v!r}' for k,v in args.items())})"
        try:
            result = fn.invoke(args)
            if not isinstance(result, str):
                fail(label, f"returned {type(result).__name__}, expected str")
            elif not check(result):
                fail(label, f"unexpected result: {result!r}")
            else:
                ok(label, result[:60])
        except Exception as e:
            fail(label, traceback.format_exc(limit=1).strip())

    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# 7. LIVE API KEYS
# ══════════════════════════════════════════════════════════════════════════════
def test_live_apis():
    hdr("7 · LIVE API KEY VALIDATION")

    # ── OpenWeatherMap ────────────────────────────────────────────────────────
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        warn("OpenWeather — skipped (key not set)")
    else:
        try:
            import requests as req
            t0 = time.time()
            r = req.get(
                f"http://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}&units=metric",
                timeout=8
            )
            ms = int((time.time()-t0)*1000)
            if r.status_code == 200:
                d = r.json()
                ok(f"OpenWeather — London: {d['main']['temp']}°C, {d['weather'][0]['description']}", f"{ms}ms")
            elif r.status_code == 401:
                fail("OpenWeather — 401 Unauthorized (bad API key)")
            else:
                warn(f"OpenWeather — status {r.status_code}", r.text[:80])
        except Exception as e:
            fail("OpenWeather — request failed", str(e))

    # ── Tavily ────────────────────────────────────────────────────────────────
    tvly_key = os.getenv("TAVILY_API_KEY", "")
    if not tvly_key:
        warn("Tavily — skipped (key not set)")
    else:
        try:
            from tavily import TavilyClient
            t0 = time.time()
            client = TavilyClient(api_key=tvly_key)
            res = client.search(query="test", max_results=1, search_depth="basic")
            ms = int((time.time()-t0)*1000)
            results = res.get("results", [])
            if results:
                ok(f"Tavily — got {len(results)} result(s)", f"{ms}ms")
            else:
                warn("Tavily — no results returned")
        except Exception as e:
            fail("Tavily — request failed", str(e))

    # ── Mistral ───────────────────────────────────────────────────────────────
    mk = os.getenv("MISTRAL_API_KEY", "")
    if not mk:
        warn("Mistral — skipped (key not set)")
    else:
        try:
            try:
                from mistralai import Mistral
            except ImportError:
                fail("mistralai import failed — run: pip install --upgrade mistralai")
                section_score(); return
            # Detect old SDK
            import mistralai as _mai
            if not hasattr(_mai, "Mistral"):
                fail("mistralai OLD SDK — has MistralClient, needs Mistral",
                     "Fix: pip install --upgrade mistralai")
                section_score(); return
            client = Mistral(api_key=mk)
            t0 = time.time()
            r = client.chat.complete(
                model="mistral-small-2506",
                messages=[{"role":"user","content":"Reply with just: OK"}],
                max_tokens=5,
            )
            ms = int((time.time()-t0)*1000)
            reply = r.choices[0].message.content.strip()
            ok(f"Mistral basic chat — reply: {reply!r}", f"{ms}ms")
        except Exception as e:
            fail("Mistral basic chat", str(e))

    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# 8. MISTRAL TOOL-CALL ROUND-TRIP (the original bug)
# ══════════════════════════════════════════════════════════════════════════════
def test_tool_call_roundtrip():
    hdr("8 · MISTRAL TOOL-CALL ROUND-TRIP (core bug check)")
    mk = os.getenv("MISTRAL_API_KEY", "")
    if not mk:
        warn("Skipped — MISTRAL_API_KEY not set"); section_score(); return

    try:
        from mistralai import Mistral
        import main as m
        client = Mistral(api_key=mk)

        # Force a tool call: ask for time (deterministic, no external API)
        messages = [
            {"role": "system",  "content": "You are a helpful assistant."},
            {"role": "user",    "content": "What time is it right now?"},
        ]

        print(f"  {DIM}  → Sending tool-capable request to Mistral…{RST}")
        t0 = time.time()
        resp = client.chat.complete(
            model="mistral-small-2506",
            messages=messages,
            tools=m.MISTRAL_TOOLS,
            tool_choice="auto",
        )
        ms = int((time.time()-t0)*1000)
        choice = resp.choices[0]
        msg    = choice.message

        if not msg.tool_calls:
            warn("Mistral didn't use a tool — check system prompt", f"reply: {msg.content[:60]}")
            section_score(); return

        ok(f"Mistral returned {len(msg.tool_calls)} tool call(s)", f"{ms}ms")

        # Check every tool call has an id
        null_id_count = 0
        for tc in msg.tool_calls:
            if not tc.id:
                null_id_count += 1
                warn(f"Tool call id is None/empty for '{tc.function.name}' — UUID fallback will fire")
            else:
                ok(f"Tool call id present: {tc.id}", tc.function.name)

        # Build assistant turn with guaranteed IDs (mirrors invoke_agent logic)
        safe_calls = []
        for tc in msg.tool_calls:
            tc_id = tc.id or f"call_{uuid.uuid4().hex[:12]}"
            safe_calls.append({
                "id":   tc_id,
                "type": "function",
                "function": {
                    "name":      tc.function.name,
                    "arguments": tc.function.arguments,
                },
            })

        messages.append({
            "role":       "assistant",
            "content":    msg.content or "",
            "tool_calls": safe_calls,
        })

        # Execute tool(s) and append results
        for tc_dict in safe_calls:
            tool_name = tc_dict["function"]["name"]
            try:
                args = json.loads(tc_dict["function"]["arguments"])
            except Exception:
                args = {}

            tool_fn = m._tool_map.get(tool_name)
            result  = tool_fn.invoke(args) if tool_fn else f"Unknown: {tool_name}"
            ok(f"Tool executed: {tool_name}", result[:60])

            messages.append({
                "role":         "tool",
                "tool_call_id": tc_dict["id"],
                "content":      str(result),
            })

        # Send back — this is where 400 used to fire
        print(f"  {DIM}  → Sending tool results back to Mistral…{RST}")
        t0 = time.time()
        resp2 = client.chat.complete(
            model="mistral-small-2506",
            messages=messages,
            tools=m.MISTRAL_TOOLS,
            tool_choice="auto",
        )
        ms2 = int((time.time()-t0)*1000)
        final_text = resp2.choices[0].message.content or ""
        ok(f"Round-trip complete — no 400 error", f"{ms2}ms")
        ok(f"Final reply: {final_text[:80]!r}")

        if null_id_count:
            warn(f"{null_id_count} tool call(s) had null IDs from Mistral — UUID fallback is essential")
        else:
            ok("All tool call IDs were non-null (UUID fallback not needed this run)")

    except Exception as e:
        fail("Tool-call round-trip failed", str(e))
        if "400" in str(e) and "3051" in str(e):
            print(f"  {R}  ↳ This is THE original bug — tool_call_id still broken!{RST}")
        traceback.print_exc()

    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# 9. INVOKE_AGENT END-TO-END
# ══════════════════════════════════════════════════════════════════════════════
def test_invoke_agent():
    hdr("9 · INVOKE_AGENT END-TO-END")
    mk = os.getenv("MISTRAL_API_KEY", "")
    if not mk:
        warn("Skipped — MISTRAL_API_KEY not set"); section_score(); return

    try:
        import main as m
    except Exception as e:
        fail("Cannot import main", str(e)); return

    test_cases = [
        # (description, user_input, history, checks)
        ("plain chat",
         "Say hello in exactly 3 words.",
         [],
         [lambda r: r.get("emotion") in {"happy","speaking","idle","excited"},
          lambda r: isinstance(r.get("response"), str) and len(r["response"]) > 0]),

        ("time tool call",
         "What time is it right now?",
         [],
         [lambda r: r.get("emotion") in {"speaking","thinking","happy","idle"},
          lambda r: re.search(r"\d{1,2}:\d{2}", r.get("response","")) is not None]),

        ("joke tool",
         "Tell me a joke.",
         [],
         [lambda r: isinstance(r.get("response"), str) and len(r["response"]) > 5]),

        ("smart home — lights",
         "Turn on the living room lights.",
         [],
         [lambda r: r.get("emotion") in {"happy","speaking","idle","excited"},
          lambda r: "living" in r.get("response","").lower() or "light" in r.get("response","").lower()]),

        ("history threading",
         "What did I just ask you?",
         [{"role":"user","content":"My favourite colour is purple."},
          {"role":"assistant","content":"[EMOTION:happy] Great choice! Purple is lovely."}],
         [lambda r: isinstance(r.get("response"), str)]),

        ("error recovery — empty input",
         " ",
         [],
         [lambda r: isinstance(r.get("response"), str)]),
    ]

    for desc, user_input, history, checks in test_cases:
        print(f"\n  {DIM}  Testing: {desc}…{RST}")
        try:
            t0 = time.time()
            result = asyncio.run(m.invoke_agent(user_input, history))
            ms = int((time.time()-t0)*1000)

            if not isinstance(result, dict):
                fail(desc, f"returned {type(result)} not dict")
                continue

            # Required keys
            for key in ("response","emotion","condition"):
                if key not in result:
                    fail(desc, f"missing key '{key}' in result"); break
            else:
                all_ok = True
                for i, chk in enumerate(checks):
                    if not chk(result):
                        fail(desc, f"check #{i+1} failed — result={result}")
                        all_ok = False
                        break
                if all_ok:
                    ok(desc, f"emotion={result['emotion']!r}  {ms}ms  reply={result['response'][:50]!r}")

        except Exception as e:
            fail(desc, traceback.format_exc(limit=2).strip())

    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# 10. REST ENDPOINTS (needs server running at localhost:8000)
# ══════════════════════════════════════════════════════════════════════════════
def test_rest_endpoints():
    hdr("10 · REST ENDPOINTS  (server must be running on :8000)")
    import requests as req

    BASE = "http://localhost:8000"

    def get(path, timeout=10):
        return req.get(BASE + path, timeout=timeout)

    def post(path, body, timeout=30):
        return req.post(BASE + path, json=body, timeout=timeout)

    # Health
    try:
        r = get("/api/health")
        if r.status_code == 200:
            d = r.json()
            ok("/api/health", f"status={d.get('status')} version={d.get('version')}")
        else:
            fail("/api/health", f"status {r.status_code}")
    except Exception as e:
        warn("/api/health — server not reachable", str(e))
        info("Start the server:  uvicorn main:app --reload --port 8000")
        section_score(); return   # no point running endpoint tests without server

    # Time
    try:
        r = get("/api/time")
        if r.status_code == 200:
            d = r.json()
            ok("/api/time", f"time={d.get('time')} is_night={d.get('is_night')}")
        else:
            fail("/api/time", f"status {r.status_code}")
    except Exception as e:
        fail("/api/time", str(e))

    # News (may be empty on first boot)
    try:
        r = get("/api/news")
        if r.status_code == 200:
            d = r.json()
            ok(f"/api/news — {len(d.get('news',[]))} articles cached")
        else:
            fail("/api/news", f"status {r.status_code}")
    except Exception as e:
        fail("/api/news", str(e))

    # Weather
    for city in ["London", "InvalidCity99999"]:
        try:
            r = get(f"/api/weather/{city}")
            if city == "InvalidCity99999":
                if "error" in r.json() or r.status_code >= 400:
                    ok(f"/api/weather/InvalidCity — graceful error response")
                else:
                    warn(f"/api/weather/InvalidCity — no error field returned", str(r.json()))
            else:
                if r.status_code == 200:
                    d = r.json()
                    ok(f"/api/weather/{city}", f"temp={d.get('temp')}°C  condition={d.get('condition')}")
                else:
                    fail(f"/api/weather/{city}", f"status {r.status_code}")
        except Exception as e:
            fail(f"/api/weather/{city}", str(e))

    # Chat endpoint — short round-trip
    try:
        t0 = time.time()
        r = post("/api/chat", {"message": "What time is it?", "history": []})
        ms = int((time.time()-t0)*1000)
        if r.status_code == 200:
            d = r.json()
            if "response" in d and "emotion" in d:
                ok(f"/api/chat — tool call round-trip", f"{ms}ms  emotion={d['emotion']!r}")
            else:
                fail("/api/chat — missing keys in response", str(d))
        else:
            fail(f"/api/chat", f"status {r.status_code}  body={r.text[:120]}")
    except Exception as e:
        fail("/api/chat", str(e))

    # CORS headers
    try:
        r = req.options(BASE + "/api/health", headers={"Origin":"http://localhost:5173"}, timeout=5)
        cors = r.headers.get("access-control-allow-origin","")
        if cors:
            ok("CORS headers present", f"allow-origin={cors!r}")
        else:
            warn("CORS — allow-origin header missing from OPTIONS response")
    except Exception as e:
        warn("CORS check failed", str(e))

    # 404 behaviour
    try:
        r = get("/api/doesnotexist")
        if r.status_code == 404:
            ok("Unknown route → 404")
        else:
            warn(f"Unknown route → {r.status_code} (expected 404)")
    except Exception as e:
        warn("404 check failed", str(e))

    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# 11. WEBSOCKET (optional — server must be running)
# ══════════════════════════════════════════════════════════════════════════════
def test_websocket():
    hdr("11 · WEBSOCKET  (server must be running on :8000)")
    try:
        import websockets
    except ImportError:
        warn("websockets package not installed", "pip install websockets")
        section_score(); return

    async def _ws_tests():
        url = "ws://localhost:8000/ws/agent"
        try:
            async with websockets.connect(url, open_timeout=5) as ws:
                ok("WebSocket connected")

                # Ping/pong
                await ws.send(json.dumps({"type": "ping"}))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                d   = json.loads(raw)
                if d.get("type") == "pong":
                    ok("Ping → Pong")
                else:
                    # might be news_update first
                    if d.get("type") == "news_update":
                        info("Received news_update on connect (expected)")
                        raw = await asyncio.wait_for(ws.recv(), timeout=5)
                        d   = json.loads(raw)
                        if d.get("type") == "pong":
                            ok("Ping → Pong (after news_update)")
                        else:
                            fail("Ping/Pong", f"got {d}")
                    else:
                        fail("Ping/Pong", f"got {d}")

                # clear_history
                await ws.send(json.dumps({"type": "clear_history"}))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                d   = json.loads(raw)
                if d.get("type") == "history_cleared":
                    ok("clear_history → history_cleared")
                else:
                    fail("clear_history", f"got {d}")

                # chat round-trip
                await ws.send(json.dumps({"type": "chat", "message": "What time is it?"}))

                # first response should be emotion:thinking
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                d   = json.loads(raw)
                if d.get("type") == "emotion" and d.get("emotion") == "thinking":
                    ok("Chat → thinking emotion received")
                else:
                    warn("Expected emotion:thinking first", f"got {d}")

                # then the actual response
                raw = await asyncio.wait_for(ws.recv(), timeout=45)
                d   = json.loads(raw)
                if d.get("type") == "response":
                    ok("Chat → response received", f"emotion={d.get('emotion')!r}  msg={d.get('message','')[:50]!r}")
                else:
                    fail("Chat response", f"got {d}")

        except (ConnectionRefusedError, OSError):
            warn("WebSocket — server not reachable on ws://localhost:8000/ws/agent")
            info("Start server first:  uvicorn main:app --reload --port 8000")
        except asyncio.TimeoutError:
            fail("WebSocket — timed out waiting for response")
        except Exception as e:
            fail("WebSocket — unexpected error", str(e))

    asyncio.run(_ws_tests())
    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# 12. LIVE TOOL API CALLS
# ══════════════════════════════════════════════════════════════════════════════
def test_live_tools():
    hdr("12 · LIVE TOOL API CALLS (weather + news)")
    try:
        import main as m
    except Exception as e:
        fail("Cannot import main", str(e)); return

    # Weather tool
    if os.getenv("OPENWEATHER_API_KEY"):
        for city in ["London", "Delhi", "FakeCityXYZ"]:
            try:
                r = m.get_weather.invoke({"city": city})
                if city == "FakeCityXYZ":
                    if "couldn't" in r.lower() or "sorry" in r.lower():
                        ok(f"get_weather({city}) — graceful error", r[:60])
                    else:
                        warn(f"get_weather({city}) — no error message", r[:60])
                else:
                    if "°C" in r:
                        ok(f"get_weather({city})", r[:70])
                    else:
                        warn(f"get_weather({city}) — odd response", r[:70])
            except Exception as e:
                fail(f"get_weather({city})", str(e))
    else:
        warn("get_weather — skipped (OPENWEATHER_API_KEY not set)")

    # News tool
    if os.getenv("TAVILY_API_KEY"):
        try:
            r = m.get_latest_news.invoke({"topic": "technology"})
            if "•" in r or "Latest" in r:
                ok("get_latest_news(technology)", r[:80])
            else:
                warn("get_latest_news — unexpected format", r[:80])
        except Exception as e:
            fail("get_latest_news", str(e))
    else:
        warn("get_latest_news — skipped (TAVILY_API_KEY not set)")

    section_score()


# ══════════════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
def final_report():
    total = passed + failed + warned
    bar   = "═" * 70
    print(f"\n{B}{bar}{RST}")
    print(f"{W}  ARIA DIAGNOSTIC REPORT{RST}")
    print(f"{B}{bar}{RST}")
    print(f"  {G}Passed : {passed:>4}{RST}")
    print(f"  {R}Failed : {failed:>4}{RST}")
    print(f"  {Y}Warned : {warned:>4}{RST}")
    print(f"  {DIM}Total  : {total:>4}{RST}")
    print(f"{B}{bar}{RST}")

    if failed == 0 and warned == 0:
        print(f"\n  {G}🎉  All clear — ARIA backend looks healthy!{RST}\n")
    elif failed == 0:
        print(f"\n  {Y}⚡  No failures, but review warnings above.{RST}\n")
    else:
        print(f"\n  {R}🔥  {failed} failure(s) detected — fix before deploying.{RST}\n")
        print(f"  {DIM}Common fixes:")
        print(f"    • 400 tool_call_id  →  use native Mistral SDK (not ChatMistralAI)")
        print(f"    • Missing package   →  pip install -r requirements.txt")
        print(f"    • Bad API key       →  check backend/.env{RST}\n")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARIA Deep Diagnostic")
    parser.add_argument("--no-live",  action="store_true", help="Skip real API calls")
    parser.add_argument("--ws",       action="store_true", help="Include WebSocket test")
    parser.add_argument("--only",     type=int,            help="Run only test section N (1-12)")
    args = parser.parse_args()

    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{C}  {'='*60}{RST}")
    print(f"{C}   ARIA Deep Diagnostic Suite          {DIM}{ts}{RST}")
    print(f"{C}  {'='*60}{RST}\n")

    all_tests = [
        (1,  "Environment Variables",   test_env),
        (2,  "Package Imports",         test_imports),
        (3,  "Static Analysis",         test_static),
        (4,  "Tool Schemas",            test_tool_schemas),
        (5,  "Helper Functions",        test_helpers),
        (6,  "Tools (offline)",         test_tools_offline),
        (7,  "Live API Keys",           test_live_apis),
        (8,  "Tool-call Round-trip",    test_tool_call_roundtrip),
        (9,  "invoke_agent E2E",        test_invoke_agent),
        (10, "REST Endpoints",          test_rest_endpoints),
        (11, "WebSocket",               test_websocket),
        (12, "Live Tool API Calls",     test_live_tools),
    ]

    skip_live = {7, 8, 9, 10, 12}
    skip_ws   = {11}

    for num, name, fn in all_tests:
        if args.only and args.only != num:
            continue
        if args.no_live and num in skip_live:
            hdr(f"{num} · {name}  [SKIPPED — --no-live]")
            info("Pass --no-live=false or remove flag to run")
            continue
        if num in skip_ws and not args.ws:
            hdr(f"{num} · {name}  [SKIPPED — pass --ws to enable]")
            info("Add --ws flag to include WebSocket test")
            continue
        try:
            fn()
        except Exception as e:
            fail(f"Section {num} crashed", traceback.format_exc(limit=3))

    final_report()
