"""Unit tests for TavilyAPIClient.

Tests for T004-T008:
- T004: Basic functionality tests (search, extract, get_search_context)
- T005: AUTH_ERROR (401) handling
- T006: RATE_LIMIT_ERROR (429) with retry handling
- T007: TIMEOUT_ERROR handling
- T008: VALIDATION_ERROR (400) handling
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from mixseek_plus.errors import TavilyAPIError

if TYPE_CHECKING:
    pass


class TestTavilySearchResult:
    """Tests for TavilySearchResult and TavilyExtractResult model validation."""

    def test_search_result_item_validates_required_fields(self) -> None:
        """TavilySearchResultItem validates required fields."""
        from mixseek_plus.providers.tavily_client import TavilySearchResultItem

        item = TavilySearchResultItem(
            title="Test Title",
            url="https://example.com",
            content="Test content",
            score=0.95,
        )
        assert item.title == "Test Title"
        assert item.url == "https://example.com"
        assert item.content == "Test content"
        assert item.score == 0.95
        assert item.raw_content is None

    def test_search_result_item_accepts_raw_content(self) -> None:
        """TavilySearchResultItem accepts optional raw_content."""
        from mixseek_plus.providers.tavily_client import TavilySearchResultItem

        item = TavilySearchResultItem(
            title="Test Title",
            url="https://example.com",
            content="Test content",
            score=0.95,
            raw_content="<html>Raw HTML</html>",
        )
        assert item.raw_content == "<html>Raw HTML</html>"

    def test_search_result_validates_structure(self) -> None:
        """TavilySearchResult validates overall structure."""
        from mixseek_plus.providers.tavily_client import (
            TavilySearchResult,
            TavilySearchResultItem,
        )

        result = TavilySearchResult(
            query="test query",
            results=[
                TavilySearchResultItem(
                    title="Test",
                    url="https://example.com",
                    content="Content",
                    score=0.9,
                )
            ],
            response_time=1.23,
        )
        assert result.query == "test query"
        assert len(result.results) == 1
        assert result.answer is None
        assert result.images is None
        assert result.response_time == 1.23

    def test_extract_result_validates_structure(self) -> None:
        """TavilyExtractResult validates overall structure."""
        from mixseek_plus.providers.tavily_client import (
            TavilyExtractFailedItem,
            TavilyExtractResult,
            TavilyExtractResultItem,
        )

        result = TavilyExtractResult(
            results=[
                TavilyExtractResultItem(
                    url="https://example.com",
                    raw_content="Extracted content",
                )
            ],
            failed_results=[
                TavilyExtractFailedItem(
                    url="https://failed.com",
                    error="Connection error",
                )
            ],
            response_time=2.34,
        )
        assert len(result.results) == 1
        assert len(result.failed_results) == 1
        assert result.response_time == 2.34


class TestTavilyAPIClientSearch:
    """Tests for TavilyAPIClient.search() method."""

    @pytest.mark.asyncio
    async def test_search_returns_formatted_result(self) -> None:
        """search() returns TavilySearchResult with mock response."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        mock_response = {
            "query": "Python latest version",
            "results": [
                {
                    "title": "Python 3.13 Release",
                    "url": "https://python.org/downloads/release/python-3130/",
                    "content": "Python 3.13 is the latest version...",
                    "score": 0.95,
                }
            ],
            "response_time": 1.5,
        }

        with patch.object(TavilyAPIClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(api_key="test-api-key")
            result = await client.search("Python latest version")

            assert result.query == "Python latest version"
            assert len(result.results) == 1
            assert result.results[0].title == "Python 3.13 Release"
            assert result.results[0].score == 0.95

    @pytest.mark.asyncio
    async def test_search_passes_parameters_correctly(self) -> None:
        """search() passes all parameters to underlying client."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        mock_response = {
            "query": "test",
            "results": [],
            "response_time": 0.5,
        }

        with patch.object(TavilyAPIClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(api_key="test-api-key")
            await client.search(
                query="test",
                search_depth="advanced",
                max_results=10,
                include_answer=True,
                include_raw_content=True,
                include_images=True,
                include_domains=["example.com"],
                exclude_domains=["spam.com"],
            )

            mock_client.search.assert_called_once()
            call_kwargs = mock_client.search.call_args[1]
            assert call_kwargs["query"] == "test"
            assert call_kwargs["search_depth"] == "advanced"
            assert call_kwargs["max_results"] == 10
            assert call_kwargs["include_answer"] is True
            assert call_kwargs["include_raw_content"] is True
            assert call_kwargs["include_images"] is True
            assert call_kwargs["include_domains"] == ["example.com"]
            assert call_kwargs["exclude_domains"] == ["spam.com"]


class TestTavilyAPIClientExtract:
    """Tests for TavilyAPIClient.extract() method."""

    @pytest.mark.asyncio
    async def test_extract_returns_formatted_result(self) -> None:
        """extract() returns TavilyExtractResult with mock response."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        mock_response = {
            "results": [
                {
                    "url": "https://example.com/article",
                    "raw_content": "Article content here...",
                }
            ],
            "failed_results": [],
            "response_time": 2.0,
        }

        with patch.object(TavilyAPIClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.extract = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(api_key="test-api-key")
            result = await client.extract(["https://example.com/article"])

            assert len(result.results) == 1
            assert result.results[0].url == "https://example.com/article"
            assert result.results[0].raw_content == "Article content here..."
            assert len(result.failed_results) == 0

    @pytest.mark.asyncio
    async def test_extract_handles_partial_failures(self) -> None:
        """extract() handles partial URL failures gracefully."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        mock_response = {
            "results": [
                {
                    "url": "https://success.com",
                    "raw_content": "Success content",
                }
            ],
            "failed_results": [
                {
                    "url": "https://failed.com",
                    "error": "Connection timeout",
                }
            ],
            "response_time": 3.0,
        }

        with patch.object(TavilyAPIClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.extract = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(api_key="test-api-key")
            result = await client.extract(["https://success.com", "https://failed.com"])

            assert len(result.results) == 1
            assert len(result.failed_results) == 1
            assert result.failed_results[0].error == "Connection timeout"


class TestTavilyAPIClientGetSearchContext:
    """Tests for TavilyAPIClient.get_search_context() method."""

    @pytest.mark.asyncio
    async def test_get_search_context_returns_string(self) -> None:
        """get_search_context() returns context string."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        mock_context = "Quantum computing is a field of computing..."

        with patch.object(TavilyAPIClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_search_context = AsyncMock(return_value=mock_context)
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(api_key="test-api-key")
            result = await client.get_search_context("quantum computing basics")

            assert result == mock_context

    @pytest.mark.asyncio
    async def test_get_search_context_passes_parameters(self) -> None:
        """get_search_context() passes all parameters correctly."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        with patch.object(TavilyAPIClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_search_context = AsyncMock(return_value="context")
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(api_key="test-api-key")
            await client.get_search_context(
                query="test",
                search_depth="advanced",
                max_results=10,
                max_tokens=2000,
            )

            mock_client.get_search_context.assert_called_once()
            call_kwargs = mock_client.get_search_context.call_args[1]
            assert call_kwargs["query"] == "test"
            assert call_kwargs["search_depth"] == "advanced"
            assert call_kwargs["max_results"] == 10
            assert call_kwargs["max_tokens"] == 2000


class TestTavilyAPIClientRetryLogic:
    """Tests for TavilyAPIClient retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_on_server_error(self) -> None:
        """Client retries on 500 server error with exponential backoff."""
        from httpx import HTTPStatusError, Request, Response

        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        # Create mock HTTP error
        request = Request("POST", "https://api.tavily.com/search")
        response = Response(500, request=request)
        http_error = HTTPStatusError("Server error", request=request, response=response)

        call_count = 0

        async def mock_search(**kwargs: object) -> dict[str, object]:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise http_error
            return {
                "query": "test",
                "results": [],
                "response_time": 0.5,
            }

        with (
            patch.object(TavilyAPIClient, "_get_client") as mock_get_client,
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_client = AsyncMock()
            mock_client.search = mock_search
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(
                api_key="test-api-key",
                max_retries=3,
                base_delay=0.1,
            )
            result = await client.search("test")

            assert call_count == 3
            assert result.query == "test"

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self) -> None:
        """Client uses exponential backoff delays between retries."""
        from httpx import HTTPStatusError, Request, Response

        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        request = Request("POST", "https://api.tavily.com/search")
        response = Response(500, request=request)
        http_error = HTTPStatusError("Server error", request=request, response=response)

        delays: list[float] = []
        call_count = 0

        async def mock_search(**kwargs: object) -> dict[str, object]:
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise http_error
            return {"query": "test", "results": [], "response_time": 0.5}

        async def mock_sleep(delay: float) -> None:
            delays.append(delay)

        with (
            patch.object(TavilyAPIClient, "_get_client") as mock_get_client,
            patch("asyncio.sleep", side_effect=mock_sleep),
        ):
            mock_client = AsyncMock()
            mock_client.search = mock_search
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(
                api_key="test-api-key",
                max_retries=4,
                base_delay=1.0,
                max_delay=10.0,
            )
            await client.search("test")

            # Expected delays: 1.0, 2.0, 4.0 (exponential backoff)
            assert len(delays) == 3
            assert delays[0] == pytest.approx(1.0)
            assert delays[1] == pytest.approx(2.0)
            assert delays[2] == pytest.approx(4.0)

    @pytest.mark.asyncio
    async def test_max_delay_cap(self) -> None:
        """Exponential backoff respects max_delay cap."""
        from httpx import HTTPStatusError, Request, Response

        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        request = Request("POST", "https://api.tavily.com/search")
        response = Response(500, request=request)
        http_error = HTTPStatusError("Server error", request=request, response=response)

        delays: list[float] = []
        call_count = 0

        async def mock_search(**kwargs: object) -> dict[str, object]:
            nonlocal call_count
            call_count += 1
            if call_count <= 5:
                raise http_error
            return {"query": "test", "results": [], "response_time": 0.5}

        async def mock_sleep(delay: float) -> None:
            delays.append(delay)

        with (
            patch.object(TavilyAPIClient, "_get_client") as mock_get_client,
            patch("asyncio.sleep", side_effect=mock_sleep),
        ):
            mock_client = AsyncMock()
            mock_client.search = mock_search
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(
                api_key="test-api-key",
                max_retries=6,
                base_delay=1.0,
                max_delay=5.0,  # Cap at 5 seconds
            )
            await client.search("test")

            # Delays should be capped at 5.0
            # Expected: 1.0, 2.0, 4.0, 5.0, 5.0 (capped)
            assert all(d <= 5.0 for d in delays)


class TestTavilyAPIClientAuthError:
    """Tests for AUTH_ERROR (401) handling (T005)."""

    @pytest.mark.asyncio
    async def test_auth_error_raises_tavily_api_error(self) -> None:
        """401 error raises TavilyAPIError with AUTH_ERROR type."""
        from httpx import HTTPStatusError, Request, Response

        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        request = Request("POST", "https://api.tavily.com/search")
        response = Response(401, request=request)
        http_error = HTTPStatusError("Unauthorized", request=request, response=response)

        with patch.object(TavilyAPIClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search = AsyncMock(side_effect=http_error)
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(api_key="invalid-key")

            with pytest.raises(TavilyAPIError) as exc_info:
                await client.search("test")

            assert exc_info.value.error_type == "AUTH_ERROR"
            assert exc_info.value.status_code == 401
            assert exc_info.value.is_retryable is False
            assert (
                "認証に失敗" in exc_info.value.message
                or "authentication" in exc_info.value.message.lower()
            )


class TestTavilyAPIClientRateLimitError:
    """Tests for RATE_LIMIT_ERROR (429) with retry handling (T006)."""

    @pytest.mark.asyncio
    async def test_rate_limit_error_is_retried(self) -> None:
        """429 error is retried before raising TavilyAPIError."""
        from httpx import HTTPStatusError, Request, Response

        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        request = Request("POST", "https://api.tavily.com/search")
        response = Response(429, request=request)
        http_error = HTTPStatusError("Rate limited", request=request, response=response)

        call_count = 0

        async def mock_search(**kwargs: object) -> dict[str, object]:
            nonlocal call_count
            call_count += 1
            raise http_error

        with (
            patch.object(TavilyAPIClient, "_get_client") as mock_get_client,
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_client = AsyncMock()
            mock_client.search = mock_search
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(
                api_key="test-api-key",
                max_retries=3,
                base_delay=0.1,
            )

            with pytest.raises(TavilyAPIError) as exc_info:
                await client.search("test")

            # Should have retried max_retries times
            assert call_count == 3
            assert exc_info.value.error_type == "RATE_LIMIT_ERROR"
            assert exc_info.value.status_code == 429
            assert exc_info.value.is_retryable is True


class TestTavilyAPIClientTimeoutError:
    """Tests for TIMEOUT_ERROR handling (T007)."""

    @pytest.mark.asyncio
    async def test_timeout_error_raises_tavily_api_error(self) -> None:
        """Timeout error raises TavilyAPIError with TIMEOUT_ERROR type."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        with patch.object(TavilyAPIClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search = AsyncMock(
                side_effect=asyncio.TimeoutError("Request timed out")
            )
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(
                api_key="test-api-key",
                timeout=1.0,
                max_retries=1,
            )

            with pytest.raises(TavilyAPIError) as exc_info:
                await client.search("test")

            assert exc_info.value.error_type == "TIMEOUT_ERROR"
            assert exc_info.value.is_retryable is True


class TestTavilyAPIClientValidationError:
    """Tests for VALIDATION_ERROR (400) handling (T008)."""

    @pytest.mark.asyncio
    async def test_validation_error_raises_tavily_api_error(self) -> None:
        """400 error raises TavilyAPIError with VALIDATION_ERROR type."""
        from httpx import HTTPStatusError, Request, Response

        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        request = Request("POST", "https://api.tavily.com/search")
        response = Response(400, request=request, text="Invalid query parameter")
        http_error = HTTPStatusError("Bad request", request=request, response=response)

        with patch.object(TavilyAPIClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search = AsyncMock(side_effect=http_error)
            mock_get_client.return_value = mock_client

            client = TavilyAPIClient(api_key="test-api-key")

            with pytest.raises(TavilyAPIError) as exc_info:
                await client.search("")

            assert exc_info.value.error_type == "VALIDATION_ERROR"
            assert exc_info.value.status_code == 400
            assert exc_info.value.is_retryable is False


class TestTavilyAPIClientInstantiation:
    """Tests for TavilyAPIClient instantiation."""

    def test_client_accepts_api_key(self) -> None:
        """Client can be instantiated with valid API key."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        client = TavilyAPIClient(api_key="tvly-test-key")
        assert client.api_key == "tvly-test-key"

    def test_client_default_parameters(self) -> None:
        """Client has correct default parameters."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        client = TavilyAPIClient(api_key="test-key")
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.base_delay == 1.0
        assert client.max_delay == 10.0

    def test_client_custom_parameters(self) -> None:
        """Client accepts custom parameters."""
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        client = TavilyAPIClient(
            api_key="test-key",
            timeout=60.0,
            max_retries=5,
            base_delay=2.0,
            max_delay=20.0,
        )
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.base_delay == 2.0
        assert client.max_delay == 20.0
