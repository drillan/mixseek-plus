"""Unit tests for ClaudeCodeTavilySearchAgent.

Tests for T031-T034:
- T031: Test agent inherits BaseClaudeCodeAgent and TavilyToolsRepositoryMixin
        Test _create_tavily_client() returns TavilyAPIClient with env API key
        Test _create_deps() returns TavilySearchDeps
        Test _get_agent_type_metadata() returns correct type info
        Test agent registers 3 Tavily tools
- T032: Test MCP tool naming convention (mcp__pydantic_tools__tavily_*)
- T033: Test _wrap_tool_for_mcp() injects TavilySearchDeps correctly
- T034: Test allowed_tools includes MCP tool names

NOTE: Tests use type="custom" to bypass MemberAgentConfig's model prefix validation.
This is needed because Pydantic v2 compiles validators at class definition time,
making runtime patching of validators ineffective. The "custom" type allows
any model prefix including 'claudecode:'.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from mixseek.models.member_agent import MemberAgentConfig

if TYPE_CHECKING:
    pass


class TestClaudeCodeTavilySearchAgentInheritance:
    """Tests for ClaudeCodeTavilySearchAgent class inheritance (T031)."""

    def test_inherits_from_base_claudecode_agent(self) -> None:
        """Agent inherits from BaseClaudeCodeAgent."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )

        assert issubclass(ClaudeCodeTavilySearchAgent, BaseClaudeCodeAgent)

    def test_inherits_from_tavily_tools_mixin(self) -> None:
        """Agent inherits from TavilyToolsRepositoryMixin."""
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )
        from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin

        assert issubclass(ClaudeCodeTavilySearchAgent, TavilyToolsRepositoryMixin)


class TestClaudeCodeTavilySearchAgentInitialization:
    """Tests for ClaudeCodeTavilySearchAgent initialization (T031)."""

    def test_creates_tavily_client_from_env(
        self,
        mock_tavily_api_key: str,
    ) -> None:
        """_create_tavily_client() returns TavilyAPIClient with env API key."""
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )
        from mixseek_plus.providers.tavily_client import TavilyAPIClient

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",  # Use custom type to bypass model prefix validation
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful research assistant.",
        )

        agent = ClaudeCodeTavilySearchAgent(config)

        # Verify TavilyAPIClient was created
        assert hasattr(agent, "_tavily_client")
        assert isinstance(agent._tavily_client, TavilyAPIClient)
        # mock_tavily_api_key fixture sets TAVILY_API_KEY
        assert agent._tavily_client.api_key == "tvly-test_api_key_1234567890"

    def test_registers_tavily_tools_on_init(
        self,
        mock_tavily_api_key: str,
    ) -> None:
        """Agent registers 3 Tavily tools during initialization."""
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",  # Use custom type to bypass model prefix validation
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful research assistant.",
        )

        agent = ClaudeCodeTavilySearchAgent(config)

        # Verify _tavily_tools was set
        assert hasattr(agent, "_tavily_tools")
        assert len(agent._tavily_tools) == 3

        # Verify tool names
        tool_names = [t.__name__ for t in agent._tavily_tools]
        assert "tavily_search" in tool_names
        assert "tavily_extract" in tool_names
        assert "tavily_context" in tool_names


class TestClaudeCodeTavilySearchAgentCreateDeps:
    """Tests for ClaudeCodeTavilySearchAgent._create_deps() (T031)."""

    def test_create_deps_returns_tavily_search_deps(
        self,
        mock_tavily_api_key: str,
    ) -> None:
        """_create_deps() returns TavilySearchDeps."""
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )
        from mixseek_plus.agents.mixins.tavily_tools import TavilySearchDeps

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",  # Use custom type to bypass model prefix validation
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful research assistant.",
        )

        agent = ClaudeCodeTavilySearchAgent(config)
        deps = agent._create_deps()

        assert isinstance(deps, TavilySearchDeps)
        assert deps.config == config
        assert deps.tavily_client == agent._tavily_client


class TestClaudeCodeTavilySearchAgentMetadata:
    """Tests for ClaudeCodeTavilySearchAgent._get_agent_type_metadata() (T031)."""

    def test_get_agent_type_metadata_returns_correct_info(
        self,
        mock_tavily_api_key: str,
    ) -> None:
        """_get_agent_type_metadata() returns correct type info."""
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",  # Use custom type to bypass model prefix validation
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful research assistant.",
        )

        agent = ClaudeCodeTavilySearchAgent(config)
        metadata = agent._get_agent_type_metadata()

        assert metadata["agent_type"] == "claudecode_tavily_search"


class TestClaudeCodeTavilySearchAgentMCPNaming:
    """Tests for MCP tool naming convention (T032)."""

    def test_mcp_tool_names_follow_convention(
        self,
        mock_tavily_api_key: str,
    ) -> None:
        """MCP tools follow naming convention: mcp__pydantic_tools__tavily_*."""
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful research assistant.",
        )

        agent = ClaudeCodeTavilySearchAgent(config)

        # Get MCP tool names
        mcp_tool_names = agent._get_mcp_tool_names()

        expected_names = [
            "mcp__pydantic_tools__tavily_search",
            "mcp__pydantic_tools__tavily_extract",
            "mcp__pydantic_tools__tavily_context",
        ]

        assert set(mcp_tool_names) == set(expected_names)


class TestClaudeCodeTavilySearchAgentWrapTool:
    """Tests for _wrap_tool_for_mcp() deps injection (T033)."""

    @pytest.mark.asyncio
    async def test_wrap_tool_for_mcp_injects_deps(
        self,
        mock_tavily_api_key: str,
    ) -> None:
        """_wrap_tool_for_mcp() injects TavilySearchDeps correctly."""
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )
        from mixseek_plus.providers.tavily_client import (
            TavilySearchResult,
            TavilySearchResultItem,
        )

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful research assistant.",
        )

        agent = ClaudeCodeTavilySearchAgent(config)

        # Mock the tavily client's search method
        mock_result = TavilySearchResult(
            query="test query",
            results=[
                TavilySearchResultItem(
                    title="Test Result",
                    url="https://example.com",
                    content="Test content",
                    score=0.95,
                )
            ],
            response_time=1.5,
        )
        # Use object.__setattr__ to bypass method assignment restriction
        object.__setattr__(
            agent._tavily_client, "search", AsyncMock(return_value=mock_result)
        )

        # Get wrapped tool
        wrapped_tools = agent._get_wrapped_mcp_tools()
        tavily_search_wrapped = None
        for name, tool_fn in wrapped_tools.items():
            if "tavily_search" in name:
                tavily_search_wrapped = tool_fn
                break

        assert tavily_search_wrapped is not None

        # Call the wrapped tool - it should work without passing deps
        result = await tavily_search_wrapped(
            query="test query",
            search_depth="basic",
            max_results=5,
        )

        # Verify the result contains expected output
        assert "検索結果: test query" in result
        assert "Test Result" in result


class TestClaudeCodeTavilySearchAgentAllowedTools:
    """Tests for allowed_tools including MCP tool names (T034)."""

    def test_allowed_tools_includes_mcp_tool_names(
        self,
        mock_tavily_api_key: str,
    ) -> None:
        """allowed_tools includes MCP tool names for ClaudeCode model."""
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful research assistant.",
        )

        agent = ClaudeCodeTavilySearchAgent(config)

        # Get the tool settings that would be passed to the model
        tool_names = agent._get_mcp_tool_names()

        # Verify all three MCP tool names are present
        assert "mcp__pydantic_tools__tavily_search" in tool_names
        assert "mcp__pydantic_tools__tavily_extract" in tool_names
        assert "mcp__pydantic_tools__tavily_context" in tool_names


class TestClaudeCodeTavilySearchAgentValidation:
    """Tests for ClaudeCodeTavilySearchAgent validation and error handling."""

    def test_raises_value_error_without_tavily_api_key(
        self,
        clear_tavily_api_key: None,
    ) -> None:
        """Agent raises ValueError if TAVILY_API_KEY is missing."""
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",  # Use custom type to bypass model prefix validation
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful research assistant.",
        )

        with pytest.raises(ValueError) as exc_info:
            ClaudeCodeTavilySearchAgent(config)

        assert "Tavily" in str(exc_info.value)


class TestClaudeCodeTavilySearchAgentToolsetRegistration:
    """Tests for ClaudeCodeModel toolset registration."""

    def test_has_register_toolsets_method(
        self,
        mock_tavily_api_key: str,
    ) -> None:
        """Agent has _register_toolsets_if_claudecode method."""
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful research assistant.",
        )

        agent = ClaudeCodeTavilySearchAgent(config)

        # Verify the method exists
        assert hasattr(agent, "_register_toolsets_if_claudecode")
        assert callable(agent._register_toolsets_if_claudecode)

    def test_calls_set_agent_toolsets_for_claudecode_model(
        self,
        mock_tavily_api_key: str,
    ) -> None:
        """set_agent_toolsets() is called when using ClaudeCodeModel."""

        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful research assistant.",
        )

        agent = ClaudeCodeTavilySearchAgent(config)

        # Verify that the model has set_agent_toolsets method called
        # Since ClaudeCodeModel is used, set_agent_toolsets should have been called
        # We verify this by checking that the model instance is ClaudeCodeModel
        from claudecode_model import ClaudeCodeModel

        assert isinstance(agent._model, ClaudeCodeModel)

        # The toolsets should be registered (can be verified via internal state)
        # We check that _agent_toolsets is not empty on the model
        toolsets = getattr(agent._model, "_agent_toolsets", None)
        assert toolsets is not None
        assert len(toolsets) == 3  # 3 Tavily tools

    def test_adds_mcp_tool_names_to_allowed_tools(
        self,
        mock_tavily_api_key: str,
    ) -> None:
        """MCP tool names are added to model's allowed_tools."""
        from mixseek_plus.agents.claudecode_tavily_search_agent import (
            ClaudeCodeTavilySearchAgent,
        )

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful research assistant.",
        )

        agent = ClaudeCodeTavilySearchAgent(config)

        # Verify allowed_tools was updated with MCP tool names
        assert agent._model._allowed_tools is not None
        assert len(agent._model._allowed_tools) >= 3

        # Check MCP naming convention
        mcp_tool_names = [
            t
            for t in agent._model._allowed_tools
            if t.startswith("mcp__pydantic_tools__tavily_")
        ]
        assert len(mcp_tool_names) == 3
        assert "mcp__pydantic_tools__tavily_search" in mcp_tool_names
        assert "mcp__pydantic_tools__tavily_extract" in mcp_tool_names
        assert "mcp__pydantic_tools__tavily_context" in mcp_tool_names

    def test_skips_registration_for_non_claudecode_model(
        self,
        mock_groq_api_key: str,
    ) -> None:
        """No registration happens for non-ClaudeCode models (Groq model)."""
        from mixseek_plus.agents.groq_tavily_search_agent import GroqTavilySearchAgent

        config = MemberAgentConfig(
            name="test-groq-tavily-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful research assistant.",
        )

        # Create a Groq agent - it should not have set_agent_toolsets
        agent = GroqTavilySearchAgent(config)

        # Verify model does not have set_agent_toolsets (it's not ClaudeCodeModel)
        assert not hasattr(agent._model, "set_agent_toolsets")
