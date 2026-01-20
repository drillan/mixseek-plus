"""Unit tests for TavilyToolsRepositoryMixin.

Tests for T014-T017:
- T014: Basic functionality tests (_register_tavily_tools, tool functions)
- T015: tavily_extract handles empty URL list with VALIDATION_ERROR
- T016: tavily_extract handles URL limit (>20) per NFR-004a
- T017: tavily_search returns "検索結果が見つかりませんでした" for 0 results
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic_ai import Agent

if TYPE_CHECKING:
    pass


@dataclass
class MockMemberAgentConfig:
    """Mock MemberAgentConfig for testing."""

    name: str = "test-agent"
    type: str = "tavily_search"
    model: str = "groq:test-model"


class MockLogger:
    """Mock logger for testing."""

    def log_execution_start(self, **kwargs: object) -> str:
        return "test-execution-id"

    def log_execution_complete(self, **kwargs: object) -> None:
        pass

    def log_error(self, **kwargs: object) -> None:
        pass

    def log_tool_invocation(self, **kwargs: object) -> None:
        pass


class TestTavilyToolsRepositoryMixinRegistration:
    """Tests for _register_tavily_tools() registering tools."""

    def test_register_tavily_tools_registers_3_tools(self) -> None:
        """_register_tavily_tools() registers 3 tools."""
        from mixseek_plus.agents.mixins.tavily_tools import (
            TavilyToolsRepositoryMixin,
        )

        # Create a mock agent
        mock_agent = MagicMock(spec=Agent)
        mock_agent.tool = MagicMock(side_effect=lambda fn: fn)

        # Create a minimal class that combines mixin with protocol
        class TestAgent(TavilyToolsRepositoryMixin):
            def __init__(self) -> None:
                self._agent = mock_agent
                self._logger = MockLogger()

            @property
            def logger(self) -> MockLogger:
                return self._logger

            def _get_agent(self) -> Agent[object, str]:
                return self._agent

        agent = TestAgent()
        tools = TavilyToolsRepositoryMixin._register_tavily_tools(agent)  # type: ignore[arg-type]

        # Should register 3 tools
        assert len(tools) == 3
        tool_names = [t.__name__ for t in tools]
        assert "tavily_search" in tool_names
        assert "tavily_extract" in tool_names
        assert "tavily_context" in tool_names


class TestTavilySearchToolOutput:
    """Tests for tavily_search tool output formatting."""

    @pytest.mark.asyncio
    async def test_tavily_search_formats_results_correctly(self) -> None:
        """tavily_search tool returns formatted string per contracts/tavily-tools.md."""
        from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin
        from mixseek_plus.providers.tavily_client import (
            TavilyAPIClient,
            TavilySearchResult,
            TavilySearchResultItem,
        )

        # Create mock search result
        mock_result = TavilySearchResult(
            query="Python latest version",
            results=[
                TavilySearchResultItem(
                    title="Python 3.13 Release",
                    url="https://python.org/downloads/",
                    content="Python 3.13 is the latest version...",
                    score=0.95,
                ),
                TavilySearchResultItem(
                    title="Python News",
                    url="https://python.org/news/",
                    content="Latest Python news and updates...",
                    score=0.89,
                ),
            ],
            response_time=1.5,
        )

        mock_client = AsyncMock(spec=TavilyAPIClient)
        mock_client.search = AsyncMock(return_value=mock_result)

        # Test the format_search_result method
        class TestAgent(TavilyToolsRepositoryMixin):
            def __init__(self) -> None:
                self._logger = MockLogger()

            @property
            def logger(self) -> MockLogger:
                return self._logger

            def _get_agent(self) -> Agent[object, str]:
                return MagicMock()

        agent = TestAgent()
        formatted = agent.format_search_result(mock_result)

        # Check format per contracts/tavily-tools.md section 2.4
        assert "## 検索結果: Python latest version" in formatted
        assert "### 1. Python 3.13 Release" in formatted
        assert "URL: https://python.org/downloads/" in formatted
        assert "スコア: 0.95" in formatted
        assert "Python 3.13 is the latest version..." in formatted
        assert "### 2. Python News" in formatted

    @pytest.mark.asyncio
    async def test_tavily_search_no_results_message(self) -> None:
        """tavily_search returns '検索結果が見つかりませんでした' for 0 results (T017)."""
        from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin
        from mixseek_plus.providers.tavily_client import TavilySearchResult

        # Create mock search result with no results
        mock_result = TavilySearchResult(
            query="nonexistent query xyz123",
            results=[],
            response_time=0.5,
        )

        class TestAgent(TavilyToolsRepositoryMixin):
            def __init__(self) -> None:
                self._logger = MockLogger()

            @property
            def logger(self) -> MockLogger:
                return self._logger

            def _get_agent(self) -> Agent[object, str]:
                return MagicMock()

        agent = TestAgent()
        formatted = agent.format_search_result(mock_result)

        assert "検索結果が見つかりませんでした" in formatted


class TestTavilyExtractToolOutput:
    """Tests for tavily_extract tool output formatting."""

    @pytest.mark.asyncio
    async def test_tavily_extract_formats_results_correctly(self) -> None:
        """tavily_extract tool returns formatted string per contracts/tavily-tools.md."""
        from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin
        from mixseek_plus.providers.tavily_client import (
            TavilyExtractResult,
            TavilyExtractResultItem,
        )

        mock_result = TavilyExtractResult(
            results=[
                TavilyExtractResultItem(
                    url="https://example.com/article1",
                    raw_content="Article 1 content here...",
                ),
                TavilyExtractResultItem(
                    url="https://example.com/article2",
                    raw_content="Article 2 content here...",
                ),
            ],
            failed_results=[],
            response_time=2.0,
        )

        class TestAgent(TavilyToolsRepositoryMixin):
            def __init__(self) -> None:
                self._logger = MockLogger()

            @property
            def logger(self) -> MockLogger:
                return self._logger

            def _get_agent(self) -> Agent[object, str]:
                return MagicMock()

        agent = TestAgent()
        formatted = agent.format_extract_result(mock_result)

        # Check format per contracts/tavily-tools.md section 3.4
        assert "## コンテンツ抽出結果" in formatted
        assert "### URL: https://example.com/article1" in formatted
        assert "Article 1 content here..." in formatted
        assert "### URL: https://example.com/article2" in formatted
        assert "Article 2 content here..." in formatted
        # Should not have failed section when all succeed
        assert "## 失敗したURL" not in formatted

    @pytest.mark.asyncio
    async def test_tavily_extract_formats_failures_correctly(self) -> None:
        """tavily_extract includes failed URLs section when some fail."""
        from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin
        from mixseek_plus.providers.tavily_client import (
            TavilyExtractFailedItem,
            TavilyExtractResult,
            TavilyExtractResultItem,
        )

        mock_result = TavilyExtractResult(
            results=[
                TavilyExtractResultItem(
                    url="https://success.com",
                    raw_content="Success content",
                ),
            ],
            failed_results=[
                TavilyExtractFailedItem(
                    url="https://failed.com",
                    error="Connection timeout",
                ),
            ],
            response_time=3.0,
        )

        class TestAgent(TavilyToolsRepositoryMixin):
            def __init__(self) -> None:
                self._logger = MockLogger()

            @property
            def logger(self) -> MockLogger:
                return self._logger

            def _get_agent(self) -> Agent[object, str]:
                return MagicMock()

        agent = TestAgent()
        formatted = agent.format_extract_result(mock_result)

        assert "## 失敗したURL" in formatted
        assert "- https://failed.com: Connection timeout" in formatted


class TestTavilyContextToolOutput:
    """Tests for tavily_context tool output formatting."""

    @pytest.mark.asyncio
    async def test_tavily_context_formats_correctly(self) -> None:
        """tavily_context returns formatted string per contracts/tavily-tools.md."""
        from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin

        class TestAgent(TavilyToolsRepositoryMixin):
            def __init__(self) -> None:
                self._logger = MockLogger()

            @property
            def logger(self) -> MockLogger:
                return self._logger

            def _get_agent(self) -> Agent[object, str]:
                return MagicMock()

        agent = TestAgent()
        formatted = agent.format_context_result(
            "quantum computing basics", "Quantum computing is a revolutionary..."
        )

        # Check format per contracts/tavily-tools.md section 4.4
        assert "## RAG用検索コンテキスト: quantum computing basics" in formatted
        assert "Quantum computing is a revolutionary..." in formatted


class TestTavilyExtractValidation:
    """Tests for tavily_extract input validation."""

    @pytest.mark.asyncio
    async def test_tavily_extract_empty_url_list_raises_validation_error(
        self,
    ) -> None:
        """tavily_extract handles empty URL list with VALIDATION_ERROR (T015)."""
        from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin
        from mixseek_plus.errors import TavilyAPIError

        class TestAgent(TavilyToolsRepositoryMixin):
            def __init__(self) -> None:
                self._logger = MockLogger()

            @property
            def logger(self) -> MockLogger:
                return self._logger

            def _get_agent(self) -> Agent[object, str]:
                return MagicMock()

        agent = TestAgent()

        # validate_extract_urls should raise for empty list
        with pytest.raises(TavilyAPIError) as exc_info:
            agent.validate_extract_urls([])

        assert exc_info.value.error_type == "VALIDATION_ERROR"
        assert (
            "空" in exc_info.value.message or "empty" in exc_info.value.message.lower()
        )

    @pytest.mark.asyncio
    async def test_tavily_extract_url_limit_exceeded_truncates_with_warning(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """tavily_extract truncates to 20 URLs with warning per NFR-004a (T016)."""
        import logging

        from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin

        class TestAgent(TavilyToolsRepositoryMixin):
            def __init__(self) -> None:
                self._logger = MockLogger()

            @property
            def logger(self) -> MockLogger:
                return self._logger

            def _get_agent(self) -> Agent[object, str]:
                return MagicMock()

        agent = TestAgent()

        # Create list with 21 URLs (exceeds limit of 20)
        input_urls = [f"https://example.com/page{i}" for i in range(21)]

        with caplog.at_level(logging.WARNING):
            result_urls = agent.validate_extract_urls(input_urls)

        # Should truncate to 20 URLs
        assert len(result_urls) == 20
        # Should keep first 20 URLs
        assert result_urls == input_urls[:20]
        # Should log a warning
        assert "URL数が上限" in caplog.text
        assert "20" in caplog.text

    @pytest.mark.asyncio
    async def test_tavily_extract_accepts_valid_url_list(self) -> None:
        """tavily_extract accepts valid URL list (1-20 URLs)."""
        from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin

        class TestAgent(TavilyToolsRepositoryMixin):
            def __init__(self) -> None:
                self._logger = MockLogger()

            @property
            def logger(self) -> MockLogger:
                return self._logger

            def _get_agent(self) -> Agent[object, str]:
                return MagicMock()

        agent = TestAgent()

        # Valid single URL
        urls = agent.validate_extract_urls(["https://example.com"])
        assert urls == ["https://example.com"]

        # Valid 20 URLs (max limit)
        urls = agent.validate_extract_urls(
            [f"https://example.com/page{i}" for i in range(20)]
        )
        assert len(urls) == 20


class TestTavilyToolsRepositoryMixinErrorFormatting:
    """Tests for error message formatting."""

    def test_format_error_message_produces_correct_format(self) -> None:
        """format_error_message produces format per contracts/tavily-tools.md section 5.3."""
        from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin
        from mixseek_plus.errors import TavilyAPIError

        class TestAgent(TavilyToolsRepositoryMixin):
            def __init__(self) -> None:
                self._logger = MockLogger()

            @property
            def logger(self) -> MockLogger:
                return self._logger

            def _get_agent(self) -> Agent[object, str]:
                return MagicMock()

        agent = TestAgent()
        error = TavilyAPIError(
            message="認証に失敗しました",
            status_code=401,
            error_type="AUTH_ERROR",
        )

        formatted = agent.format_error_message(error)

        assert "Tavily API エラー:" in formatted
        assert "認証に失敗しました" in formatted
        assert "エラータイプ: AUTH_ERROR" in formatted
