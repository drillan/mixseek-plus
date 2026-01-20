"""Unit tests for PydanticAgentExecutorMixin.

Tests cover:
- MIX-001: _extract_usage_info extracts token counts correctly
- MIX-002: _execute_pydantic_agent validates empty task
- MIX-003: _execute_pydantic_agent logs execution start
- MIX-004: _execute_pydantic_agent calls _build_agent_metadata
- MIX-005: _execute_pydantic_agent handles exceptions via _handle_execution_error
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mixseek.models.member_agent import (
    MemberAgentConfig,
    MemberAgentResult,
    ResultStatus,
)

from mixseek_plus.agents.mixins.execution import PydanticAgentExecutorMixin

if TYPE_CHECKING:
    pass


class ConcreteAgentWithMixin(PydanticAgentExecutorMixin):
    """Concrete implementation for testing the mixin."""

    def __init__(self) -> None:
        """Initialize test agent."""
        self._agent_name = "test_agent"
        self._agent_type = "test"
        # Use MagicMock for config to avoid validation issues
        self._config = MagicMock(spec=MemberAgentConfig)
        self._config.model = "groq:llama-3.3-70b-versatile"
        self._config.temperature = 0.7
        self._config.max_tokens = 1024
        self._logger = MagicMock()
        self._mock_agent = MagicMock()
        self._mock_deps: object = {}

    @property
    def agent_name(self) -> str:
        """Agent name."""
        return self._agent_name

    @property
    def agent_type(self) -> str:
        """Agent type."""
        return self._agent_type

    @property
    def config(self) -> MemberAgentConfig:
        """Agent config."""
        return self._config

    @property
    def logger(self) -> MagicMock:
        """Logger."""
        return self._logger

    def _get_agent(self) -> MagicMock:
        """Get mock agent."""
        return self._mock_agent

    def _create_deps(self) -> object:
        """Create mock deps."""
        return self._mock_deps

    def _build_agent_metadata(
        self, context: dict[str, object] | None
    ) -> dict[str, object]:
        """Build test metadata."""
        metadata: dict[str, object] = {
            "model_id": self._config.model,
            "test_field": "test_value",
        }
        if context:
            metadata["context"] = context
        return metadata

    def _handle_execution_error(
        self,
        error: Exception,
        task: str,
        kwargs: dict[str, object],
        execution_id: str,
        start_time: float,
    ) -> MemberAgentResult:
        """Handle test errors."""
        return MemberAgentResult.error(
            error_message=str(error),
            agent_name=self._agent_name,
            agent_type=self._agent_type,
            error_code="TEST_ERROR",
            execution_time_ms=100,
        )


class TestExtractUsageInfo:
    """Tests for _extract_usage_info method (MIX-001)."""

    def test_extract_usage_info_with_all_fields(self) -> None:
        """MIX-001: _extract_usage_info extracts all token counts."""
        agent = ConcreteAgentWithMixin()

        # Create mock result with usage
        mock_usage = MagicMock()
        mock_usage.total_tokens = 100
        mock_usage.prompt_tokens = 60
        mock_usage.completion_tokens = 40
        mock_usage.requests = 1

        mock_result = MagicMock()
        mock_result.usage.return_value = mock_usage

        usage_info = agent._extract_usage_info(mock_result)

        assert usage_info["total_tokens"] == 100
        assert usage_info["prompt_tokens"] == 60
        assert usage_info["completion_tokens"] == 40
        assert usage_info["requests"] == 1

    def test_extract_usage_info_without_usage(self) -> None:
        """MIX-001: _extract_usage_info returns empty dict when no usage."""
        agent = ConcreteAgentWithMixin()

        # Create mock result without usage attribute
        mock_result = MagicMock(spec=[])  # No usage attribute

        usage_info = agent._extract_usage_info(mock_result)

        assert usage_info == {}

    def test_extract_usage_info_with_partial_fields(self) -> None:
        """MIX-001: _extract_usage_info handles partial usage data."""
        agent = ConcreteAgentWithMixin()

        # Create mock result with partial usage
        mock_usage = MagicMock(spec=["total_tokens"])
        mock_usage.total_tokens = 50

        mock_result = MagicMock()
        mock_result.usage.return_value = mock_usage

        usage_info = agent._extract_usage_info(mock_result)

        assert usage_info["total_tokens"] == 50
        assert usage_info["prompt_tokens"] is None
        assert usage_info["completion_tokens"] is None


class TestExecutePydanticAgent:
    """Tests for _execute_pydantic_agent method (MIX-002 to MIX-005)."""

    @pytest.mark.asyncio
    async def test_execute_validates_empty_task(self) -> None:
        """MIX-002: _execute_pydantic_agent rejects empty task."""
        agent = ConcreteAgentWithMixin()
        agent._logger.log_execution_start.return_value = "exec-123"

        result = await agent._execute_pydantic_agent("   ")

        assert result.status == ResultStatus.ERROR
        assert result.error_code == "EMPTY_TASK"
        assert result.error_message is not None
        assert "empty" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_logs_execution_start(self) -> None:
        """MIX-003: _execute_pydantic_agent logs execution start."""
        agent = ConcreteAgentWithMixin()
        agent._logger.log_execution_start.return_value = "exec-123"

        # Setup mock agent.run() to return a result
        mock_result = MagicMock()
        mock_result.output = "test output"
        mock_result.all_messages.return_value = []
        agent._mock_agent.run = AsyncMock(return_value=mock_result)

        await agent._execute_pydantic_agent("test task", context={"key": "value"})

        agent._logger.log_execution_start.assert_called_once()
        call_kwargs = agent._logger.log_execution_start.call_args
        assert call_kwargs.kwargs["agent_name"] == "test_agent"
        assert call_kwargs.kwargs["task"] == "test task"
        assert call_kwargs.kwargs["context"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_execute_calls_build_agent_metadata(self) -> None:
        """MIX-004: _execute_pydantic_agent calls _build_agent_metadata."""
        agent = ConcreteAgentWithMixin()
        agent._logger.log_execution_start.return_value = "exec-123"

        mock_result = MagicMock()
        mock_result.output = "test output"
        mock_result.all_messages.return_value = []
        agent._mock_agent.run = AsyncMock(return_value=mock_result)

        # Spy on _build_agent_metadata
        with patch.object(
            agent, "_build_agent_metadata", wraps=agent._build_agent_metadata
        ) as spy:
            result = await agent._execute_pydantic_agent("test task")

            spy.assert_called_once_with(None)
            assert result.metadata is not None
            assert result.metadata["test_field"] == "test_value"

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self) -> None:
        """MIX-005: _execute_pydantic_agent delegates to _handle_execution_error."""
        agent = ConcreteAgentWithMixin()
        agent._logger.log_execution_start.return_value = "exec-123"

        # Setup mock agent.run() to raise an exception
        agent._mock_agent.run = AsyncMock(side_effect=ValueError("Test error"))

        result = await agent._execute_pydantic_agent("test task")

        assert result.status == ResultStatus.ERROR
        assert result.error_code == "TEST_ERROR"
        assert result.error_message is not None
        assert "Test error" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_returns_success_result(self) -> None:
        """Execute returns success result with all fields populated."""
        agent = ConcreteAgentWithMixin()
        agent._logger.log_execution_start.return_value = "exec-123"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 50
        mock_usage.prompt_tokens = 30
        mock_usage.completion_tokens = 20
        mock_usage.requests = 1

        mock_result = MagicMock()
        mock_result.output = "Hello, world!"
        # Return empty list to avoid validation issues with message format
        mock_result.all_messages.return_value = []
        mock_result.usage.return_value = mock_usage
        agent._mock_agent.run = AsyncMock(return_value=mock_result)

        result = await agent._execute_pydantic_agent("say hello")

        assert result.status == ResultStatus.SUCCESS
        assert result.content == "Hello, world!"
        assert result.agent_name == "test_agent"
        assert result.agent_type == "test"
        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 0
        assert result.usage_info is not None
        assert result.usage_info["total_tokens"] == 50

    @pytest.mark.asyncio
    async def test_execute_logs_completion(self) -> None:
        """Execute logs completion after successful execution."""
        agent = ConcreteAgentWithMixin()
        agent._logger.log_execution_start.return_value = "exec-123"

        mock_result = MagicMock()
        mock_result.output = "done"
        mock_result.all_messages.return_value = []
        agent._mock_agent.run = AsyncMock(return_value=mock_result)

        await agent._execute_pydantic_agent("test")

        agent._logger.log_execution_complete.assert_called_once()
        call_args = agent._logger.log_execution_complete.call_args
        assert call_args.kwargs["execution_id"] == "exec-123"
