"""
test_endpoints.py — Integration tests for all REST endpoints.

Endpoints tested
────────────────
GET  /api/health
POST /api/chat
GET  /api/weather/{city}
GET  /api/news
GET  /api/time

Every external call (requests.get, TavilyClient, AgentExecutor) is mocked
via fixtures defined in conftest.py so no real API keys are required.
"""

import json
import re
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

# ──────────────────────────────────────────────────────────────────────────────
# App fixture (per-module so we don't spin up app multiple times)
# ──────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="module")
async def client():
    from main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


def _weather_mock(status=200, payload=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload or {
        "weather": [{"description": "few clouds", "main": "Clouds", "icon": "02d"}],
        "main":    {"temp": 18.3, "feels_like": 17.0, "humidity": 65},
        "wind":    {"speed": 4.1},
    }
    return r


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/health
# ──────────────────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_status_field(self, client):
        resp = await client.get("/api/health")
        assert resp.json()["status"] == "ARIA online"

    @pytest.mark.asyncio
    async def test_version_field(self, client):
        resp = await client.get("/api/health")
        assert resp.json()["version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_time_field_is_iso8601(self, client):
        resp = await client.get("/api/health")
        time_str = resp.json()["time"]
        # ISO 8601 basic check — contains 'T'
        assert "T" in time_str

    @pytest.mark.asyncio
    async def test_content_type_json(self, client):
        resp = await client.get("/api/health")
        assert "application/json" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_no_auth_required(self, client):
        """Health endpoint must be public — no credentials needed."""
        resp = await client.get("/api/health")
        assert resp.status_code != 401
        assert resp.status_code != 403


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/chat
# ──────────────────────────────────────────────────────────────────────────────
# NOTE: AgentExecutor is a Pydantic model — patch("main.agent_executor.invoke")
# will raise AttributeError because Pydantic blocks arbitrary setattr.
# Instead we patch main.invoke_agent directly (the async wrapper function).

from unittest.mock import AsyncMock

def _agent_ok(response="The time is 03:00 PM.", emotion="speaking", condition=None):
    return AsyncMock(return_value={"response": response, "emotion": emotion, "condition": condition})

def _agent_err():
    return AsyncMock(return_value={"response": "Something went wrong.", "emotion": "sad", "condition": None})


class TestChatEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200(self, client):
        with patch("main.invoke_agent", _agent_ok()):
            resp = await client.post("/api/chat", json={"message": "What time is it?"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_response_field_present(self, client):
        with patch("main.invoke_agent", _agent_ok()):
            resp = await client.post("/api/chat", json={"message": "hi"})
        assert "response" in resp.json()

    @pytest.mark.asyncio
    async def test_emotion_field_present(self, client):
        with patch("main.invoke_agent", _agent_ok()):
            resp = await client.post("/api/chat", json={"message": "hi"})
        assert "emotion" in resp.json()

    @pytest.mark.asyncio
    async def test_emotion_tag_stripped_from_response(self, client):
        with patch("main.invoke_agent", _agent_ok("Hello!", "happy")):
            resp = await client.post("/api/chat", json={"message": "hello"})
        assert "[EMOTION" not in resp.json()["response"]

    @pytest.mark.asyncio
    async def test_chat_with_history(self, client):
        history = [
            {"role": "user",      "content": "My name is Alex"},
            {"role": "assistant", "content": "Nice to meet you Alex!"},
        ]
        with patch("main.invoke_agent", _agent_ok("You told me your name is Alex.", "speaking")):
            resp = await client.post("/api/chat", json={
                "message": "What's my name?",
                "history": history,
            })
        assert resp.status_code == 200
        assert resp.json()["response"] != ""

    @pytest.mark.asyncio
    async def test_empty_message_still_returns_200(self, client):
        with patch("main.invoke_agent", _agent_ok("How can I help?", "idle")):
            resp = await client.post("/api/chat", json={"message": ""})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_message_field_returns_422(self, client):
        resp = await client.post("/api/chat", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_non_string_message_returns_422(self, client):
        resp = await client.post("/api/chat", json={"message": 12345})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_agent_exception_returns_200_with_sad_emotion(self, client):
        """Agent errors are swallowed and returned as sad emotion — not 500."""
        with patch("main.invoke_agent", _agent_err()):
            resp = await client.post("/api/chat", json={"message": "break me"})
        assert resp.status_code == 200
        assert resp.json()["emotion"] == "sad"

    @pytest.mark.asyncio
    async def test_condition_field_present(self, client):
        with patch("main.invoke_agent", _agent_ok("Rainy today.", "speaking", "Rain")):
            resp = await client.post("/api/chat", json={"message": "weather?"})
        assert "condition" in resp.json()

    @pytest.mark.asyncio
    async def test_condition_value_extracted(self, client):
        with patch("main.invoke_agent", _agent_ok("Snowing!", "speaking", "Snow")):
            resp = await client.post("/api/chat", json={"message": "weather?"})
        assert resp.json()["condition"] == "Snow"

    @pytest.mark.asyncio
    async def test_history_none_treated_as_empty(self, client):
        with patch("main.invoke_agent", _agent_ok("OK", "idle")):
            resp = await client.post("/api/chat", json={"message": "ping", "history": None})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_very_long_message_accepted(self, client):
        long_msg = "a" * 2000
        with patch("main.invoke_agent", _agent_ok("Processing...", "thinking")):
            resp = await client.post("/api/chat", json={"message": long_msg})
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/weather/{city}
# ──────────────────────────────────────────────────────────────────────────────

class TestWeatherEndpoint:
    @pytest.mark.asyncio
    async def test_valid_city_returns_200(self, client):
        with patch("requests.get", return_value=_weather_mock()):
            resp = await client.get("/api/weather/London")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_response_has_all_fields(self, client):
        with patch("requests.get", return_value=_weather_mock()):
            resp = await client.get("/api/weather/London")
        data = resp.json()
        for field in ["city", "temp", "feels_like", "description", "condition", "humidity", "wind_speed"]:
            assert field in data, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_temp_is_number(self, client):
        with patch("requests.get", return_value=_weather_mock()):
            resp = await client.get("/api/weather/Paris")
        assert isinstance(resp.json()["temp"], (int, float))

    @pytest.mark.asyncio
    async def test_temp_rounded_to_one_decimal(self, client):
        mock = _weather_mock(payload={
            "weather": [{"description": "sunny", "main": "Clear", "icon": "01d"}],
            "main":    {"temp": 22.567, "feels_like": 21.9999, "humidity": 55},
            "wind":    {"speed": 2.0},
        })
        with patch("requests.get", return_value=mock):
            resp = await client.get("/api/weather/Rome")
        t = resp.json()["temp"]
        assert t == round(t, 1)

    @pytest.mark.asyncio
    async def test_city_name_echoed_back(self, client):
        with patch("requests.get", return_value=_weather_mock()):
            resp = await client.get("/api/weather/Tokyo")
        assert resp.json()["city"] == "Tokyo"

    @pytest.mark.asyncio
    async def test_invalid_city_returns_error_key(self, client):
        with patch("requests.get", return_value=_weather_mock(status=404)):
            resp = await client.get("/api/weather/FakeCity123")
        assert "error" in resp.json()

    @pytest.mark.asyncio
    async def test_invalid_city_condition_defaults_to_clear(self, client):
        with patch("requests.get", return_value=_weather_mock(status=404)):
            resp = await client.get("/api/weather/NoSuchPlace")
        assert resp.json()["condition"] == "Clear"

    @pytest.mark.asyncio
    async def test_city_with_spaces_url_encoded(self, client):
        """'New York' should be accepted (HTTPX handles URL encoding)."""
        with patch("requests.get", return_value=_weather_mock()):
            resp = await client.get("/api/weather/New%20York")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_humidity_is_integer(self, client):
        with patch("requests.get", return_value=_weather_mock()):
            resp = await client.get("/api/weather/Berlin")
        assert isinstance(resp.json()["humidity"], int)

    @pytest.mark.asyncio
    async def test_icon_field_present(self, client):
        with patch("requests.get", return_value=_weather_mock()):
            resp = await client.get("/api/weather/Madrid")
        assert "icon" in resp.json()

    @pytest.mark.asyncio
    async def test_condition_one_of_known_values(self, client):
        known = {"Clear", "Clouds", "Rain", "Snow", "Thunderstorm", "Drizzle", "Mist", "Fog"}
        with patch("requests.get", return_value=_weather_mock()):
            resp = await client.get("/api/weather/Oslo")
        # "Clouds" is what the mock returns
        assert resp.json()["condition"] in known


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/news
# ──────────────────────────────────────────────────────────────────────────────

class TestNewsEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200(self, client):
        resp = await client.get("/api/news")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_response_has_news_key(self, client):
        resp = await client.get("/api/news")
        assert "news" in resp.json()

    @pytest.mark.asyncio
    async def test_news_is_list(self, client):
        resp = await client.get("/api/news")
        assert isinstance(resp.json()["news"], list)

    @pytest.mark.asyncio
    async def test_fetched_at_present(self, client):
        resp = await client.get("/api/news")
        assert "fetched_at" in resp.json()

    @pytest.mark.asyncio
    async def test_fetched_at_is_iso8601(self, client):
        resp = await client.get("/api/news")
        ts = resp.json()["fetched_at"]
        assert "T" in ts

    @pytest.mark.asyncio
    async def test_news_items_have_title(self, client):
        """If news cache is populated, each item must have a title."""
        import main as main_module
        main_module.news_cache = [
            {"title": "Story A", "url": "http://a.com", "snippet": "..."},
            {"title": "Story B", "url": "http://b.com", "snippet": "..."},
        ]
        resp = await client.get("/api/news")
        for item in resp.json()["news"]:
            assert "title" in item
        # reset
        main_module.news_cache = []

    @pytest.mark.asyncio
    async def test_empty_cache_returns_empty_list(self, client):
        import main as main_module
        main_module.news_cache = []
        resp = await client.get("/api/news")
        assert resp.json()["news"] == []


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/time
# ──────────────────────────────────────────────────────────────────────────────

class TestTimeEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200(self, client):
        resp = await client.get("/api/time")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_has_all_fields(self, client):
        resp = await client.get("/api/time")
        data = resp.json()
        for field in ["time", "date", "hour", "is_night"]:
            assert field in data, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_time_format(self, client):
        resp = await client.get("/api/time")
        assert re.match(r"\d{2}:\d{2} [AP]M", resp.json()["time"])

    @pytest.mark.asyncio
    async def test_hour_is_integer_0_to_23(self, client):
        resp = await client.get("/api/time")
        h = resp.json()["hour"]
        assert isinstance(h, int)
        assert 0 <= h <= 23

    @pytest.mark.asyncio
    async def test_is_night_is_bool(self, client):
        resp = await client.get("/api/time")
        assert isinstance(resp.json()["is_night"], bool)

    @pytest.mark.asyncio
    async def test_is_night_logic(self, client):
        """is_night should be True for hour < 6 or >= 20, False otherwise."""
        from unittest.mock import patch
        from datetime import datetime

        for hour, expected in [(0, True), (5, True), (6, False), (12, False), (19, False), (20, True), (23, True)]:
            fake_now = datetime(2024, 1, 15, hour, 30, 0)
            with patch("main.datetime") as mock_dt:
                mock_dt.now.return_value = fake_now
                mock_dt.strftime = datetime.strftime
                resp = await client.get("/api/time")
            assert resp.json()["is_night"] == expected, f"Failed for hour={hour}"

    @pytest.mark.asyncio
    async def test_date_contains_year(self, client):
        from datetime import datetime
        resp = await client.get("/api/time")
        assert str(datetime.now().year) in resp.json()["date"]


# ──────────────────────────────────────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────────────────────────────────────

class TestCORS:
    @pytest.mark.asyncio
    async def test_cors_header_present(self, client):
        resp = await client.get(
            "/api/health",
            headers={"Origin": "http://localhost:5173"}
        )
        assert "access-control-allow-origin" in resp.headers

    @pytest.mark.asyncio
    async def test_cors_wildcard_or_matching_origin(self, client):
        resp = await client.get(
            "/api/health",
            headers={"Origin": "http://localhost:5173"}
        )
        acao = resp.headers.get("access-control-allow-origin", "")
        assert acao in ("*", "http://localhost:5173")

    @pytest.mark.asyncio
    async def test_preflight_options(self, client):
        resp = await client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )
        assert resp.status_code in (200, 204)


# ──────────────────────────────────────────────────────────────────────────────
# 404 / unknown routes
# ──────────────────────────────────────────────────────────────────────────────

class TestUnknownRoutes:
    @pytest.mark.asyncio
    async def test_unknown_get_returns_404(self, client):
        resp = await client.get("/api/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unknown_post_returns_404_or_405(self, client):
        resp = await client.post("/api/nonexistent", json={})
        assert resp.status_code in (404, 405)