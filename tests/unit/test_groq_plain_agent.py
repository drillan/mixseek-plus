"""Unit tests for GroqPlainAgent.

Tests cover:
- GR-050: GroqPlainAgent existence and BaseMemberAgent inheritance
- GR-052: BaseMemberAgent interface implementation
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mixseek.models.member_agent import (
    MemberAgentConfig,
    MemberAgentResult,
    ResultStatus,
)

from mixseek_plus.agents.groq_agent import GroqAgentDeps, GroqPlainAgent


class TestGroqPlainAgentInitialization:
    """Tests for GroqPlainAgent initialization."""

    def test_inherits_from_base_member_agent(self, mock_groq_api_key: str) -> None:
        """GR-052: GroqPlainAgent should inherit from BaseMemberAgent."""
        from mixseek.agents.member.base import BaseMemberAgent

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
        )

        agent = GroqPlainAgent(config)

        assert isinstance(agent, BaseMemberAgent)

    def test_creates_agent_with_valid_config(self, mock_groq_api_key: str) -> None:
        """GR-050: GroqPlainAgent should be creatable with valid config."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
        )

        agent = GroqPlainAgent(config)

        assert agent.agent_name == "test-agent"
        assert agent.config.model == "groq:llama-3.3-70b-versatile"

    def test_creates_agent_with_all_settings(self, mock_groq_api_key: str) -> None:
        """Agent should support all MemberAgentConfig settings."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
            temperature=0.7,
            max_tokens=1024,
            top_p=0.9,
            seed=42,
            max_retries=3,
            timeout_seconds=30,
            stop_sequences=["STOP"],
        )

        agent = GroqPlainAgent(config)

        assert agent.config.temperature == 0.7
        assert agent.config.max_tokens == 1024

    def test_raises_value_error_for_invalid_api_key(
        self, clear_groq_api_key: None
    ) -> None:
        """Should raise ValueError when API key is missing."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
        )

        with pytest.raises(ValueError, match="Model creation failed"):
            GroqPlainAgent(config)

    def test_accepts_system_prompt(self, mock_groq_api_key: str) -> None:
        """Agent should accept optional system_prompt in addition to system_instruction."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="Base instructions",
            system_prompt="Dynamic system prompt",
        )

        agent = GroqPlainAgent(config)

        assert agent.config.system_prompt == "Dynamic system prompt"


class TestGroqPlainAgentExecute:
    """Tests for GroqPlainAgent.execute() method."""

    @pytest.mark.asyncio
    async def test_returns_member_agent_result(self, mock_groq_api_key: str) -> None:
        """GR-052: execute() should return MemberAgentResult."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
        )

        agent = GroqPlainAgent(config)

        # Mock the pydantic-ai agent run
        mock_result = MagicMock()
        mock_result.output = "Test response"
        mock_result.all_messages.return_value = []

        with patch.object(agent._agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result
            result = await agent.execute("Hello")

        assert isinstance(result, MemberAgentResult)
        assert result.status == ResultStatus.SUCCESS
        assert result.content == "Test response"

    @pytest.mark.asyncio
    async def test_returns_error_for_empty_task(self, mock_groq_api_key: str) -> None:
        """Empty task should return error result."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
        )

        agent = GroqPlainAgent(config)
        result = await agent.execute("")

        assert result.status == ResultStatus.ERROR
        assert result.error_code == "EMPTY_TASK"

    @pytest.mark.asyncio
    async def test_returns_error_for_whitespace_task(
        self, mock_groq_api_key: str
    ) -> None:
        """Whitespace-only task should return error result."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
        )

        agent = GroqPlainAgent(config)
        result = await agent.execute("   \n\t  ")

        assert result.status == ResultStatus.ERROR
        assert result.error_code == "EMPTY_TASK"

    @pytest.mark.asyncio
    async def test_includes_usage_info_when_available(
        self, mock_groq_api_key: str
    ) -> None:
        """Result should include usage info when API returns it."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
        )

        agent = GroqPlainAgent(config)

        mock_usage = MagicMock()
        mock_usage.total_tokens = 100
        mock_usage.prompt_tokens = 20
        mock_usage.completion_tokens = 80
        mock_usage.requests = 1

        mock_result = MagicMock()
        mock_result.output = "Test response"
        mock_result.all_messages.return_value = []
        mock_result.usage.return_value = mock_usage

        with patch.object(agent._agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result
            result = await agent.execute("Hello")

        assert result.usage_info is not None
        assert result.usage_info["total_tokens"] == 100

    @pytest.mark.asyncio
    async def test_handles_api_error(self, mock_groq_api_key: str) -> None:
        """API errors should be wrapped in error result."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
        )

        agent = GroqPlainAgent(config)

        with patch.object(agent._agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = Exception("API Error: Rate limit exceeded")
            result = await agent.execute("Hello")

        assert result.status == ResultStatus.ERROR
        assert result.error_code == "EXECUTION_ERROR"
        assert result.error_message is not None
        assert "Rate limit exceeded" in result.error_message

    @pytest.mark.asyncio
    async def test_handles_incomplete_tool_call(self, mock_groq_api_key: str) -> None:
        """IncompleteToolCall should be handled with specific error code."""
        from pydantic_ai import IncompleteToolCall

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
        )

        agent = GroqPlainAgent(config)

        with patch.object(agent._agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = IncompleteToolCall("Token limit reached")
            result = await agent.execute("Hello")

        assert result.status == ResultStatus.ERROR
        assert result.error_code == "TOKEN_LIMIT_EXCEEDED"


class TestGroqAgentDeps:
    """Tests for GroqAgentDeps dataclass."""

    def test_holds_config(self) -> None:
        """GroqAgentDeps should hold MemberAgentConfig."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
        )

        deps = GroqAgentDeps(config=config)

        assert deps.config == config
        assert deps.config.name == "test-agent"
