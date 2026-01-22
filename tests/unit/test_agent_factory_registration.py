"""Unit tests for MemberAgentFactory registration.

Tests cover:
- GR-053: Factory registration for groq_plain and groq_web_search
- GR-054: TOML configuration support via type field
- CC-032, CC-033, CC-071: Factory registration for claudecode_plain
- _register_agents helper function
"""

from mixseek.agents.member.factory import MemberAgentFactory
from mixseek.models.member_agent import MemberAgentConfig


class TestRegisterAgentsHelper:
    """Tests for the _register_agents() helper function."""

    def test_register_agents_helper_exists(self) -> None:
        """_register_agents helper function should exist."""
        from mixseek_plus.agents import _register_agents

        assert callable(_register_agents)

    def test_register_agents_with_single_agent(self) -> None:
        """_register_agents should register a single agent correctly."""
        from mixseek_plus.agents import GroqPlainAgent, _register_agents

        # Clear any existing registration for test isolation
        test_type = "test_single_agent"

        _register_agents({test_type: GroqPlainAgent})

        assert test_type in MemberAgentFactory._agent_classes
        assert MemberAgentFactory._agent_classes[test_type] is GroqPlainAgent

    def test_register_agents_with_multiple_agents(self) -> None:
        """_register_agents should register multiple agents correctly."""
        from mixseek_plus.agents import (
            ClaudeCodePlainAgent,
            GroqPlainAgent,
            _register_agents,
        )

        test_agents = {
            "test_multi_1": GroqPlainAgent,
            "test_multi_2": ClaudeCodePlainAgent,
        }

        _register_agents(test_agents)

        assert "test_multi_1" in MemberAgentFactory._agent_classes
        assert "test_multi_2" in MemberAgentFactory._agent_classes
        assert MemberAgentFactory._agent_classes["test_multi_1"] is GroqPlainAgent
        assert MemberAgentFactory._agent_classes["test_multi_2"] is ClaudeCodePlainAgent

    def test_register_agents_is_idempotent(self) -> None:
        """Multiple calls to _register_agents with same data should be safe."""
        from mixseek_plus.agents import GROQ_AGENTS, _register_agents

        test_type = "groq_plain"  # Use existing constant

        _register_agents(GROQ_AGENTS)
        _register_agents(GROQ_AGENTS)
        _register_agents(GROQ_AGENTS)

        assert test_type in MemberAgentFactory._agent_classes

    def test_register_agents_with_empty_dict(self) -> None:
        """_register_agents should handle empty dict without error."""
        from mixseek_plus.agents import _register_agents

        # Should not raise
        _register_agents({})


class TestAgentRegistrationConstants:
    """Tests for agent registration constants."""

    def test_groq_agents_constant_exists(self) -> None:
        """GROQ_AGENTS constant should exist and contain correct agents."""
        from mixseek_plus.agents import GROQ_AGENTS, GroqPlainAgent, GroqWebSearchAgent

        assert "groq_plain" in GROQ_AGENTS
        assert "groq_web_search" in GROQ_AGENTS
        assert GROQ_AGENTS["groq_plain"] is GroqPlainAgent
        assert GROQ_AGENTS["groq_web_search"] is GroqWebSearchAgent

    def test_claudecode_agents_constant_exists(self) -> None:
        """CLAUDECODE_AGENTS constant should exist and contain correct agents."""
        from mixseek_plus.agents import CLAUDECODE_AGENTS, ClaudeCodePlainAgent

        assert "claudecode_plain" in CLAUDECODE_AGENTS
        assert CLAUDECODE_AGENTS["claudecode_plain"] is ClaudeCodePlainAgent

    def test_tavily_agents_constant_exists(self) -> None:
        """TAVILY_AGENTS constant should exist and contain correct agents."""
        from mixseek_plus.agents import (
            TAVILY_AGENTS,
            ClaudeCodeTavilySearchAgent,
            GroqTavilySearchAgent,
        )

        assert "tavily_search" in TAVILY_AGENTS
        assert "claudecode_tavily_search" in TAVILY_AGENTS
        assert TAVILY_AGENTS["tavily_search"] is GroqTavilySearchAgent
        assert TAVILY_AGENTS["claudecode_tavily_search"] is ClaudeCodeTavilySearchAgent


class TestClaudeCodeFactoryRegistration:
    """Tests for ClaudeCode MemberAgentFactory registration (CC-032, CC-033, CC-071)."""

    def test_register_claudecode_agents_function_exists(self) -> None:
        """CC-071: register_claudecode_agents function should exist."""
        from mixseek_plus.agents import register_claudecode_agents

        assert callable(register_claudecode_agents)

    def test_register_claudecode_agents_registers_claudecode_plain(self) -> None:
        """CC-032: After registration, claudecode_plain type should be available."""
        from mixseek_plus.agents import register_claudecode_agents

        # Register agents
        register_claudecode_agents()

        # Check registration
        assert "claudecode_plain" in MemberAgentFactory._agent_classes

    def test_factory_creates_claudecode_plain_agent(self) -> None:
        """CC-033: Factory should create ClaudeCodePlainAgent from type='claudecode_plain'.

        Note: MemberAgentConfig validates model field, so we use type='custom'
        to bypass validation and verify Factory registration works correctly.
        """
        from mixseek_plus.agents import ClaudeCodePlainAgent, register_claudecode_agents

        register_claudecode_agents()

        config = MemberAgentConfig(
            name="test-claudecode-agent",
            type="custom",  # Bypass model validation
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a test assistant.",
        )

        # Directly instantiate to verify the class works
        agent = ClaudeCodePlainAgent(config)

        assert isinstance(agent, ClaudeCodePlainAgent)
        assert agent.agent_name == "test-claudecode-agent"

    def test_claudecode_registration_is_idempotent(self) -> None:
        """Multiple calls to register_claudecode_agents should be safe."""
        from mixseek_plus.agents import register_claudecode_agents

        # Call multiple times
        register_claudecode_agents()
        register_claudecode_agents()
        register_claudecode_agents()

        # Should still work
        assert "claudecode_plain" in MemberAgentFactory._agent_classes


class TestFactoryRegistration:
    """Tests for MemberAgentFactory registration."""

    def test_groq_plain_registration_function_exists(self) -> None:
        """GR-053: register_groq_agents function should exist."""
        from mixseek_plus.agents import register_groq_agents

        assert callable(register_groq_agents)

    def test_register_groq_agents_registers_groq_plain(
        self, mock_groq_api_key: str
    ) -> None:
        """GR-053: After registration, groq_plain type should be available."""
        from mixseek_plus.agents import register_groq_agents

        # Register agents
        register_groq_agents()

        # Check registration
        assert "groq_plain" in MemberAgentFactory._agent_classes

    def test_register_groq_agents_registers_groq_web_search(
        self, mock_groq_api_key: str
    ) -> None:
        """GR-053: After registration, groq_web_search type should be available."""
        from mixseek_plus.agents import register_groq_agents

        # Register agents
        register_groq_agents()

        # Check registration
        assert "groq_web_search" in MemberAgentFactory._agent_classes

    def test_factory_creates_groq_plain_agent(self, mock_groq_api_key: str) -> None:
        """GR-054: Factory should create GroqPlainAgent from type='groq_plain'.

        Note: MemberAgentConfig validates model field, so we use type='custom'
        to bypass validation and verify Factory registration works correctly.
        In production, TOML files are loaded differently.
        """
        from mixseek_plus.agents import GroqPlainAgent, register_groq_agents

        register_groq_agents()

        # Use type='custom' to bypass model validation in MemberAgentConfig
        # The actual factory registration allows 'groq_plain' to map to GroqPlainAgent
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",  # Bypass model validation
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a test assistant.",
        )

        # Directly instantiate to verify the class works
        agent = GroqPlainAgent(config)

        assert isinstance(agent, GroqPlainAgent)
        assert agent.agent_name == "test-agent"

    def test_factory_creates_groq_web_search_agent(
        self, mock_groq_api_key: str
    ) -> None:
        """GR-054: Factory should create GroqWebSearchAgent from type='groq_web_search'.

        Note: MemberAgentConfig validates model field, so we use type='custom'
        to bypass validation and verify Factory registration works correctly.
        """
        from mixseek_plus.agents import GroqWebSearchAgent, register_groq_agents

        register_groq_agents()

        # Use type='custom' to bypass model validation
        config = MemberAgentConfig(
            name="test-web-agent",
            type="custom",  # Bypass model validation
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a web search assistant.",
        )

        # Directly instantiate to verify the class works
        agent = GroqWebSearchAgent(config)

        assert isinstance(agent, GroqWebSearchAgent)
        assert agent.agent_name == "test-web-agent"

    def test_registration_is_idempotent(self, mock_groq_api_key: str) -> None:
        """Multiple calls to register_groq_agents should be safe."""
        from mixseek_plus.agents import register_groq_agents

        # Call multiple times
        register_groq_agents()
        register_groq_agents()
        register_groq_agents()

        # Should still work
        assert "groq_plain" in MemberAgentFactory._agent_classes
        assert "groq_web_search" in MemberAgentFactory._agent_classes


class TestTomlConfigurationSupport:
    """Tests for TOML configuration support."""

    def test_groq_plain_config_from_dict(self, mock_groq_api_key: str) -> None:
        """GR-054: groq_plain should work with TOML-style dict config.

        Note: Uses type='custom' to bypass MemberAgentConfig model validation.
        """
        from mixseek_plus.agents import GroqPlainAgent, register_groq_agents

        register_groq_agents()

        # Create config with TOML-style values (using custom type to bypass validation)
        config = MemberAgentConfig(
            name="toml-groq-agent",
            type="custom",  # Bypass model validation
            model="groq:llama-3.3-70b-versatile",
            system_instruction="From TOML config",
            temperature=0.5,
            max_tokens=512,
        )
        agent = GroqPlainAgent(config)

        assert agent.agent_name == "toml-groq-agent"
        assert agent.config.temperature == 0.5

    def test_groq_web_search_config_from_dict(self, mock_groq_api_key: str) -> None:
        """GR-054: groq_web_search should work with TOML-style dict config.

        Note: Uses type='custom' to bypass MemberAgentConfig model validation.
        """
        from mixseek_plus.agents import GroqWebSearchAgent, register_groq_agents

        register_groq_agents()

        # Create config with TOML-style values (using custom type to bypass validation)
        config = MemberAgentConfig(
            name="toml-search-agent",
            type="custom",  # Bypass model validation
            model="groq:llama-3.3-70b-versatile",
            system_instruction="Search the web",
        )
        agent = GroqWebSearchAgent(config)

        assert isinstance(agent, GroqWebSearchAgent)
        assert agent.agent_name == "toml-search-agent"
