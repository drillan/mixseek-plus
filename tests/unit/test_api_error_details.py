"""Tests for detailed API error handling (GR-032).

This module tests that API errors (429 rate limit, 503 service unavailable)
are properly handled with user-friendly messages.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mixseek.models.member_agent import MemberAgentConfig, ResultStatus


class TestGroqAgentAPIErrorHandling:
    """Test detailed API error handling in GroqPlainAgent."""

    @pytest.fixture
    def groq_config(self) -> MemberAgentConfig:
        """Create a basic GroqPlainAgent config."""
        # Use type="custom" to bypass mixseek-core model validation
        return MemberAgentConfig(
            name="test-groq-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful assistant.",
        )

    @pytest.mark.asyncio
    async def test_rate_limit_error_429_has_clear_message(
        self, mock_groq_api_key: str, groq_config: MemberAgentConfig
    ) -> None:
        """Test that HTTP 429 error produces a rate limit message.

        GR-032: API errors should be wrapped with descriptive messages.
        429 should indicate rate limiting.
        """
        from httpx import HTTPStatusError, Request, Response

        from mixseek_plus.agents.groq_agent import GroqPlainAgent

        agent = GroqPlainAgent(groq_config)

        # Create a mock 429 response
        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        http_error = HTTPStatusError(
            "Rate limit exceeded",
            request=mock_request,
            response=mock_response,
        )

        # Mock the agent's run method to raise the error
        with patch.object(agent._agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = http_error

            result = await agent.execute("Test task")

        # Check that the error message indicates rate limiting
        assert result.status == ResultStatus.ERROR
        error_msg = result.error_message.lower() if result.error_message else ""
        assert any(
            keyword in error_msg
            for keyword in ["rate limit", "レート制限", "429", "wait", "retry"]
        ), f"Error message should indicate rate limiting: {result.error_message}"
        assert result.error_code == "RATE_LIMIT_ERROR"

    @pytest.mark.asyncio
    async def test_service_unavailable_error_503_has_clear_message(
        self, mock_groq_api_key: str, groq_config: MemberAgentConfig
    ) -> None:
        """Test that HTTP 503 error produces a service unavailable message.

        GR-032: API errors should be wrapped with descriptive messages.
        503 should indicate service temporarily unavailable.
        """
        from httpx import HTTPStatusError, Request, Response

        from mixseek_plus.agents.groq_agent import GroqPlainAgent

        agent = GroqPlainAgent(groq_config)

        # Create a mock 503 response
        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"

        http_error = HTTPStatusError(
            "Service Unavailable",
            request=mock_request,
            response=mock_response,
        )

        # Mock the agent's run method to raise the error
        with patch.object(agent._agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = http_error

            result = await agent.execute("Test task")

        # Check that the error message indicates service unavailability
        assert result.status == ResultStatus.ERROR
        error_msg = result.error_message.lower() if result.error_message else ""
        assert any(
            keyword in error_msg
            for keyword in [
                "unavailable",
                "一時停止",
                "503",
                "try again",
                "temporarily",
            ]
        ), f"Error message should indicate service unavailable: {result.error_message}"
        assert result.error_code == "SERVICE_UNAVAILABLE_ERROR"


class TestGroqWebSearchAgentAPIErrorHandling:
    """Test detailed API error handling in GroqWebSearchAgent."""

    @pytest.fixture
    def groq_web_search_config(self) -> MemberAgentConfig:
        """Create a basic GroqWebSearchAgent config."""
        # Use type="custom" to bypass mixseek-core model validation
        return MemberAgentConfig(
            name="test-groq-web-search",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful assistant with web search.",
        )

    @pytest.mark.asyncio
    async def test_rate_limit_error_429_has_clear_message(
        self, mock_groq_api_key: str, groq_web_search_config: MemberAgentConfig
    ) -> None:
        """Test that HTTP 429 error produces a rate limit message.

        GR-032: API errors should be wrapped with descriptive messages.
        429 should indicate rate limiting.
        """
        from httpx import HTTPStatusError, Request, Response

        from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

        agent = GroqWebSearchAgent(groq_web_search_config)

        # Create a mock 429 response
        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        http_error = HTTPStatusError(
            "Rate limit exceeded",
            request=mock_request,
            response=mock_response,
        )

        # Mock the agent's run method to raise the error
        with patch.object(agent._agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = http_error

            result = await agent.execute("Test task")

        # Check that the error message indicates rate limiting
        assert result.status == ResultStatus.ERROR
        error_msg = result.error_message.lower() if result.error_message else ""
        assert any(
            keyword in error_msg
            for keyword in ["rate limit", "レート制限", "429", "wait", "retry"]
        ), f"Error message should indicate rate limiting: {result.error_message}"
        assert result.error_code == "RATE_LIMIT_ERROR"

    @pytest.mark.asyncio
    async def test_service_unavailable_error_503_has_clear_message(
        self, mock_groq_api_key: str, groq_web_search_config: MemberAgentConfig
    ) -> None:
        """Test that HTTP 503 error produces a service unavailable message.

        GR-032: API errors should be wrapped with descriptive messages.
        503 should indicate service temporarily unavailable.
        """
        from httpx import HTTPStatusError, Request, Response

        from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

        agent = GroqWebSearchAgent(groq_web_search_config)

        # Create a mock 503 response
        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"

        http_error = HTTPStatusError(
            "Service Unavailable",
            request=mock_request,
            response=mock_response,
        )

        # Mock the agent's run method to raise the error
        with patch.object(agent._agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = http_error

            result = await agent.execute("Test task")

        # Check that the error message indicates service unavailability
        assert result.status == ResultStatus.ERROR
        error_msg = result.error_message.lower() if result.error_message else ""
        assert any(
            keyword in error_msg
            for keyword in [
                "unavailable",
                "一時停止",
                "503",
                "try again",
                "temporarily",
            ]
        ), f"Error message should indicate service unavailable: {result.error_message}"
        assert result.error_code == "SERVICE_UNAVAILABLE_ERROR"


class TestAPIErrorCodes:
    """Test that appropriate error codes are used for API errors."""

    @pytest.fixture
    def groq_config(self) -> MemberAgentConfig:
        """Create a basic GroqPlainAgent config."""
        # Use type="custom" to bypass mixseek-core model validation
        return MemberAgentConfig(
            name="test-groq-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful assistant.",
        )

    @pytest.mark.asyncio
    async def test_401_error_uses_auth_error_code(
        self, mock_groq_api_key: str, groq_config: MemberAgentConfig
    ) -> None:
        """Test that HTTP 401 error uses AUTH_ERROR code."""
        from httpx import HTTPStatusError, Request, Response

        from mixseek_plus.agents.groq_agent import GroqPlainAgent

        agent = GroqPlainAgent(groq_config)

        # Create a mock 401 response
        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        http_error = HTTPStatusError(
            "Unauthorized",
            request=mock_request,
            response=mock_response,
        )

        with patch.object(agent._agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = http_error

            result = await agent.execute("Test task")

        assert result.status == ResultStatus.ERROR
        assert result.error_code == "AUTH_ERROR"
