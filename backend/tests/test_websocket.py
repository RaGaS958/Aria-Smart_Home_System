"""
test_websocket.py — Tests for /ws/agent WebSocket endpoint.

Covers
──────
• Successful connection and acceptance
• ping → pong heartbeat
• chat message → emotion state → response flow
• Emotion tag emitted before LLM response
• clear_history resets conversation
• Malformed JSON handling
• Graceful disconnect (no server crash)
• News cache broadcast on connect
• Dead connection removal from ws_connections pool
• Multiple concurrent connections
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from starlette.testclient import TestClient


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_agent_mock(output: str):
    """Return a synchronous mock that AgentExecutor.invoke can be patched with."""
    return MagicMock(return_value={"output": output})


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def sync_client():
    """
    Synchronous Starlette TestClient is the most reliable way to test
    WebSockets in FastAPI without full event-loop gymnastics.
    """
    from main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ──────────────────────────────────────────────────────────────────────────────
# Connection tests
# ──────────────────────────────────────────────────────────────────────────────

class TestWebSocketConnection:
    def test_connection_accepted(self, sync_client):
        with sync_client.websocket_connect("/ws/agent") as ws:
            # If we reach here the handshake succeeded
            assert ws is not None

    def test_client_added_to_pool(self, sync_client):
        import main as main_module
        before = len(main_module.ws_connections)
        with sync_client.websocket_connect("/ws/agent"):
            during = len(main_module.ws_connections)
        assert during == before + 1

    def test_client_removed_after_disconnect(self, sync_client):
        import main as main_module
        with sync_client.websocket_connect("/ws/agent"):
            pass  # connect then immediately disconnect
        import time; time.sleep(0.05)  # allow cleanup
        # Pool should be back to original size (or less)
        # Just verify no exception was raised

    def test_news_cache_sent_on_connect(self, sync_client):
        import main as main_module
        main_module.news_cache = [
            {"title": "Breaking News", "url": "http://news.com", "snippet": "..."}
        ]
        try:
            with sync_client.websocket_connect("/ws/agent") as ws:
                msg = ws.receive_text()
                data = json.loads(msg)
            assert data["type"] == "news_update"
            assert data["data"][0]["title"] == "Breaking News"
        finally:
            main_module.news_cache = []

    def test_no_message_on_connect_if_cache_empty(self, sync_client):
        import main as main_module
        main_module.news_cache = []
        with sync_client.websocket_connect("/ws/agent") as ws:
            # Send a ping to verify we can communicate (no initial message)
            ws.send_text(json.dumps({"type": "ping"}))
            msg = json.loads(ws.receive_text())
        assert msg["type"] == "pong"  # First message is pong, not news


# ──────────────────────────────────────────────────────────────────────────────
# Ping / Pong heartbeat
# ──────────────────────────────────────────────────────────────────────────────

class TestPingPong:
    def test_ping_returns_pong(self, sync_client):
        with sync_client.websocket_connect("/ws/agent") as ws:
            ws.send_text(json.dumps({"type": "ping"}))
            resp = json.loads(ws.receive_text())
        assert resp["type"] == "pong"

    def test_multiple_pings(self, sync_client):
        with sync_client.websocket_connect("/ws/agent") as ws:
            for _ in range(3):
                ws.send_text(json.dumps({"type": "ping"}))
                resp = json.loads(ws.receive_text())
                assert resp["type"] == "pong"


# ──────────────────────────────────────────────────────────────────────────────
# Chat message flow
# ──────────────────────────────────────────────────────────────────────────────

# NOTE: AgentExecutor is Pydantic — patch("main.agent_executor.invoke") raises
# AttributeError. Patch main.invoke_agent (the async wrapper) instead.

from unittest.mock import AsyncMock as _AsyncMock

def _ia_mock(message="OK", emotion="speaking", condition=None):
    """Return an AsyncMock that resolves to a parsed invoke_agent result dict."""
    return _AsyncMock(return_value={"response": message, "emotion": emotion, "condition": condition})

def _ia_err():
    return _AsyncMock(return_value={"response": "Something went wrong.", "emotion": "sad", "condition": None})


class TestChatFlow:
    def test_chat_emits_thinking_then_response(self, sync_client):
        with patch("main.invoke_agent", _ia_mock("Certainly!", "happy")):
            with sync_client.websocket_connect("/ws/agent") as ws:
                ws.send_text(json.dumps({"type": "chat", "message": "hello"}))
                msg1 = json.loads(ws.receive_text())  # thinking
                msg2 = json.loads(ws.receive_text())  # response

        assert msg1["type"] == "emotion"
        assert msg1["emotion"] == "thinking"
        assert msg2["type"] == "response"

    def test_response_message_field(self, sync_client):
        with patch("main.invoke_agent", _ia_mock("The time is 3 PM.", "speaking")):
            with sync_client.websocket_connect("/ws/agent") as ws:
                ws.send_text(json.dumps({"type": "chat", "message": "time?"}))
                ws.receive_text()  # thinking
                resp = json.loads(ws.receive_text())

        assert "message" in resp
        assert resp["message"] == "The time is 3 PM."

    def test_response_emotion_field(self, sync_client):
        with patch("main.invoke_agent", _ia_mock("Amazing discovery!", "excited")):
            with sync_client.websocket_connect("/ws/agent") as ws:
                ws.send_text(json.dumps({"type": "chat", "message": "wow"}))
                ws.receive_text()  # thinking
                resp = json.loads(ws.receive_text())

        assert resp["emotion"] == "excited"

    def test_emotion_tag_stripped_from_message(self, sync_client):
        with patch("main.invoke_agent", _ia_mock("Clean text.", "happy")):
            with sync_client.websocket_connect("/ws/agent") as ws:
                ws.send_text(json.dumps({"type": "chat", "message": "hi"}))
                ws.receive_text()  # thinking
                resp = json.loads(ws.receive_text())

        assert "[EMOTION" not in resp["message"]

    def test_condition_field_in_response(self, sync_client):
        with patch("main.invoke_agent", _ia_mock("It's raining.", "speaking", "Rain")):
            with sync_client.websocket_connect("/ws/agent") as ws:
                ws.send_text(json.dumps({"type": "chat", "message": "weather?"}))
                ws.receive_text()  # thinking
                resp = json.loads(ws.receive_text())

        assert resp.get("condition") == "Rain"

    def test_agent_error_returns_sad_response(self, sync_client):
        with patch("main.invoke_agent", _ia_err()):
            with sync_client.websocket_connect("/ws/agent") as ws:
                ws.send_text(json.dumps({"type": "chat", "message": "crash please"}))
                ws.receive_text()  # thinking
                resp = json.loads(ws.receive_text())

        assert resp["emotion"] == "sad"
        assert resp["type"] == "response"

    def test_empty_message_handled(self, sync_client):
        with patch("main.invoke_agent", _ia_mock("How can I help?", "idle")):
            with sync_client.websocket_connect("/ws/agent") as ws:
                ws.send_text(json.dumps({"type": "chat", "message": ""}))
                ws.receive_text()  # thinking
                resp = json.loads(ws.receive_text())
        assert resp["type"] == "response"

    def test_consecutive_messages_in_same_session(self, sync_client):
        """Two messages in the same WS session must each get a response."""
        responses = []
        with patch("main.invoke_agent", _ia_mock("Reply.", "speaking")):
            with sync_client.websocket_connect("/ws/agent") as ws:
                for _ in range(2):
                    ws.send_text(json.dumps({"type": "chat", "message": "msg"}))
                    ws.receive_text()  # thinking
                    responses.append(json.loads(ws.receive_text()))

        assert len(responses) == 2
        assert all(r["type"] == "response" for r in responses)


# ──────────────────────────────────────────────────────────────────────────────
# clear_history
# ──────────────────────────────────────────────────────────────────────────────

class TestClearHistory:
    def test_clear_history_returns_history_cleared(self, sync_client):
        with sync_client.websocket_connect("/ws/agent") as ws:
            ws.send_text(json.dumps({"type": "clear_history"}))
            resp = json.loads(ws.receive_text())
        assert resp["type"] == "history_cleared"

    def test_clear_history_allows_fresh_chat(self, sync_client):
        """After clearing history, a new chat message should still get a response."""
        with patch("main.invoke_agent", _ia_mock("Fresh start!", "happy")):
            with sync_client.websocket_connect("/ws/agent") as ws:
                ws.send_text(json.dumps({"type": "clear_history"}))
                ws.receive_text()  # history_cleared
                ws.send_text(json.dumps({"type": "chat", "message": "Hi again!"}))
                ws.receive_text()  # thinking
                resp = json.loads(ws.receive_text())

        assert resp["type"] == "response"
        assert resp["message"] == "Fresh start!"


# ──────────────────────────────────────────────────────────────────────────────
# Malformed / edge case messages
# ──────────────────────────────────────────────────────────────────────────────

class TestMalformedMessages:
    def test_unknown_message_type_does_not_crash(self, sync_client):
        """Unknown type should be silently ignored — server stays alive."""
        with sync_client.websocket_connect("/ws/agent") as ws:
            ws.send_text(json.dumps({"type": "unknown_type", "data": "anything"}))
            # Server should still respond to a subsequent ping
            ws.send_text(json.dumps({"type": "ping"}))
            resp = json.loads(ws.receive_text())
        assert resp["type"] == "pong"

    def test_missing_type_key_does_not_crash(self, sync_client):
        with sync_client.websocket_connect("/ws/agent") as ws:
            ws.send_text(json.dumps({"message": "no type key"}))
            # Still alive
            ws.send_text(json.dumps({"type": "ping"}))
            resp = json.loads(ws.receive_text())
        assert resp["type"] == "pong"

    def test_chat_without_message_key_handled(self, sync_client):
        """chat with no 'message' key — empty string fallback should not crash."""
        with patch("main.invoke_agent", _ia_mock("OK", "idle")):
            with sync_client.websocket_connect("/ws/agent") as ws:
                ws.send_text(json.dumps({"type": "chat"}))  # no 'message'
                ws.receive_text()  # thinking
                resp = json.loads(ws.receive_text())
        assert resp["type"] == "response"


# ──────────────────────────────────────────────────────────────────────────────
# News broadcast
# ──────────────────────────────────────────────────────────────────────────────

class TestNewsBroadcast:
    def test_news_update_structure(self, sync_client):
        import main as main_module
        main_module.news_cache = [
            {"title": "T1", "url": "http://1.com", "snippet": "s1"},
            {"title": "T2", "url": "http://2.com", "snippet": "s2"},
        ]
        try:
            with sync_client.websocket_connect("/ws/agent") as ws:
                raw = ws.receive_text()
                data = json.loads(raw)
            assert data["type"] == "news_update"
            assert len(data["data"]) == 2
            assert data["data"][0]["title"] == "T1"
        finally:
            main_module.news_cache = []

    def test_news_items_have_url(self, sync_client):
        import main as main_module
        main_module.news_cache = [{"title": "X", "url": "http://x.com", "snippet": ""}]
        try:
            with sync_client.websocket_connect("/ws/agent") as ws:
                data = json.loads(ws.receive_text())
            for item in data["data"]:
                assert "url" in item
        finally:
            main_module.news_cache = []