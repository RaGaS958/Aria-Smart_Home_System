"""
test_helpers.py — Unit tests for parse_response() and invoke_agent().

parse_response  strips [EMOTION:X] and [CONDITION:Y] tags, extracts
                emotion/condition values, handles edge cases.

invoke_agent    builds chat history correctly, calls AgentExecutor,
                returns parsed dict, handles exceptions gracefully.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from main import parse_response, invoke_agent


# ──────────────────────────────────────────────────────────────────────────────
# parse_response
# ──────────────────────────────────────────────────────────────────────────────

class TestParseResponse:

    # ── Emotion extraction ────────────────────────────────────────────────────

    def test_extracts_emotion_tag(self):
        result = parse_response("[EMOTION:happy] Hello there!")
        assert result["emotion"] == "happy"

    def test_removes_emotion_tag_from_response(self):
        result = parse_response("[EMOTION:happy] Hello there!")
        assert "[EMOTION" not in result["response"]

    def test_response_text_stripped(self):
        result = parse_response("[EMOTION:sad]   Lots of spaces around   ")
        assert result["response"] == "Lots of spaces around"

    def test_default_emotion_when_missing(self):
        result = parse_response("No emotion tag here.")
        assert result["emotion"] == "speaking"

    def test_all_valid_emotions_extracted(self):
        valid = ["idle", "happy", "thinking", "speaking", "surprised", "sad", "excited", "sleeping"]
        for emo in valid:
            result = parse_response(f"[EMOTION:{emo}] Message.")
            assert result["emotion"] == emo, f"Failed for emotion: {emo}"

    def test_emotion_normalised_to_lowercase(self):
        result = parse_response("[EMOTION:HAPPY] Hi!")
        assert result["emotion"] == "happy"

    def test_unknown_emotion_still_extracted(self):
        """Unknown emotion tokens pass through (validation is the caller's job)."""
        result = parse_response("[EMOTION:dancing] Whee!")
        assert result["emotion"] == "dancing"

    # ── Condition extraction ─────────────────────────────────────────────────

    def test_extracts_condition_tag(self):
        result = parse_response("[EMOTION:speaking] [CONDITION:Rain] It's raining.")
        assert result["condition"] == "Rain"

    def test_removes_condition_tag_from_response(self):
        result = parse_response("[EMOTION:speaking] [CONDITION:Clear] Sunny day.")
        assert "[CONDITION" not in result["response"]

    def test_condition_none_when_absent(self):
        result = parse_response("[EMOTION:idle] Just a chat message.")
        assert result["condition"] is None

    def test_all_condition_types(self):
        conditions = ["Clear", "Clouds", "Rain", "Snow", "Thunderstorm", "Drizzle"]
        for cond in conditions:
            result = parse_response(f"[CONDITION:{cond}] weather info")
            assert result["condition"] == cond

    # ── Response text integrity ──────────────────────────────────────────────

    def test_response_text_preserved_with_both_tags(self):
        raw = "[EMOTION:speaking] [CONDITION:Clear] The sky is blue and the sun is shining."
        result = parse_response(raw)
        assert result["response"] == "The sky is blue and the sun is shining."

    def test_empty_string_input(self):
        result = parse_response("")
        assert result["emotion"] == "speaking"
        assert result["response"] == ""
        assert result["condition"] is None

    def test_only_emotion_tag_input(self):
        result = parse_response("[EMOTION:idle]")
        assert result["emotion"] == "idle"
        assert result["response"] == ""

    def test_multiline_response_preserved(self):
        raw = "[EMOTION:speaking] Line one.\nLine two.\nLine three."
        result = parse_response(raw)
        assert "Line one." in result["response"]
        assert "Line two." in result["response"]
        assert "Line three." in result["response"]

    def test_response_with_special_characters(self):
        raw = "[EMOTION:happy] Temperature: 22.5°C — feels like 20°C!"
        result = parse_response(raw)
        assert "22.5°C" in result["response"]
        assert "20°C" in result["response"]

    def test_returns_dict_with_all_keys(self):
        result = parse_response("[EMOTION:idle] Hello.")
        assert set(result.keys()) == {"response", "emotion", "condition"}

    def test_tag_in_middle_of_sentence(self):
        """Tag can appear anywhere — tool output embeds CONDITION mid-string."""
        raw = "The [CONDITION:Snow] weather is cold today."
        result = parse_response(raw)
        assert result["condition"] == "Snow"
        assert "[CONDITION" not in result["response"]

    def test_duplicate_emotion_tags_uses_first(self):
        """Only the first EMOTION tag should be extracted (re.search behaviour)."""
        raw = "[EMOTION:happy] [EMOTION:sad] Mixed feelings."
        result = parse_response(raw)
        assert result["emotion"] == "happy"


# ──────────────────────────────────────────────────────────────────────────────
# invoke_agent
# ──────────────────────────────────────────────────────────────────────────────


# ── Helper: patch asyncio.to_thread (AgentExecutor is Pydantic — cannot setattr.invoke) ──
# invoke_agent calls: await asyncio.to_thread(agent_executor.invoke, {...})
# We intercept at the asyncio.to_thread boundary so no Pydantic restriction applies.

def _thread_mock(output: str):
    """Return an AsyncMock that resolves to a fake AgentExecutor result dict."""
    return AsyncMock(return_value={"output": output})

def _thread_error(exc: Exception):
    """Return an AsyncMock that raises exc (simulates agent crash)."""
    return AsyncMock(side_effect=exc)


class TestInvokeAgent:

    @pytest.mark.asyncio
    async def test_returns_dict_with_expected_keys(self):
        with patch("asyncio.to_thread", _thread_mock("[EMOTION:happy] Hello!")):
            result = await invoke_agent("hi", [])
        assert "response"  in result
        assert "emotion"   in result
        assert "condition" in result

    @pytest.mark.asyncio
    async def test_emotion_parsed_correctly(self):
        with patch("asyncio.to_thread", _thread_mock("[EMOTION:thinking] Let me check...")):
            result = await invoke_agent("What's the weather?", [])
        assert result["emotion"] == "thinking"

    @pytest.mark.asyncio
    async def test_response_text_cleaned(self):
        with patch("asyncio.to_thread", _thread_mock("[EMOTION:speaking] It is 22°C in London.")):
            result = await invoke_agent("weather", [])
        assert result["response"] == "It is 22°C in London."
        assert "[EMOTION" not in result["response"]

    @pytest.mark.asyncio
    async def test_history_limited_to_8_messages(self):
        """invoke_agent should only pass the last 8 history items."""
        captured_calls = []

        async def fake_thread(fn, inp):
            captured_calls.append(inp)
            return {"output": "[EMOTION:idle] OK"}

        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
            for i in range(12)
        ]

        with patch("asyncio.to_thread", side_effect=fake_thread):
            await invoke_agent("new question", history)

        passed_history = captured_calls[0]["chat_history"]
        assert len(passed_history) == 8

    @pytest.mark.asyncio
    async def test_history_roles_converted_to_langchain_messages(self):
        from langchain_core.messages import HumanMessage, AIMessage
        captured = []

        async def fake_thread(fn, inp):
            captured.append(inp["chat_history"])
            return {"output": "[EMOTION:idle] done"}

        history = [
            {"role": "user",      "content": "Hello ARIA"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        with patch("asyncio.to_thread", side_effect=fake_thread):
            await invoke_agent("next", history)

        msgs = captured[0]
        assert isinstance(msgs[0], HumanMessage)
        assert isinstance(msgs[1], AIMessage)
        assert msgs[0].content == "Hello ARIA"
        assert msgs[1].content == "Hi there!"

    @pytest.mark.asyncio
    async def test_empty_history_works(self):
        with patch("asyncio.to_thread", _thread_mock("[EMOTION:happy] Sure!")):
            result = await invoke_agent("tell me a joke", [])
        assert result["emotion"] == "happy"

    @pytest.mark.asyncio
    async def test_exception_returns_sad_emotion(self):
        with patch("asyncio.to_thread", _thread_error(RuntimeError("LLM unreachable"))):
            result = await invoke_agent("anything", [])
        assert result["emotion"] == "sad"

    @pytest.mark.asyncio
    async def test_exception_response_truncated(self):
        """Error messages from exceptions must be ≤ 100 chars total in the response."""
        long_error = "X" * 200
        with patch("asyncio.to_thread", _thread_error(RuntimeError(long_error))):
            result = await invoke_agent("anything", [])
        assert len(result["response"]) <= 100

    @pytest.mark.asyncio
    async def test_condition_forwarded_from_tool_output(self):
        with patch("asyncio.to_thread",
                   _thread_mock("[EMOTION:speaking] [CONDITION:Rain] It's raining.")):
            result = await invoke_agent("weather?", [])
        assert result["condition"] == "Rain"

    @pytest.mark.asyncio
    async def test_condition_none_when_not_weather(self):
        with patch("asyncio.to_thread", _thread_mock("[EMOTION:happy] Here's a joke!")):
            result = await invoke_agent("joke?", [])
        assert result["condition"] is None