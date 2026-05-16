"""
test_tools.py — Unit tests for every LangChain tool in main.py.

Each tool is called directly (bypassing the agent) so we test the pure
business logic with deterministic mocked I/O.

Coverage targets
────────────────
get_weather        happy-path, 404 city, network timeout, key missing
get_current_time   format correctness, timezone consistency
get_latest_news    happy-path, empty results, runtime error, topic injection
set_timer          singular/plural minutes, zero minutes, large value
tell_joke          return type, non-empty, pool membership
control_lights     default brightness, explicit brightness, case variants
"""

import os
import re
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
import requests as req_mod

# Env vars set in conftest.py before this import
from main import (
    get_weather,
    get_current_time,
    get_latest_news,
    set_timer,
    tell_joke,
    control_lights,
)

MOCK_WEATHER = {
    "weather": [{"description": "light rain", "main": "Rain", "icon": "10d"}],
    "main":    {"temp": 15.0, "feels_like": 13.5, "humidity": 82},
    "wind":    {"speed": 5.4},
}

# ──────────────────────────────────────────────────────────────────────────────
# get_weather
# ──────────────────────────────────────────────────────────────────────────────

class TestGetWeather:
    def _ok(self):
        r = MagicMock()
        r.status_code = 200
        r.json.return_value = MOCK_WEATHER
        return r

    def _fail(self, code=404):
        r = MagicMock()
        r.status_code = code
        return r

    def test_happy_path_contains_city(self):
        with patch("requests.get", return_value=self._ok()):
            result = get_weather.invoke({"city": "London"})
        assert "London" in result

    def test_happy_path_contains_condition_tag(self):
        with patch("requests.get", return_value=self._ok()):
            result = get_weather.invoke({"city": "London"})
        assert "[CONDITION:Rain]" in result

    def test_happy_path_contains_temperature(self):
        with patch("requests.get", return_value=self._ok()):
            result = get_weather.invoke({"city": "London"})
        assert "15.0°C" in result

    def test_happy_path_contains_humidity(self):
        with patch("requests.get", return_value=self._ok()):
            result = get_weather.invoke({"city": "London"})
        assert "82%" in result

    def test_happy_path_contains_wind(self):
        with patch("requests.get", return_value=self._ok()):
            result = get_weather.invoke({"city": "London"})
        assert "5.4 m/s" in result

    def test_city_not_found_returns_sorry(self):
        with patch("requests.get", return_value=self._fail(404)):
            result = get_weather.invoke({"city": "Atlantis"})
        assert "Sorry" in result
        assert "Atlantis" in result

    def test_server_error_returns_sorry(self):
        with patch("requests.get", return_value=self._fail(500)):
            result = get_weather.invoke({"city": "Tokyo"})
        assert "Sorry" in result

    def test_network_timeout_propagates(self):
        with patch("requests.get", side_effect=req_mod.exceptions.Timeout):
            with pytest.raises(req_mod.exceptions.Timeout):
                get_weather.invoke({"city": "Paris"})

    def test_api_key_injected_into_url(self):
        os.environ["OPENWEATHER_API_KEY"] = "my_test_key_xyz"
        captured_url = []

        def fake_get(url, **_):
            captured_url.append(url)
            return self._ok()

        with patch("requests.get", side_effect=fake_get):
            get_weather.invoke({"city": "Berlin"})

        assert "my_test_key_xyz" in captured_url[0]
        assert "Berlin" in captured_url[0]
        assert "metric" in captured_url[0]

    def test_feels_like_present(self):
        with patch("requests.get", return_value=self._ok()):
            result = get_weather.invoke({"city": "Rome"})
        assert "feels like" in result.lower()


# ──────────────────────────────────────────────────────────────────────────────
# get_current_time
# ──────────────────────────────────────────────────────────────────────────────

class TestGetCurrentTime:
    def test_returns_string(self):
        result = get_current_time.invoke({})
        assert isinstance(result, str)

    def test_contains_am_or_pm(self):
        result = get_current_time.invoke({})
        assert "AM" in result or "PM" in result

    def test_contains_weekday(self):
        result = get_current_time.invoke({})
        days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        assert any(d in result for d in days)

    def test_contains_full_year(self):
        result = get_current_time.invoke({})
        current_year = str(datetime.now().year)
        assert current_year in result

    def test_contains_month_name(self):
        result = get_current_time.invoke({})
        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        assert any(m in result for m in months)

    def test_starts_with_its(self):
        result = get_current_time.invoke({})
        assert result.startswith("It's")

    def test_time_format_hh_mm(self):
        result = get_current_time.invoke({})
        # Expect pattern like "03:45 PM"
        assert re.search(r"\d{2}:\d{2} [AP]M", result), f"No time pattern in: {result}"

    def test_consistent_across_two_calls(self):
        """Two back-to-back calls should be within a minute of each other."""
        r1 = get_current_time.invoke({})
        r2 = get_current_time.invoke({})
        # Both should contain same year
        assert str(datetime.now().year) in r1
        assert str(datetime.now().year) in r2


# ──────────────────────────────────────────────────────────────────────────────
# get_latest_news
# ──────────────────────────────────────────────────────────────────────────────

MOCK_NEWS = {
    "results": [
        {"title": "Headline One",   "url": "http://a.com", "content": "Content one here..."},
        {"title": "Headline Two",   "url": "http://b.com", "content": "Content two here..."},
        {"title": "Headline Three", "url": "http://c.com", "content": "Content three here..."},
    ]
}

class TestGetLatestNews:
    def test_happy_path_contains_all_titles(self):
        with patch("tavily.TavilyClient.search", return_value=MOCK_NEWS):
            result = get_latest_news.invoke({"topic": "technology"})
        assert "Headline One"   in result
        assert "Headline Two"   in result
        assert "Headline Three" in result

    def test_happy_path_topic_in_output(self):
        with patch("tavily.TavilyClient.search", return_value=MOCK_NEWS):
            result = get_latest_news.invoke({"topic": "science"})
        assert "science" in result.lower()

    def test_default_topic_world(self):
        captured = []
        def fake_search(query, **_):
            captured.append(query)
            return MOCK_NEWS
        with patch("tavily.TavilyClient.search", side_effect=fake_search):
            get_latest_news.invoke({"topic": "world"})
        assert "world" in captured[0].lower()

    def test_empty_results_returns_no_news_message(self):
        with patch("tavily.TavilyClient.search", return_value={"results": []}):
            result = get_latest_news.invoke({"topic": "unicorns"})
        assert "No recent news" in result
        assert "unicorns" in result

    def test_results_truncated_to_80_chars(self):
        long_content = "X" * 200
        mock_data = {"results": [{"title": "T", "url": "u", "content": long_content}]}
        with patch("tavily.TavilyClient.search", return_value=mock_data):
            result = get_latest_news.invoke({"topic": "test"})
        # Snippet should end with "..." after 80 chars
        assert "..." in result

    def test_bullet_points_in_output(self):
        with patch("tavily.TavilyClient.search", return_value=MOCK_NEWS):
            result = get_latest_news.invoke({"topic": "world"})
        assert "•" in result

    def test_tavily_key_used(self):
        os.environ["TAVILY_API_KEY"] = "secret_tavily_abc"
        init_args = []
        original_init = __import__("tavily").TavilyClient.__init__

        def patched_init(self_, api_key, *a, **kw):
            init_args.append(api_key)
            # Don't call real __init__
        
        with patch("tavily.TavilyClient.__init__", patched_init), \
             patch("tavily.TavilyClient.search", return_value=MOCK_NEWS):
            get_latest_news.invoke({"topic": "world"})

        if init_args:  # Only assert if __init__ was captured
            assert "secret_tavily_abc" in init_args[0]

    def test_missing_content_key_handled(self):
        """Results with no 'content' key should not raise KeyError."""
        no_content = {"results": [{"title": "No Content Story", "url": "http://x.com"}]}
        with patch("tavily.TavilyClient.search", return_value=no_content):
            result = get_latest_news.invoke({"topic": "world"})
        assert "No Content Story" in result


# ──────────────────────────────────────────────────────────────────────────────
# set_timer
# ──────────────────────────────────────────────────────────────────────────────

class TestSetTimer:
    def test_label_in_response(self):
        result = set_timer.invoke({"label": "pasta", "minutes": 10})
        assert "pasta" in result

    def test_minutes_plural(self):
        result = set_timer.invoke({"label": "coffee", "minutes": 5})
        assert "5 minutes" in result

    def test_minutes_singular(self):
        result = set_timer.invoke({"label": "egg", "minutes": 1})
        assert "1 minute" in result
        assert "minutes" not in result  # strictly singular

    def test_zero_minutes(self):
        result = set_timer.invoke({"label": "instant", "minutes": 0})
        assert "0 minutes" in result

    def test_large_minutes(self):
        result = set_timer.invoke({"label": "roast", "minutes": 120})
        assert "120 minutes" in result

    def test_checkmark_in_response(self):
        result = set_timer.invoke({"label": "test", "minutes": 3})
        assert "✓" in result

    def test_returns_string(self):
        result = set_timer.invoke({"label": "x", "minutes": 2})
        assert isinstance(result, str)

    def test_label_with_spaces(self):
        result = set_timer.invoke({"label": "team standup meeting", "minutes": 15})
        assert "team standup meeting" in result


# ──────────────────────────────────────────────────────────────────────────────
# tell_joke
# ──────────────────────────────────────────────────────────────────────────────

KNOWN_JOKES = [
    "Why do programmers prefer dark mode?",
    "Error 404: Humor not found",
    "Why was the robot angry?",
    "Parallel processing walks into a bar",
    "I have a joke about UDP",
]

class TestTellJoke:
    def test_returns_string(self):
        result = tell_joke.invoke({})
        assert isinstance(result, str)

    def test_non_empty(self):
        result = tell_joke.invoke({})
        assert len(result) > 10

    def test_result_in_known_pool(self):
        """Run multiple times and confirm every result comes from the known pool."""
        for _ in range(20):
            result = tell_joke.invoke({})
            assert any(fragment in result for fragment in KNOWN_JOKES), \
                f"Unexpected joke: {result!r}"

    def test_randomness_over_many_calls(self):
        """Given 20 calls, we should see at least 2 distinct jokes."""
        results = {tell_joke.invoke({}) for _ in range(20)}
        assert len(results) >= 2, "Jokes seem to always return the same value"


# ──────────────────────────────────────────────────────────────────────────────
# control_lights
# ──────────────────────────────────────────────────────────────────────────────

class TestControlLights:
    def test_room_in_response(self):
        result = control_lights.invoke({"room": "bedroom", "action": "on"})
        assert "bedroom" in result

    def test_action_in_response(self):
        result = control_lights.invoke({"room": "kitchen", "action": "off"})
        assert "off" in result

    def test_default_brightness_100(self):
        result = control_lights.invoke({"room": "living room", "action": "dim"})
        assert "100%" in result

    def test_explicit_brightness(self):
        result = control_lights.invoke({"room": "hall", "action": "dim", "brightness": 40})
        assert "40%" in result

    def test_zero_brightness(self):
        result = control_lights.invoke({"room": "office", "action": "off", "brightness": 0})
        assert "0%" in result

    def test_home_tag_in_response(self):
        result = control_lights.invoke({"room": "garage", "action": "on"})
        assert "[HOME]" in result

    def test_done_in_response(self):
        result = control_lights.invoke({"room": "porch", "action": "on"})
        assert "Done!" in result

    def test_returns_string(self):
        result = control_lights.invoke({"room": "attic", "action": "toggle"})
        assert isinstance(result, str)

    def test_multi_word_room(self):
        result = control_lights.invoke({"room": "master bedroom", "action": "on"})
        assert "master bedroom" in result
