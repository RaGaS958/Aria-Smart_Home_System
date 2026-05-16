"""
test_scheduler.py — Tests for the news_scheduler background task.

The scheduler runs in an asyncio loop; we call it directly (one cycle)
by patching asyncio.sleep to break after the first iteration.

Covers
──────
• News cache populated after one cycle
• Correct Tavily query used
• Results trimmed to 120-char snippets
• Dead WebSocket connections pruned from pool
• Exceptions inside the loop do NOT crash the scheduler
• Broadcast payload structure matches expected schema
"""

import json
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

MOCK_RESULTS = {
    "results": [
        {"title": "Tech surge", "url": "http://tech.com", "content": "A" * 200},
        {"title": "Sports win",  "url": "http://sport.com", "content": "B" * 50},
        {"title": "Weather big", "url": "http://weather.com", "content": "C" * 5},
    ]
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

async def _run_one_cycle():
    """
    Run exactly one iteration of news_scheduler by making asyncio.sleep
    raise StopAsyncIteration after the first call to break the while-loop.
    """
    import main as main_module

    sleep_call_count = 0

    async def stop_after_first(_):
        nonlocal sleep_call_count
        sleep_call_count += 1
        if sleep_call_count >= 1:
            raise StopAsyncIteration

    with patch("asyncio.sleep", side_effect=stop_after_first):
        try:
            await main_module.news_scheduler()
        except StopAsyncIteration:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestNewsScheduler:
    @pytest.mark.asyncio
    async def test_cache_populated_after_one_cycle(self):
        import main as main_module
        main_module.news_cache = []

        with patch("tavily.TavilyClient.search", return_value=MOCK_RESULTS), \
             patch("asyncio.sleep", side_effect=[None, StopAsyncIteration]):
            try:
                await main_module.news_scheduler()
            except StopAsyncIteration:
                pass

        assert len(main_module.news_cache) == 3

    @pytest.mark.asyncio
    async def test_cache_items_have_title(self):
        import main as main_module
        main_module.news_cache = []

        with patch("tavily.TavilyClient.search", return_value=MOCK_RESULTS), \
             patch("asyncio.sleep", side_effect=[None, StopAsyncIteration]):
            try:
                await main_module.news_scheduler()
            except StopAsyncIteration:
                pass

        for item in main_module.news_cache:
            assert "title" in item

    @pytest.mark.asyncio
    async def test_cache_items_have_url(self):
        import main as main_module

        with patch("tavily.TavilyClient.search", return_value=MOCK_RESULTS), \
             patch("asyncio.sleep", side_effect=[None, StopAsyncIteration]):
            try:
                await main_module.news_scheduler()
            except StopAsyncIteration:
                pass

        for item in main_module.news_cache:
            assert "url" in item

    @pytest.mark.asyncio
    async def test_snippet_truncated_to_120_chars(self):
        """Long content must be trimmed to 120 characters."""
        import main as main_module

        with patch("tavily.TavilyClient.search", return_value=MOCK_RESULTS), \
             patch("asyncio.sleep", side_effect=[None, StopAsyncIteration]):
            try:
                await main_module.news_scheduler()
            except StopAsyncIteration:
                pass

        for item in main_module.news_cache:
            assert len(item["snippet"]) <= 120, \
                f"Snippet too long: {len(item['snippet'])} chars"

    @pytest.mark.asyncio
    async def test_correct_tavily_query_used(self):
        import main as main_module
        captured = []

        def fake_search(query, **_):
            captured.append(query)
            return MOCK_RESULTS

        with patch("tavily.TavilyClient.search", side_effect=fake_search), \
             patch("asyncio.sleep", side_effect=[None, StopAsyncIteration]):
            try:
                await main_module.news_scheduler()
            except StopAsyncIteration:
                pass

        assert len(captured) >= 1
        assert "trending" in captured[0].lower() or "news" in captured[0].lower()

    @pytest.mark.asyncio
    async def test_sleep_interval_is_600_seconds(self):
        """Scheduler must sleep for 600 s (10 min) between cycles."""
        import main as main_module
        sleep_durations = []

        async def capture_sleep(duration):
            sleep_durations.append(duration)
            raise StopAsyncIteration

        with patch("tavily.TavilyClient.search", return_value=MOCK_RESULTS), \
             patch("asyncio.sleep", side_effect=capture_sleep):
            try:
                await main_module.news_scheduler()
            except StopAsyncIteration:
                pass

        assert sleep_durations[0] == 600

    @pytest.mark.asyncio
    async def test_broadcast_payload_structure(self):
        """Each connected WebSocket should receive a proper JSON payload."""
        import main as main_module

        sent_payloads = []
        mock_ws = MagicMock()
        mock_ws.send_text = AsyncMock(side_effect=lambda p: sent_payloads.append(json.loads(p)))
        main_module.ws_connections = [mock_ws]

        try:
            with patch("tavily.TavilyClient.search", return_value=MOCK_RESULTS), \
                 patch("asyncio.sleep", side_effect=[None, StopAsyncIteration]):
                try:
                    await main_module.news_scheduler()
                except StopAsyncIteration:
                    pass
        finally:
            main_module.ws_connections = []

        assert len(sent_payloads) >= 1
        payload = sent_payloads[0]
        assert payload["type"] == "news_update"
        assert isinstance(payload["data"], list)

    @pytest.mark.asyncio
    async def test_dead_ws_removed_from_pool(self):
        """A WebSocket that raises on send_text should be removed from pool."""
        import main as main_module

        dead_ws = MagicMock()
        dead_ws.send_text = AsyncMock(side_effect=RuntimeError("Connection closed"))
        main_module.ws_connections = [dead_ws]

        with patch("tavily.TavilyClient.search", return_value=MOCK_RESULTS), \
             patch("asyncio.sleep", side_effect=[None, StopAsyncIteration]):
            try:
                await main_module.news_scheduler()
            except StopAsyncIteration:
                pass
            finally:
                assert dead_ws not in main_module.ws_connections
                main_module.ws_connections = []

    @pytest.mark.asyncio
    async def test_healthy_ws_kept_in_pool(self):
        """A working WebSocket must NOT be removed from pool."""
        import main as main_module

        ok_ws = MagicMock()
        ok_ws.send_text = AsyncMock()
        main_module.ws_connections = [ok_ws]

        with patch("tavily.TavilyClient.search", return_value=MOCK_RESULTS), \
             patch("asyncio.sleep", side_effect=[None, StopAsyncIteration]):
            try:
                await main_module.news_scheduler()
            except StopAsyncIteration:
                pass
            finally:
                assert ok_ws in main_module.ws_connections
                main_module.ws_connections = []

    @pytest.mark.asyncio
    async def test_tavily_exception_does_not_crash_scheduler(self):
        """A Tavily error should be caught; the loop must continue (next sleep)."""
        import main as main_module
        sleep_calls = []

        async def track_sleep(d):
            sleep_calls.append(d)
            if len(sleep_calls) >= 1:
                raise StopAsyncIteration

        with patch("tavily.TavilyClient.search",
                   side_effect=RuntimeError("API quota exceeded")), \
             patch("asyncio.sleep", side_effect=track_sleep):
            try:
                await main_module.news_scheduler()
            except StopAsyncIteration:
                pass

        # If we reach here, exception was swallowed and sleep was reached
        assert len(sleep_calls) >= 1

    @pytest.mark.asyncio
    async def test_empty_results_clears_cache(self):
        import main as main_module
        main_module.news_cache = [{"title": "old", "url": "", "snippet": ""}]

        with patch("tavily.TavilyClient.search", return_value={"results": []}), \
             patch("asyncio.sleep", side_effect=[None, StopAsyncIteration]):
            try:
                await main_module.news_scheduler()
            except StopAsyncIteration:
                pass

        assert main_module.news_cache == []

    @pytest.mark.asyncio
    async def test_multiple_ws_all_receive_broadcast(self):
        import main as main_module

        ws_list = [MagicMock() for _ in range(4)]
        for ws in ws_list:
            ws.send_text = AsyncMock()
        main_module.ws_connections = ws_list[:]

        # StopAsyncIteration on first sleep → exactly one loop body → one broadcast per ws
        with patch("tavily.TavilyClient.search", return_value=MOCK_RESULTS), \
             patch("asyncio.sleep", side_effect=StopAsyncIteration):
            try:
                await main_module.news_scheduler()
            except StopAsyncIteration:
                pass
            finally:
                main_module.ws_connections = []

        for ws in ws_list:
            ws.send_text.assert_called()          # called at least once
            assert ws.send_text.call_count == 1   # exactly once (one cycle)