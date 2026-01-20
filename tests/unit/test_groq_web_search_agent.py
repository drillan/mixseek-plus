"""Unit tests for GroqWebSearchAgent.

Tests cover:
- GR-051: GroqWebSearchAgent existence and Web Search capability
- GR-052: BaseMemberAgent interface implementation
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mixseek.models.member_agent import (
    MemberAgentConfig,
    MemberAgentResult,
    ResultStatus,
)


class TestGroqWebSearchAgentInitialization:
    """Tests for GroqWebSearchAgent initialization."""

    def test_inherits_from_base_member_agent(self, mock_groq_api_key: str) -> None:
        """GR-052: GroqWebSearchAgent should inherit from BaseMemberAgent."""
        from mixseek.agents.member.base import BaseMemberAgent

        from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a web search assistant.",
        )

        agent = GroqWebSearchAgent(config)

        assert isinstance(agent, BaseMemberAgent)

    def test_creates_agent_with_valid_config(self, mock_groq_api_key: str) -> None:
        """GR-051: GroqWebSearchAgent should be creatable with valid config."""
        from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

        config = MemberAgentConfig(
            name="test-web-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a web search assistant.",
        )

        agent = GroqWebSearchAgent(config)

        assert agent.agent_name == "test-web-agent"
        assert agent.config.model == "groq:llama-3.3-70b-versatile"

    def test_has_web_search_tool(self, mock_groq_api_key: str) -> None:
        """GR-051: GroqWebSearchAgent should have WebSearchTool configured."""
        from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

        config = MemberAgentConfig(
            name="test-web-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a web search assistant.",
        )

        agent = GroqWebSearchAgent(config)

        # Check that agent has tools configured
        assert agent._agent is not None
        # The agent should have the web_search tool registered
        # We verify by checking _function_toolset has tools
        assert hasattr(agent._agent, "_function_toolset")
        assert len(agent._agent._function_toolset.tools) > 0

    def test_raises_value_error_for_missing_tavily_api_key(
        self, mock_groq_api_key: str
    ) -> None:
        """Should raise ValueError when TAVILY_API_KEY is missing."""
        from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

        # Ensure TAVILY_API_KEY is not set
        import os

        os.environ.pop("TAVILY_API_KEY", None)

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a web search assistant.",
        )

        with pytest.raises(ValueError, match="Tavily credential validation failed"):
            GroqWebSearchAgent(config)

    def test_raises_value_error_for_missing_groq_api_key(
        self, clear_groq_api_key: None
    ) -> None:
        """Should raise ValueError when GROQ_API_KEY is missing."""
        import os

        from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

        # Set valid TAVILY_API_KEY but no GROQ_API_KEY
        os.environ["TAVILY_API_KEY"] = "tvly-test123"

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a web search assistant.",
        )

        try:
            with pytest.raises(ValueError, match="Model creation failed"):
                GroqWebSearchAgent(config)
        finally:
            os.environ.pop("TAVILY_API_KEY", None)


class TestGroqWebSearchAgentExecute:
    """Tests for GroqWebSearchAgent.execute() method."""

    @pytest.mark.asyncio
    async def test_returns_member_agent_result(self, mock_groq_api_key: str) -> None:
        """GR-052: execute() should return MemberAgentResult."""
        from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

        config = MemberAgentConfig(
            name="test-web-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a web search assistant.",
        )

        agent = GroqWebSearchAgent(config)

        mock_result = MagicMock()
        mock_result.output = "Web search result"
        mock_result.all_messages.return_value = []

        with patch.object(agent._agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result
            result = await agent.execute("Search for Python tutorials")

        assert isinstance(result, MemberAgentResult)
        assert result.status == ResultStatus.SUCCESS
        assert result.content == "Web search result"

    @pytest.mark.asyncio
    async def test_returns_error_for_empty_task(self, mock_groq_api_key: str) -> None:
        """Empty task should return error result."""
        from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

        config = MemberAgentConfig(
            name="test-web-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a web search assistant.",
        )

        agent = GroqWebSearchAgent(config)
        result = await agent.execute("")

        assert result.status == ResultStatus.ERROR
        assert result.error_code == "EMPTY_TASK"

    @pytest.mark.asyncio
    async def test_handles_api_error(self, mock_groq_api_key: str) -> None:
        """API errors should be wrapped in error result."""
        from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

        config = MemberAgentConfig(
            name="test-web-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a web search assistant.",
        )

        agent = GroqWebSearchAgent(config)

        with patch.object(agent._agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = Exception("API Error: Service unavailable")
            result = await agent.execute("Search for something")

        assert result.status == ResultStatus.ERROR
        assert result.error_code == "RUNTIME_ERROR"
        assert result.error_message is not None
        assert "Service unavailable" in result.error_message
