"""
conftest.py — Shared fixtures and mocks for ARIA backend tests.

All external I/O is patched here so tests run fully offline:
  • requests.get     → weather API stub
  • TavilyClient     → news search stub
  • AgentExecutor    → LLM stub (no Mistral calls)
  • ChatMistralAI    → neutralised at import time via env vars
"""

import json
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

# ── Patch env vars BEFORE the app module is imported ─────────────────────────
os.environ.setdefault("OPENWEATHER_API_KEY", "test_owm_key")
os.environ.setdefault("TAVILY_API_KEY",      "test_tavily_key")
os.environ.setdefault("MISTRAL_API_KEY",     "test_mistral_key")

# ──────────────────────────────────────────────────────────────────────────────
# Fixture helpers
# ──────────────────────────────────────────────────────────────────────────────

MOCK_WEATHER_PAYLOAD = {
    "weather": [{"description": "clear sky", "main": "Clear", "icon": "01d"}],
    "main": {
        "temp": 22.5,
        "feels_like": 21.3,
        "humidity": 58,
    },
    "wind": {"speed": 3.2},
}

MOCK_NEWS_RESULTS = {
    "results": [
        {"title": "AI breaks new ground",  "url": "https://news.example.com/1", "content": "Researchers announce breakthrough..."},
        {"title": "Climate summit opens",   "url": "https://news.example.com/2", "content": "World leaders gather in Geneva..."},
        {"title": "Markets hit record high","url": "https://news.example.com/3", "content": "Stocks surged on positive data..."},
    ]
}

MOCK_AGENT_RESPONSE = "[EMOTION:speaking] The weather in London is clear sky with 22.5°C."


def _make_requests_response(status: int = 200, payload: dict | None = None) -> MagicMock:
    """Build a mock requests.Response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.json.return_value = payload or MOCK_WEATHER_PAYLOAD
    return mock_resp


# ──────────────────────────────────────────────────────────────────────────────
# Pytest-asyncio mode
# ──────────────────────────────────────────────────────────────────────────────

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration (may call real APIs)")


# ──────────────────────────────────────────────────────────────────────────────
# App fixture — creates a fresh TestClient per test session
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def mock_llm():
    """Patch ChatMistralAI so it never dials out."""
    with patch("langchain_mistralai.ChatMistralAI") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield instance


@pytest.fixture(scope="session")
def mock_agent_executor():
    """Patch AgentExecutor.invoke to return a canned LLM response."""
    with patch("langchain.agents.AgentExecutor.invoke") as mock_invoke:
        mock_invoke.return_value = {"output": MOCK_AGENT_RESPONSE}
        yield mock_invoke


@pytest_asyncio.fixture(scope="session")
async def app_client(mock_agent_executor):
    """
    Async HTTPX client wired to the ARIA FastAPI app.
    AgentExecutor is stubbed so no LLM key is consumed.
    """
    # Import app AFTER env vars and patches are in place
    from main import app  # noqa: PLC0415

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture()
def weather_ok():
    """Patch requests.get to return a valid weather response."""
    with patch("requests.get", return_value=_make_requests_response(200, MOCK_WEATHER_PAYLOAD)) as m:
        yield m


@pytest.fixture()
def weather_not_found():
    """Patch requests.get to return a 404 for unknown city."""
    with patch("requests.get", return_value=_make_requests_response(404, {})) as m:
        yield m


@pytest.fixture()
def weather_timeout():
    """Patch requests.get to raise a Timeout."""
    import requests as req_mod
    with patch("requests.get", side_effect=req_mod.exceptions.Timeout) as m:
        yield m


@pytest.fixture()
def tavily_ok():
    """Patch TavilyClient.search to return mock news."""
    with patch("tavily.TavilyClient.search", return_value=MOCK_NEWS_RESULTS) as m:
        yield m


@pytest.fixture()
def tavily_empty():
    """Patch TavilyClient.search to return no results."""
    with patch("tavily.TavilyClient.search", return_value={"results": []}) as m:
        yield m


@pytest.fixture()
def tavily_error():
    """Patch TavilyClient.search to raise an exception."""
    with patch("tavily.TavilyClient.search", side_effect=RuntimeError("Tavily quota exceeded")) as m:
        yield m
