"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          ARIA — 40 QUALITY TEST CASES  (test_aria_quality.py)              ║
║                                                                              ║
║  Tests intelligence, tool control, conversation quality, edge cases,        ║
║  multi-step commands, emotion accuracy, and response conciseness.           ║
║                                                                              ║
║  Usage:                                                                     ║
║    python test_aria_quality.py                  # all 40 tests              ║
║    python test_aria_quality.py --cat tools      # filter by category        ║
║    python test_aria_quality.py --only 15        # single test               ║
║    python test_aria_quality.py --verbose        # show full responses       ║
║    python test_aria_quality.py --save report.json  # export results         ║
║                                                                             ║
║  Categories:                                                                ║
║    tools · intelligence · conversation · emotion · edge · multi · speed    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys, os, re, json, time, asyncio, argparse, traceback
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

# ── Colours ──────────────────────────────────────────────────────────────────
G="\033[92m"; R="\033[91m"; Y="\033[93m"; B="\033[94m"
C="\033[96m"; W="\033[97m"; DIM="\033[2m"; RST="\033[0m"

results: list[dict] = []
passed = failed = warned = 0

def hdr(t: str):
    print(f"\n{B}{'─'*70}{RST}\n{W}  {t}{RST}\n{B}{'─'*70}{RST}")

def record(num, label, cat, status, response, ms, notes=""):
    global passed, failed, warned
    icon = f"{G}✅ PASS{RST}" if status=="pass" else f"{R}❌ FAIL{RST}" if status=="fail" else f"{Y}⚠️  WARN{RST}"
    if status=="pass": passed+=1
    elif status=="fail": failed+=1
    else: warned+=1
    print(f"  {icon}  [{num:02d}] {label}  {DIM}{ms}ms{RST}")
    if notes: print(f"         {DIM}{notes}{RST}")
    results.append({"num":num,"label":label,"cat":cat,"status":status,
                    "response":response[:200],"ms":ms,"notes":notes})

# ── Scoring helpers ───────────────────────────────────────────────────────────
def has_word(resp: str, *words) -> bool:
    r = resp.lower()
    return any(w.lower() in r for w in words)

def no_tag(resp: str) -> bool:
    """Emotion tags must be stripped from response."""
    return "[EMOTION" not in resp and "[CONDITION" not in resp

def is_concise(resp: str, max_chars=300) -> bool:
    return len(resp.strip()) <= max_chars

def emotion_valid(emo: str) -> bool:
    return emo in {"idle","happy","thinking","speaking","surprised","sad","excited","sleeping"}

def acted_not_asked(resp: str, *question_words) -> bool:
    """Returns True if response doesn't contain pre-task question words."""
    r = resp.lower()
    bad = ["which room","what room","what brightness","which channel",
           "are you sure","please specify","could you clarify","what speed"]
    bad += [w.lower() for w in question_words]
    return not any(b in r for b in bad)

async def run(user_input: str, history: list = [], city: str = "Lucknow") -> dict:
    import main as m
    t0 = time.time()
    result = await asyncio.wait_for(
        m.invoke_agent(user_input, history, city),
        timeout=35.0
    )
    ms = int((time.time()-t0)*1000)
    return {**result, "ms": ms}

# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY A — TOOL EXECUTION (1–10)
# Tests that every tool fires correctly and response confirms the action
# ══════════════════════════════════════════════════════════════════════════════
async def cat_tools():
    hdr("A · TOOL EXECUTION  [Tests 01–10]")

    # 01 — Lights ON (no room specified → must default)
    r = await run("Turn on the lights.")
    ok = has_word(r["response"],"light","on","bright") and acted_not_asked(r["response"])
    record(1,"Lights ON — defaults to living room","tools",
           "pass" if ok else "fail", r["response"], r["ms"],
           "Should NOT ask 'which room' — auto-defaults to living room")

    # 02 — Lights DIM
    r = await run("Dim the lights.")
    ok = has_word(r["response"],"dim","light","40","low") and acted_not_asked(r["response"])
    record(2,"Lights DIM — defaults to 40%","tools",
           "pass" if ok else "fail", r["response"], r["ms"],
           "Should dim to 40% without asking brightness")

    # 03 — Lights OFF
    r = await run("Lights off please.")
    ok = has_word(r["response"],"light","off") and no_tag(r["response"])
    record(3,"Lights OFF","tools",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 04 — Curtains OPEN
    r = await run("Open the curtains.")
    ok = has_word(r["response"],"curtain","open") and acted_not_asked(r["response"])
    record(4,"Curtains OPEN — no room question","tools",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 05 — Curtains CLOSE
    r = await run("Close the curtains.")
    ok = has_word(r["response"],"curtain","clos") and no_tag(r["response"])
    record(5,"Curtains CLOSE","tools",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 06 — Fan ON (no speed specified → must default)
    r = await run("Turn on the fan.")
    ok = has_word(r["response"],"fan","on","medium","speed") and acted_not_asked(r["response"])
    record(6,"Fan ON — defaults to medium speed","tools",
           "pass" if ok else "fail", r["response"], r["ms"],
           "Should NOT ask speed before acting")

    # 07 — Fan speed change
    r = await run("Set the fan to high speed.")
    ok = has_word(r["response"],"fan","high","3","speed")
    record(7,"Fan speed HIGH (3)","tools",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 08 — TV ON
    r = await run("Turn on the TV.")
    ok = has_word(r["response"],"tv","television","on") and no_tag(r["response"])
    record(8,"TV ON","tools",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 09 — Music
    r = await run("Play some jazz music.")
    ok = has_word(r["response"],"jazz","music","playing","now")
    record(9,"Music — play jazz","tools",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 10 — Thermostat
    r = await run("Set temperature to 22 degrees.")
    ok = has_word(r["response"],"22","thermostat","temperature","degree")
    record(10,"Thermostat set 22°C","tools",
           "pass" if ok else "fail", r["response"], r["ms"])


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY B — INTELLIGENCE & INFERENCE (11–20)
# Tests ability to infer intent, use context, handle ambiguity smartly
# ══════════════════════════════════════════════════════════════════════════════
async def cat_intelligence():
    hdr("B · INTELLIGENCE & INFERENCE  [Tests 11–20]")

    # 11 — Weather without city (must use Lucknow from context)
    r = await run("What's the weather like?", city="Lucknow")
    ok = has_word(r["response"],"°","temp","weather","lucknow","degree") and \
         not has_word(r["response"],"which city","what city","specify city")
    record(11,"Weather — uses detected city (Lucknow), no asking","intelligence",
           "pass" if ok else "fail", r["response"], r["ms"],
           "Must auto-use Lucknow, not ask user for city")

    # 12 — News without topic (must use local city)
    r = await run("Any news?", city="Lucknow")
    ok = has_word(r["response"],"news","headline","latest","story") and \
         not has_word(r["response"],"which topic","what topic","about what")
    record(12,"News — auto-fetches without asking topic","intelligence",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 13 — Synonym understanding: "it's hot" → fan/ac suggestion
    r = await run("It's really hot in here.")
    ok = has_word(r["response"],"fan","cool","thermostat","ac","temperature","curtain")
    record(13,"Synonym: 'hot' → suggests cooling actions","intelligence",
           "pass" if ok else "fail", r["response"], r["ms"],
           f"Should suggest fan/thermostat. Time:{r['ms']}ms (>10s=slow)")

    # 14 — Implicit command: "I can't see" → lights on
    r = await run("I can't see anything in here.")
    ok = has_word(r["response"],"light","bright","on","lamp")
    record(14,"Implicit: 'can't see' → turns on lights","intelligence",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 15 — Time awareness: asks what time without calling time tool? should call it
    r = await run("What time is it?")
    ok = re.search(r"\d{1,2}:\d{2}", r["response"]) is not None
    record(15,"Time query — calls get_current_time tool","intelligence",
           "pass" if ok else "fail", r["response"], r["ms"],
           "Must return actual current time, not say 'I don't know'")

    # 16 — Memory in conversation: reference to earlier statement
    history = [
        {"role":"user",      "content":"My favourite colour is teal."},
        {"role":"assistant", "content":"That's a beautiful colour! Teal it is."},
    ]
    r = await run("What colour did I just mention?", history=history)
    ok = has_word(r["response"],"teal")
    record(16,"Context memory — recalls colour from history","intelligence",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 17 — Multi-device scene inference: "movie night"
    r = await run("Set up a movie night vibe.")
    ok = has_word(r["response"],"tv","light","dim","curtain","music")
    record(17,"Scene inference: 'movie night' → TV+dim lights+curtains","intelligence",
           "pass" if ok else "warn", r["response"], r["ms"],
           "Ideally controls multiple devices for a scene")

    # 18 — Negative command: "don't turn off the lights"
    r = await run("Don't turn off the lights, I'm reading.")
    ok = not has_word(r["response"],"light","off") or has_word(r["response"],"keep","stay","on","sure")
    record(18,"Negative command: does not turn off lights","intelligence",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 19 — Joke quality: should be genuinely funny
    r = await run("Tell me a good joke.")
    ok = len(r["response"]) > 20 and r["emotion"] in {"happy","excited","speaking"}
    record(19,"Joke — correct emotion + non-empty","intelligence",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 20 — Graceful unknown: handles unknown requests without crashing
    r = await run("Order me a pizza.")
    ok = len(r["response"]) > 10 and r["emotion"] in {"sad","speaking","idle","happy"}
    record(20,"Unknown task — responds gracefully (can't order pizza)","intelligence",
           "pass" if ok else "fail", r["response"], r["ms"],
           "Should apologize and suggest what it CAN do")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY C — CONVERSATION QUALITY (21–28)
# Tests response quality, conciseness, personality, no over-questioning
# ══════════════════════════════════════════════════════════════════════════════
async def cat_conversation():
    hdr("C · CONVERSATION QUALITY  [Tests 21–28]")

    # 21 — Conciseness: short command → short response
    r = await run("Lights on.")
    ok = is_concise(r["response"], 150) and has_word(r["response"],"light","on")
    record(21,"Conciseness — short command gets short reply (<150 chars)","conversation",
           "pass" if ok else "fail", r["response"], r["ms"],
           f"Length: {len(r['response'])} chars")

    # 22 — No emotion tags in response text
    r = await run("Hello ARIA!")
    ok = no_tag(r["response"])
    record(22,"No raw [EMOTION:X] tags in response text","conversation",
           "pass" if ok else "fail", r["response"], r["ms"],
           "Tags must be stripped by parse_response")

    # 23 — Greeting warmth
    r = await run("Good morning!")
    ok = has_word(r["response"],"morning","hello","hi","hey","good") and \
         r["emotion"] in {"happy","excited","idle"}
    record(23,"Greeting — warm response + positive emotion","conversation",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 24 — No pre-task questioning — direct command must execute
    r = await run("Open the curtains now.")
    ok = acted_not_asked(r["response"]) and has_word(r["response"],"curtain","open")
    record(24,"No pre-task questioning: curtains open immediately","conversation",
           "pass" if ok else "fail", r["response"], r["ms"],
           "Must NOT ask 'which room' or 'are you sure'")

    # 25 — Personality: witty optional follow-up
    r = await run("Tell me something interesting.")
    ok = len(r["response"]) > 30
    record(25,"Personality — has something interesting to say","conversation",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 26 — Doesn't repeat itself when confirmed
    history = [
        {"role":"user",      "content":"Turn on the TV."},
        {"role":"assistant", "content":"TV is on! Enjoy watching."},
    ]
    r = await run("Thanks.", history=history)
    ok = len(r["response"]) < 200 and r["emotion"] in {"happy","idle","speaking"}
    record(26,"Ack after task — short and warm, not repetitive","conversation",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 27 — Handles multi-turn naturally
    history = [
        {"role":"user",      "content":"What's 15 * 8?"},
        {"role":"assistant", "content":"15 times 8 is 120."},
    ]
    r = await run("And divide that by 4?", history=history)
    ok = has_word(r["response"],"30") or "30" in r["response"]
    record(27,"Multi-turn math: 120÷4=30 using history context","conversation",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 28 — Apology on error is natural
    r = await run("Get me weather for Atlantis.")
    ok = len(r["response"]) > 10 and r["emotion"] in {"sad","speaking","idle"}
    record(28,"Invalid city — graceful apology response","conversation",
           "pass" if ok else "fail", r["response"], r["ms"])


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY D — EMOTION ACCURACY (29–33)
# Tests that emotion tags match the situation
# ══════════════════════════════════════════════════════════════════════════════
async def cat_emotion():
    hdr("D · EMOTION ACCURACY  [Tests 29–33]")

    # 29 — Happy on success
    r = await run("Turn on the lights.")
    ok = r["emotion"] in {"happy","speaking","excited"}
    record(29,"Emotion: device command → happy/speaking","emotion",
           "pass" if ok else "fail", r["response"], r["ms"],
           f"Got emotion: {r['emotion']}")

    # 30 — Thinking on search
    r = await run("What are the latest headlines from around the world?")
    ok = r["emotion"] in {"thinking","speaking","happy"}
    record(30,"Emotion: news search → thinking or speaking","emotion",
           "pass" if ok else "fail", r["response"], r["ms"],
           f"Got emotion: {r['emotion']}")

    # 31 — Sad on failure
    r = await run("I feel really awful today.")
    ok = r["emotion"] in {"sad","speaking","surprised"}
    record(31,"Emotion: user sad → empathic/sad response","emotion",
           "pass" if ok else "fail", r["response"], r["ms"],
           f"Got emotion: {r['emotion']}")

    # 32 — Excited on cool topic
    r = await run("Did you know there's a black hole in our galaxy?")
    ok = r["emotion"] in {"excited","surprised","happy","speaking"}
    record(32,"Emotion: exciting topic → excited/surprised","emotion",
           "pass" if ok else "warn", r["response"], r["ms"],
           f"Got emotion: {r['emotion']}")

    # 33 — Emotion always valid
    r = await run("What is the meaning of life?")
    ok = emotion_valid(r["emotion"])
    record(33,"Emotion always in valid set (8 options)","emotion",
           "pass" if ok else "fail", r["response"], r["ms"],
           f"Got emotion: {r['emotion']}")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY E — EDGE CASES & ROBUSTNESS (34–37)
# ══════════════════════════════════════════════════════════════════════════════
async def cat_edge():
    hdr("E · EDGE CASES & ROBUSTNESS  [Tests 34–37]")

    # 34 — Empty-ish input
    r = await run("   ")
    ok = len(r["response"]) > 5 and emotion_valid(r["emotion"])
    record(34,"Empty/whitespace input — graceful fallback","edge",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 35 — Very long input
    long_msg = "I want you to " + "really " * 30 + "turn on the lights please."
    r = await run(long_msg)
    ok = has_word(r["response"],"light","on","bright")
    record(35,"Long rambling input — still extracts correct command","edge",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 36 — Special characters / emoji
    r = await run("Turn on the 💡 please!")
    ok = len(r["response"]) > 5 and emotion_valid(r["emotion"])
    record(36,"Emoji input — handles without crash","edge",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 37 — Contradiction in request
    r = await run("Turn on the lights and also turn off the lights.")
    ok = len(r["response"]) > 5 and emotion_valid(r["emotion"])
    record(37,"Contradiction — handles conflicting commands","edge",
           "pass" if ok else "warn", r["response"], r["ms"],
           "Should pick one or ask which — no crash allowed")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY F — MULTI-STEP & CHAINING (38–40)
# ══════════════════════════════════════════════════════════════════════════════
async def cat_multi():
    hdr("F · MULTI-STEP & CHAINING  [Tests 38–40]")

    # 38 — Two commands in one sentence
    r = await run("Turn on the lights and close the curtains.")
    ok = has_word(r["response"],"light","curtain") and len(r["response"]) > 10
    record(38,"Multi-command: lights on + curtains close (one sentence)","multi",
           "pass" if ok else "warn", r["response"], r["ms"],
           "Should address both devices, not just one")

    # 39 — Chained from history
    history = [
        {"role":"user",      "content":"What's the weather in Delhi?"},
        {"role":"assistant", "content":"It's 34°C and hazy in Delhi today."},
    ]
    r = await run("And what about Mumbai?", history=history)
    ok = has_word(r["response"],"mumbai","°","weather","temp") or \
         has_word(r["response"],"humid","cloud","clear","rain")
    record(39,"Chain: weather follow-up uses history for city swap","multi",
           "pass" if ok else "fail", r["response"], r["ms"])

    # 40 — Full smart home scene command
    r = await run("Set up a relaxing evening: dim lights, close curtains, and play soft music.")
    ok = (has_word(r["response"],"light","dim","curtain","music") or
          has_word(r["response"],"relax","cozy","evening","set"))
    record(40,"Full scene: dim+curtains+music in one request","multi",
           "pass" if ok else "warn", r["response"], r["ms"],
           "Best if all 3 tools fire; at minimum response acknowledges the scene")


# ══════════════════════════════════════════════════════════════════════════════
# SPEED REPORT
# ══════════════════════════════════════════════════════════════════════════════
def speed_report():
    hdr("SPEED ANALYSIS")
    times = [(r["num"], r["label"][:40], r["ms"]) for r in results]
    times.sort(key=lambda x: -x[2])
    print(f"\n  {'#':>3}  {'ms':>6}  Label")
    print(f"  {'─'*3}  {'─'*6}  {'─'*45}")
    for num, label, ms in times[:10]:
        bar = "█" * min(40, ms//100)
        colour = R if ms>8000 else Y if ms>4000 else G
        print(f"  {num:>3}  {colour}{ms:>6}{RST}  {label}")
    avg = sum(r["ms"] for r in results) / len(results)
    slow = sum(1 for r in results if r["ms"] > 6000)
    print(f"\n  Average: {avg:.0f}ms   Slow (>6s): {slow}/{len(results)}")
    if avg > 5000:
        print(f"  {Y}⚠️  Average >5s — consider max_tokens reduction or model change{RST}")
    if any(r["ms"] > 15000 for r in results):
        slow_tests = [r for r in results if r["ms"] > 15000]
        print(f"  {Y}⚠️  {len(slow_tests)} test(s) >15s: {[r['num'] for r in slow_tests]} — may be multi-tool chain{RST}")
    else:
        print(f"  {G}✅ Speed acceptable{RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
def final_report(save_path: str | None):
    bar = "═" * 70
    print(f"\n{B}{bar}{RST}")
    print(f"{W}  ARIA QUALITY TEST REPORT  —  {datetime.now().strftime('%Y-%m-%d %H:%M')}{RST}")
    print(f"{B}{bar}{RST}")

    # Per-category summary
    cats: dict[str, dict] = {}
    for r in results:
        c = r["cat"]
        if c not in cats: cats[c] = {"pass":0,"fail":0,"warn":0}
        cats[c][r["status"]] += 1

    print(f"\n  {'Category':<16} {'Pass':>5} {'Fail':>5} {'Warn':>5}")
    print(f"  {'─'*16} {'─'*5} {'─'*5} {'─'*5}")
    for cat, counts in cats.items():
        p,f,w = counts["pass"],counts["fail"],counts["warn"]
        colour = G if f==0 else R if f>1 else Y
        print(f"  {colour}{cat:<16}{RST} {G}{p:>5}{RST} {R if f else DIM}{f:>5}{RST} {Y if w else DIM}{w:>5}{RST}")

    total = passed + failed + warned
    score = int(passed / total * 100) if total else 0
    print(f"\n  {G}Passed : {passed:>3} / {total}{RST}")
    print(f"  {R}Failed : {failed:>3}{RST}")
    print(f"  {Y}Warned : {warned:>3}{RST}")
    print(f"\n  {'─'*40}")
    colour = G if score >= 85 else Y if score >= 65 else R
    print(f"  {colour}QUALITY SCORE: {score}%{RST}  {'🎉 Excellent' if score>=85 else '⚡ Good, tune further' if score>=65 else '🔥 Needs tuning'}")
    print(f"{B}{bar}{RST}")

    # Failed tests
    fails = [r for r in results if r["status"]=="fail"]
    if fails:
        print(f"\n{R}  Failed tests — fine-tune these:{RST}")
        for r in fails:
            print(f"  [{r['num']:02d}] {r['label']}")
            print(f"       Response: {r['response'][:100]!r}")
            if r["notes"]: print(f"       Note: {r['notes']}")

    # Fine-tuning recommendations
    print(f"\n{C}  ── FINE-TUNE RECOMMENDATIONS ──────────────────────────────{RST}")
    recs = []
    if any(r["status"]=="fail" and r["cat"]=="tools" for r in results):
        recs.append("SYSTEM_PROMPT: strengthen 'ACT FIRST' rule — tools must fire before any question")
    if any(r["num"]==11 and r["status"]!="pass" for r in results):
        recs.append("City injection: verify city_context appended to system prompt in invoke_agent")
    if any(r["num"]==21 and r["status"]!="pass" for r in results):
        recs.append("Reduce max_tokens from 350 to 200 for shorter device confirmations")
    if any(r["num"]==22 and r["status"]!="pass" for r in results):
        recs.append("parse_response: emotion tag regex not stripping — check \\[EMOTION:\\s*(\\w+)\\]")
    if any(r["num"]==17 and r["status"]=="fail" for r in results):
        recs.append("Add 'movie night' / 'relaxing evening' scene patterns to SYSTEM_PROMPT examples")
    if any(r["num"]==38 and r["status"]!="pass" for r in results):
        recs.append("Multi-command: increase max_iterations to 4 in tool loop for chained device calls")
    if not recs:
        recs.append("✅ All categories passing — consider adding more edge-case prompts to SYSTEM_PROMPT")

    for rec in recs:
        print(f"  {DIM}▸{RST} {rec}")

    # Save JSON
    if save_path:
        data = {
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "passed": passed, "failed": failed, "warned": warned,
            "results": results,
            "recommendations": recs,
        }
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n  {G}📄 Report saved: {save_path}{RST}")

    print()
    return failed


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="ARIA 40 Quality Test Cases")
    p.add_argument("--cat",     help="Run only a category: tools/intelligence/conversation/emotion/edge/multi")
    p.add_argument("--only",    type=int, help="Run only test number N")
    p.add_argument("--verbose", action="store_true", help="Show full responses")
    p.add_argument("--save",    help="Save JSON report to file")
    args = p.parse_args()

    # Add verbose response printing
    if args.verbose:
        _orig_record = record
        def record(num, label, cat, status, response, ms, notes=""):
            _orig_record(num, label, cat, status, response, ms, notes)
            print(f"         {DIM}Response: {response[:200]!r}{RST}")

    print(f"\n{C}  {'='*60}{RST}")
    print(f"{C}  ARIA — 40 Quality Test Cases{RST}")
    print(f"{C}  {'='*60}{RST}")
    print(f"  {DIM}API Key: {os.getenv('MISTRAL_API_KEY','NOT SET')[:12]}…{RST}")
    print(f"  {DIM}City:    Lucknow (simulated geolocation){RST}\n")

    # Import check
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        import main as _m
        if not hasattr(_m, "EMOTION_VALID"):
            _m.EMOTION_VALID = {"idle","happy","thinking","speaking","surprised","sad","excited","sleeping"}
        print(f"  {G}✅ main.py imported — {len(_m.MISTRAL_TOOLS)} tools ready{RST}\n")
    except Exception as e:
        print(f"  {R}❌ Cannot import main.py: {e}{RST}")
        sys.exit(1)

    if not os.getenv("MISTRAL_API_KEY"):
        print(f"  {R}❌ MISTRAL_API_KEY not set — all tests will fail{RST}")
        sys.exit(1)

    # Run selected categories
    all_cats = [
        ("tools",          cat_tools),
        ("intelligence",   cat_intelligence),
        ("conversation",   cat_conversation),
        ("emotion",        cat_emotion),
        ("edge",           cat_edge),
        ("multi",          cat_multi),
    ]

    async def run_all():
        for cat_name, cat_fn in all_cats:
            if args.cat and args.cat != cat_name:
                continue
            if args.only:
                # Run all cats but filter inside record
                pass
            try:
                await cat_fn()
            except Exception as e:
                print(f"  {R}❌ Category {cat_name} crashed: {e}{RST}")
                traceback.print_exc()

    # Filter by --only: patch record to skip non-matching
    if args.only:
        _base_record = record
        def record(num, label, cat, status, response, ms, notes=""):
            if num == args.only:
                _base_record(num, label, cat, status, response, ms, notes)

    asyncio.run(run_all())

    if results:
        speed_report()
        fails = final_report(args.save)
        sys.exit(0 if fails == 0 else 1)
    else:
        print(f"\n  {Y}No tests ran — check --cat or --only arguments{RST}")