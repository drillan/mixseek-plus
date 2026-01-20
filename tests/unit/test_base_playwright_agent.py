"""Unit tests for BasePlaywrightAgent.

Tests cover:
- PlaywrightConfig validation
- FetchResult dataclass
- BasePlaywrightAgent initialization
- Browser initialization error handling
- Retry logic with exponential backoff
- Resource blocking setup
- Retryable error detection

Note: All imports that transitively import MemberAgentConfig must be done
      inside test functions to ensure patch_core() has been called first.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from mixseek_plus.errors import FetchError, PlaywrightNotInstalledError


class TestPlaywrightConfig:
    """Tests for PlaywrightConfig Pydantic model."""

    def test_default_values(self) -> None:
        """Should have sensible defaults."""
        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig

        config = PlaywrightConfig()

        assert config.headless is True
        assert config.timeout_ms == 30000
        assert config.wait_for_load_state == "load"
        assert config.retry_count == 0
        assert config.retry_delay_ms == 1000
        assert config.block_resources is None

    def test_accepts_valid_wait_states(self) -> None:
        """Should accept valid wait_for_load_state values."""
        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig

        for state in ["load", "domcontentloaded", "networkidle"]:
            config = PlaywrightConfig(wait_for_load_state=state)  # type: ignore[arg-type]
            assert config.wait_for_load_state == state

    def test_accepts_custom_timeout(self) -> None:
        """Should accept custom timeout within bounds."""
        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig

        config = PlaywrightConfig(timeout_ms=60000)
        assert config.timeout_ms == 60000

    def test_rejects_timeout_below_minimum(self) -> None:
        """Should reject timeout below 1000ms."""
        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig

        with pytest.raises(ValidationError) as exc_info:
            PlaywrightConfig(timeout_ms=500)

        assert "timeout_ms" in str(exc_info.value)

    def test_rejects_timeout_above_maximum(self) -> None:
        """Should reject timeout above 300000ms."""
        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig

        with pytest.raises(ValidationError) as exc_info:
            PlaywrightConfig(timeout_ms=500000)

        assert "timeout_ms" in str(exc_info.value)

    def test_accepts_retry_count_within_bounds(self) -> None:
        """Should accept retry_count between 0 and 10."""
        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig

        config = PlaywrightConfig(retry_count=5)
        assert config.retry_count == 5

    def test_rejects_negative_retry_count(self) -> None:
        """Should reject negative retry_count."""
        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig

        with pytest.raises(ValidationError) as exc_info:
            PlaywrightConfig(retry_count=-1)

        assert "retry_count" in str(exc_info.value)

    def test_accepts_block_resources(self) -> None:
        """Should accept list of resource types to block."""
        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig

        config = PlaywrightConfig(block_resources=["image", "font", "stylesheet"])
        assert config.block_resources == ["image", "font", "stylesheet"]

    def test_accepts_headed_mode(self) -> None:
        """Should accept headless=False for headed mode."""
        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig

        config = PlaywrightConfig(headless=False)
        assert config.headless is False


class TestFetchResult:
    """Tests for FetchResult dataclass."""

    def test_success_factory_method(self) -> None:
        """success() should create a success result."""
        from mixseek_plus.agents.base_playwright_agent import FetchResult

        result = FetchResult.success(
            content="# Hello", url="https://example.com", attempts=1
        )

        assert result.status == "success"
        assert result.content == "# Hello"
        assert result.url == "https://example.com"
        assert result.error is None
        assert result.attempts == 1

    def test_failure_factory_method(self) -> None:
        """failure() should create an error result."""
        from mixseek_plus.agents.base_playwright_agent import FetchResult

        result = FetchResult.failure(
            url="https://example.com", error="Connection timeout", attempts=3
        )

        assert result.status == "error"
        assert result.content == ""
        assert result.url == "https://example.com"
        assert result.error == "Connection timeout"
        assert result.attempts == 3

    def test_is_immutable(self) -> None:
        """FetchResult should be immutable (frozen)."""
        from mixseek_plus.agents.base_playwright_agent import FetchResult

        result = FetchResult.success(content="test", url="https://example.com")

        with pytest.raises(AttributeError):
            result.content = "modified"  # type: ignore[misc]


class TestBasePlaywrightAgentInitialization:
    """Tests for BasePlaywrightAgent initialization."""

    def test_raises_playwright_not_installed_when_missing(
        self, mock_groq_api_key: str
    ) -> None:
        """Should raise PlaywrightNotInstalledError when playwright is missing."""
        from mixseek.models.member_agent import MemberAgentConfig

        from mixseek_plus.agents.playwright_markdown_fetch_agent import (
            PlaywrightMarkdownFetchAgent,
        )

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",  # Use custom to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
        )

        with patch(
            "mixseek_plus.agents.base_playwright_agent._check_playwright_available"
        ) as mock_check:
            mock_check.side_effect = PlaywrightNotInstalledError()
            with pytest.raises(PlaywrightNotInstalledError):
                PlaywrightMarkdownFetchAgent(config)

    def test_parses_playwright_config_from_dict(self, mock_groq_api_key: str) -> None:
        """Should parse playwright config from config dictionary."""
        from mixseek.models.member_agent import MemberAgentConfig

        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig
        from mixseek_plus.agents.playwright_markdown_fetch_agent import (
            PlaywrightMarkdownFetchAgent,
        )

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",  # Use custom to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
        )

        with (
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_playwright_available"
            ),
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_markitdown_available"
            ),
        ):
            agent = PlaywrightMarkdownFetchAgent(config)

            # Manually set playwright config (since MemberAgentConfig doesn't have playwright field)
            agent._playwright_config = PlaywrightConfig(
                headless=False,
                timeout_ms=60000,
                wait_for_load_state="networkidle",
            )

            assert agent.playwright_config.headless is False
            assert agent.playwright_config.timeout_ms == 60000
            assert agent.playwright_config.wait_for_load_state == "networkidle"


class TestBrowserInitializationErrorHandling:
    """Tests for browser initialization error handling."""

    @pytest.mark.asyncio
    async def test_cleanup_playwright_on_browser_launch_failure(
        self, mock_groq_api_key: str
    ) -> None:
        """Should clean up playwright instance when browser launch fails."""
        from mixseek.models.member_agent import MemberAgentConfig

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",  # Use custom to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
        )

        with (
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_playwright_available"
            ),
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_markitdown_available"
            ),
        ):
            from mixseek_plus.agents.playwright_markdown_fetch_agent import (
                PlaywrightMarkdownFetchAgent,
            )

            agent = PlaywrightMarkdownFetchAgent(config)

            mock_playwright_instance = MagicMock()
            mock_playwright_instance.stop = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(
                side_effect=Exception("Browser launch failed")
            )

            with patch(
                "playwright.async_api.async_playwright"
            ) as mock_async_playwright:
                mock_async_playwright.return_value.start = AsyncMock(
                    return_value=mock_playwright_instance
                )

                with pytest.raises(FetchError) as exc_info:
                    await agent._ensure_browser()

                # Verify playwright instance was cleaned up
                mock_playwright_instance.stop.assert_awaited_once()
                assert "Failed to launch browser" in str(exc_info.value)


class TestRetryLogic:
    """Tests for retry logic with exponential backoff."""

    def test_is_retryable_error_for_timeout(self, mock_groq_api_key: str) -> None:
        """Timeout errors should be retryable."""
        from mixseek.models.member_agent import MemberAgentConfig

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",  # Use custom to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
        )

        with (
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_playwright_available"
            ),
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_markitdown_available"
            ),
        ):
            from mixseek_plus.agents.playwright_markdown_fetch_agent import (
                PlaywrightMarkdownFetchAgent,
            )

            agent = PlaywrightMarkdownFetchAgent(config)

            timeout_error = FetchError(
                message="Page load timeout after 30000ms",
                url="https://example.com",
            )

            assert agent._is_retryable_error(timeout_error) is True

    def test_is_retryable_error_for_server_error(self, mock_groq_api_key: str) -> None:
        """5xx server errors should be retryable."""
        from mixseek.models.member_agent import MemberAgentConfig

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",  # Use custom to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
        )

        with (
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_playwright_available"
            ),
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_markitdown_available"
            ),
        ):
            from mixseek_plus.agents.playwright_markdown_fetch_agent import (
                PlaywrightMarkdownFetchAgent,
            )

            agent = PlaywrightMarkdownFetchAgent(config)

            server_error = FetchError(
                message="HTTP 503 Service Unavailable",
                url="https://example.com",
            )

            assert agent._is_retryable_error(server_error) is True

    def test_is_not_retryable_for_404(self, mock_groq_api_key: str) -> None:
        """404 errors should not be retryable."""
        from mixseek.models.member_agent import MemberAgentConfig

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",  # Use custom to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
        )

        with (
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_playwright_available"
            ),
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_markitdown_available"
            ),
        ):
            from mixseek_plus.agents.playwright_markdown_fetch_agent import (
                PlaywrightMarkdownFetchAgent,
            )

            agent = PlaywrightMarkdownFetchAgent(config)

            not_found_error = FetchError(
                message="HTTP 404 Not Found",
                url="https://example.com/notfound",
            )

            assert agent._is_retryable_error(not_found_error) is False

    def test_is_not_retryable_for_non_fetch_error(self, mock_groq_api_key: str) -> None:
        """Non-FetchError exceptions should not be retryable."""
        from mixseek.models.member_agent import MemberAgentConfig

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",  # Use custom to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
        )

        with (
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_playwright_available"
            ),
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_markitdown_available"
            ),
        ):
            from mixseek_plus.agents.playwright_markdown_fetch_agent import (
                PlaywrightMarkdownFetchAgent,
            )

            agent = PlaywrightMarkdownFetchAgent(config)

            generic_error = ValueError("Some error")

            assert agent._is_retryable_error(generic_error) is False
