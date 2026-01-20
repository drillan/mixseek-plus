"""Unit tests for GroqTavilySearchAgent.

Tests for T025:
- Test agent inherits BaseGroqAgent and TavilyToolsRepositoryMixin
- Test _create_tavily_client() returns TavilyAPIClient with env API key
- Test _create_deps() returns TavilySearchDeps
- Test _get_agent_type_metadata() returns correct type info
- Test agent registers 3 Tavily tools

NOTE: Tests use type="custom" to bypass MemberAgentConfig's model prefix validation.
This is needed because Pydantic v2 compiles validators at class definition time,
making runtime patching of validators ineffective. The "custom" type allows
any model prefix including 'groq:'.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from mixseek.models.member_agent import MemberAgentConfig

from mixseek_plus.agents.base_groq_agent import BaseGroqAgent
from mixseek_plus.agents.groq_tavily_search_agent import GroqTavilySearchAgent
from mixseek_plus.agents.mixins.tavily_tools import (
    TavilySearchDeps,
    TavilyToolsRepositoryMixin,
)
from mixseek_plus.providers.tavily_client import TavilyAPIClient


class TestGroqTavilySearchAgentInheritance:
    """Tests for GroqTavilySearchAgent class inheritance."""

    def test_inherits_from_base_groq_agent(self) -> None:
        """Agent inherits from BaseGroqAgent."""
        assert issubclass(GroqTavilySearchAgent, BaseGroqAgent)

    def test_inherits_from_tavily_tools_mixin(self) -> None:
        """Agent inherits from TavilyToolsRepositoryMixin."""
        assert issubclass(GroqTavilySearchAgent, TavilyToolsRepositoryMixin)


class TestGroqTavilySearchAgentInitialization:
    """Tests for GroqTavilySearchAgent initialization."""

    def test_creates_tavily_client_from_env(
        self,
        mock_groq_api_key: str,
    ) -> None:
        """_create_tavily_client() returns TavilyAPIClient with env API key."""
        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",  # Use custom type to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful research assistant.",
        )

        agent = GroqTavilySearchAgent(config)

        # Verify TavilyAPIClient was created
        assert hasattr(agent, "_tavily_client")
        assert isinstance(agent._tavily_client, TavilyAPIClient)
        # mock_groq_api_key fixture also sets TAVILY_API_KEY
        assert agent._tavily_client.api_key == "tvly-test_api_key_1234567890"

    def test_registers_tavily_tools_on_init(
        self,
        mock_groq_api_key: str,
    ) -> None:
        """Agent registers 3 Tavily tools during initialization."""
        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",  # Use custom type to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful research assistant.",
        )

        agent = GroqTavilySearchAgent(config)

        # Verify _tavily_tools was set
        assert hasattr(agent, "_tavily_tools")
        assert len(agent._tavily_tools) == 3

        # Verify tool names
        tool_names = [t.__name__ for t in agent._tavily_tools]
        assert "tavily_search" in tool_names
        assert "tavily_extract" in tool_names
        assert "tavily_context" in tool_names


class TestGroqTavilySearchAgentCreateDeps:
    """Tests for GroqTavilySearchAgent._create_deps()."""

    def test_create_deps_returns_tavily_search_deps(
        self,
        mock_groq_api_key: str,
    ) -> None:
        """_create_deps() returns TavilySearchDeps."""
        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",  # Use custom type to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful research assistant.",
        )

        agent = GroqTavilySearchAgent(config)
        deps = agent._create_deps()

        assert isinstance(deps, TavilySearchDeps)
        assert deps.config == config
        assert deps.tavily_client == agent._tavily_client


class TestGroqTavilySearchAgentMetadata:
    """Tests for GroqTavilySearchAgent._get_agent_type_metadata()."""

    def test_get_agent_type_metadata_returns_correct_info(
        self,
        mock_groq_api_key: str,
    ) -> None:
        """_get_agent_type_metadata() returns correct type info."""
        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",  # Use custom type to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful research assistant.",
        )

        agent = GroqTavilySearchAgent(config)
        metadata = agent._get_agent_type_metadata()

        assert metadata["agent_type"] == "tavily_search"


class TestGroqTavilySearchAgentValidation:
    """Tests for GroqTavilySearchAgent validation and error handling."""

    def test_raises_value_error_without_tavily_api_key(
        self,
        mock_groq_api_key: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Agent raises ValueError if TAVILY_API_KEY is missing."""
        # Remove TAVILY_API_KEY that was set by mock_groq_api_key fixture
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",  # Use custom type to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful research assistant.",
        )

        with pytest.raises(ValueError) as exc_info:
            GroqTavilySearchAgent(config)

        assert "Tavily" in str(exc_info.value)

    def test_raises_value_error_without_groq_api_key(
        self,
        clear_groq_api_key: None,
    ) -> None:
        """Agent raises ValueError if GROQ_API_KEY is missing."""
        config = MemberAgentConfig(
            name="test-tavily-agent",
            type="custom",  # Use custom type to bypass model prefix validation
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful research assistant.",
        )

        # Patch validate_tavily_credentials to not fail on Tavily side
        with patch(
            "mixseek_plus.agents.groq_tavily_search_agent.validate_tavily_credentials"
        ):
            with pytest.raises(ValueError) as exc_info:
                GroqTavilySearchAgent(config)

        assert "Model creation failed" in str(exc_info.value)
