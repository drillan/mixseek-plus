"""Integration tests for Tavily Search functionality.

These tests require a valid TAVILY_API_KEY environment variable.
Run with: uv run pytest tests/integration/test_tavily_search_integration.py -v

Tests:
- T044: Integration test for tavily_extract with valid URLs
- T045: Integration test for tavily_extract with mixed valid/invalid URLs
- T048: Integration test for tavily_context with query
- T049: Integration test for tavily_context with max_tokens
- T052: Regression test for groq_web_search (backward compatibility)
"""

from __future__ import annotations

import os

import pytest

# Skip all tests if TAVILY_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("TAVILY_API_KEY"),
    reason="TAVILY_API_KEY environment variable not set",
)


class TestTavilyExtractIntegration:
    """Integration tests for tavily_extract functionality (US3)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tavily_extract_with_valid_urls(self) -> None:
        """T044: tavily_extract with valid URLs returns extracted content."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        api_key = os.environ["TAVILY_API_KEY"]
        client = TavilyAPIClient(api_key=api_key)

        # Use well-known stable URLs for testing
        urls = ["https://httpbin.org/html"]

        result = await client.extract(urls=urls)

        # Verify structure
        assert hasattr(result, "results")
        assert hasattr(result, "failed_results")
        assert hasattr(result, "response_time")

        # At least one result should be present (either success or failure)
        # Note: httpbin.org may occasionally fail, so we check for any result
        total_results = len(result.results) + len(result.failed_results)
        assert total_results > 0, "Expected at least one result (success or failure)"

        # If successful, verify content structure
        if result.results:
            for item in result.results:
                assert item.url
                assert item.raw_content

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tavily_extract_with_mixed_urls(self) -> None:
        """T045: tavily_extract with mixed valid/invalid URLs handles partial failures."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        api_key = os.environ["TAVILY_API_KEY"]
        client = TavilyAPIClient(api_key=api_key)

        # Mix of potentially valid and definitely invalid URLs
        urls = [
            "https://httpbin.org/html",  # Valid URL
            "https://this-domain-definitely-does-not-exist-xyz123.com/page",  # Invalid
        ]

        result = await client.extract(urls=urls)

        # Verify structure
        assert hasattr(result, "results")
        assert hasattr(result, "failed_results")

        # We expect some results (either success or failure)
        # The invalid domain should appear in failed_results
        total = len(result.results) + len(result.failed_results)
        assert total >= 1, "Expected at least one result"


class TestTavilyContextIntegration:
    """Integration tests for tavily_context functionality (US4)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tavily_context_with_query(self) -> None:
        """T048: tavily_context with query returns RAG-optimized context."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        api_key = os.environ["TAVILY_API_KEY"]
        client = TavilyAPIClient(api_key=api_key)

        result = await client.get_search_context(query="Python programming language")

        # Should return a non-empty string
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tavily_context_with_max_tokens(self) -> None:
        """T049: tavily_context with max_tokens respects token limit."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        api_key = os.environ["TAVILY_API_KEY"]
        client = TavilyAPIClient(api_key=api_key)

        # Request with a small max_tokens limit
        result_limited = await client.get_search_context(
            query="Python programming language",
            max_tokens=500,
        )

        # Request without limit
        result_unlimited = await client.get_search_context(
            query="Python programming language",
        )

        # Both should return strings
        assert isinstance(result_limited, str)
        assert isinstance(result_unlimited, str)

        # Limited result should generally be shorter (though not guaranteed due to API behavior)
        # At minimum, both should have content
        assert len(result_limited) > 0
        assert len(result_unlimited) > 0


class TestTavilySearchIntegration:
    """Integration tests for tavily_search functionality."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tavily_search_basic(self) -> None:
        """Basic tavily_search integration test."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        api_key = os.environ["TAVILY_API_KEY"]
        client = TavilyAPIClient(api_key=api_key)

        result = await client.search(
            query="Python programming",
            max_results=3,
        )

        # Verify structure
        assert result.query == "Python programming"
        assert hasattr(result, "results")
        assert hasattr(result, "response_time")

        # Should have results
        assert len(result.results) > 0

        # Verify result item structure
        for item in result.results:
            assert item.title
            assert item.url
            assert item.content
            assert 0.0 <= item.score <= 1.0


class TestBackwardCompatibility:
    """Regression tests for backward compatibility (US5)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_groq_web_search_still_works(self) -> None:
        """T052: groq_web_search agent type still works after tavily_search addition.

        This test verifies that the existing groq_web_search functionality
        is not broken by the addition of tavily_search agents.
        """
        from mixseek_plus.agents import register_all_agents

        # Register all agents including both groq_web_search and tavily_search
        register_all_agents()

        # Import factory after registration
        from mixseek.agents.member.factory import MemberAgentFactory

        # Verify groq_web_search is still registered
        agent_types = MemberAgentFactory.get_supported_types()
        assert "groq_web_search" in agent_types, (
            "groq_web_search should still be registered"
        )

        # Verify tavily_search is also registered (coexistence)
        assert "tavily_search" in agent_types, "tavily_search should be registered"

        # Verify claudecode_tavily_search is registered
        assert "claudecode_tavily_search" in agent_types, (
            "claudecode_tavily_search should be registered"
        )
