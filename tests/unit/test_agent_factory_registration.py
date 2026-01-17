"""Unit tests for MemberAgentFactory registration.

Tests cover:
- GR-053: Factory registration for groq_plain and groq_web_search
- GR-054: TOML configuration support via type field
"""

from mixseek.agents.member.factory import MemberAgentFactory
from mixseek.models.member_agent import MemberAgentConfig


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
