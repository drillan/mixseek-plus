"""Unit tests for PlaywrightMarkdownFetchAgent.

Tests cover:
- Agent initialization and configuration
- BaseMemberAgent interface implementation
- Agent execution and error handling
- Default system prompt
- Agent registration

Note: All imports that transitively import MemberAgentConfig must be done
      inside test functions to ensure patch_core() has been called first.

Note: Using type="custom" is required because MemberAgentConfig's validate_model
      validator rejects groq: prefix for non-custom agent types.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestPlaywrightMarkdownFetchAgentInitialization:
    """Tests for PlaywrightMarkdownFetchAgent initialization."""

    def test_inherits_from_base_member_agent(self, mock_groq_api_key: str) -> None:
        """PlaywrightMarkdownFetchAgent should inherit from BaseMemberAgent."""
        from mixseek.agents.member.base import BaseMemberAgent
        from mixseek.models.member_agent import MemberAgentConfig

        config = MemberAgentConfig(
            name="test-fetcher",
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

            assert isinstance(agent, BaseMemberAgent)

    def test_creates_agent_with_valid_config(self, mock_groq_api_key: str) -> None:
        """Should create agent with valid configuration."""
        from mixseek.models.member_agent import MemberAgentConfig

        config = MemberAgentConfig(
            name="web-fetcher",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_prompt="Fetch and analyze web pages.",
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

            assert agent.agent_name == "web-fetcher"
            assert agent.config.model == "groq:llama-3.3-70b-versatile"

    def test_accepts_playwright_settings(
        self, mock_groq_api_key: str, mock_playwright_config: dict[str, object]
    ) -> None:
        """Should accept Playwright-specific settings."""
        from mixseek.models.member_agent import MemberAgentConfig

        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig

        config = MemberAgentConfig(
            name="test-fetcher",
            type="custom",
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

            # Manually set playwright config (MemberAgentConfig doesn't have playwright field)
            agent._playwright_config = PlaywrightConfig(
                headless=mock_playwright_config.get("headless", True),  # type: ignore[arg-type]
                timeout_ms=mock_playwright_config.get("timeout_ms", 30000),  # type: ignore[arg-type]
            )

            assert agent.playwright_config.headless is True
            assert agent.playwright_config.timeout_ms == 30000

    def test_raises_value_error_for_invalid_model(
        self, clear_groq_api_key: None
    ) -> None:
        """Should raise ValueError when model creation fails."""
        from mixseek.models.member_agent import MemberAgentConfig

        config = MemberAgentConfig(
            name="test-fetcher",
            type="custom",
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

            with pytest.raises(ValueError, match="Model creation failed"):
                PlaywrightMarkdownFetchAgent(config)


class TestPlaywrightMarkdownFetchAgentExecute:
    """Tests for PlaywrightMarkdownFetchAgent.execute() method."""

    @pytest.mark.asyncio
    async def test_returns_member_agent_result(self, mock_groq_api_key: str) -> None:
        """execute() should return MemberAgentResult."""
        from mixseek.models.member_agent import (
            MemberAgentConfig,
            MemberAgentResult,
            ResultStatus,
        )

        config = MemberAgentConfig(
            name="test-fetcher",
            type="custom",
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

            # Mock the pydantic-ai agent run
            mock_result = MagicMock()
            mock_result.output = "Fetched content summary"
            mock_result.all_messages.return_value = []

            # Get the agent (creates it if needed)
            pydantic_agent = agent._get_agent()

            with patch.object(
                pydantic_agent, "run", new_callable=AsyncMock
            ) as mock_run:
                mock_run.return_value = mock_result
                result = await agent.execute("Fetch https://example.com")

            assert isinstance(result, MemberAgentResult)
            assert result.status == ResultStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_returns_error_for_empty_task(self, mock_groq_api_key: str) -> None:
        """Empty task should return error result."""
        from mixseek.models.member_agent import MemberAgentConfig, ResultStatus

        config = MemberAgentConfig(
            name="test-fetcher",
            type="custom",
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
            result = await agent.execute("")

            assert result.status == ResultStatus.ERROR
            assert result.error_code == "EMPTY_TASK"

    @pytest.mark.asyncio
    async def test_includes_playwright_metadata(self, mock_groq_api_key: str) -> None:
        """Result metadata should include Playwright settings."""
        from mixseek.models.member_agent import MemberAgentConfig

        from mixseek_plus.agents.base_playwright_agent import PlaywrightConfig

        config = MemberAgentConfig(
            name="test-fetcher",
            type="custom",
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

            # Manually set playwright config (MemberAgentConfig doesn't have playwright field)
            agent._playwright_config = PlaywrightConfig(headless=False)

            mock_result = MagicMock()
            mock_result.output = "Content"
            mock_result.all_messages.return_value = []

            pydantic_agent = agent._get_agent()

            with patch.object(
                pydantic_agent, "run", new_callable=AsyncMock
            ) as mock_run:
                mock_run.return_value = mock_result
                result = await agent.execute("Fetch example.com")

            assert result.metadata is not None
            assert result.metadata.get("playwright_headless") is False


class TestDefaultSystemPrompt:
    """Tests for default system prompt."""

    def test_default_system_prompt_mentions_fetch_tool(
        self, mock_groq_api_key: str
    ) -> None:
        """Default system prompt should reference fetch_page tool."""
        from mixseek.models.member_agent import MemberAgentConfig

        config = MemberAgentConfig(
            name="test-fetcher",
            type="custom",
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
            prompt = agent._default_system_prompt()

            assert "fetch_page" in prompt
            assert "web" in prompt.lower()


class TestAgentTypeMetadata:
    """Tests for agent type metadata."""

    def test_returns_correct_agent_type(self, mock_groq_api_key: str) -> None:
        """_get_agent_type_metadata should return playwright_markdown_fetch type."""
        from mixseek.models.member_agent import MemberAgentConfig

        config = MemberAgentConfig(
            name="test-fetcher",
            type="custom",
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
            metadata = agent._get_agent_type_metadata()

            assert metadata["agent_type"] == "playwright_markdown_fetch"
            assert "playwright_headless" in metadata
            assert "playwright_timeout_ms" in metadata


class TestPlaywrightDeps:
    """Tests for PlaywrightDeps dataclass."""

    def test_holds_agent_reference(self, mock_groq_api_key: str) -> None:
        """PlaywrightDeps should hold reference to agent."""
        from mixseek.models.member_agent import MemberAgentConfig

        config = MemberAgentConfig(
            name="test-fetcher",
            type="custom",
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
                PlaywrightDeps,
                PlaywrightMarkdownFetchAgent,
            )

            agent = PlaywrightMarkdownFetchAgent(config)
            deps = PlaywrightDeps(agent=agent)

            assert deps.agent is agent


class TestAgentRegistration:
    """Tests for agent registration in MemberAgentFactory."""

    def test_register_playwright_agents_is_idempotent(
        self, mock_groq_api_key: str
    ) -> None:
        """register_playwright_agents() should be safe to call multiple times."""
        with (
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_playwright_available"
            ),
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_markitdown_available"
            ),
        ):
            from mixseek_plus.agents import register_playwright_agents

            # Should not raise on multiple calls
            register_playwright_agents()
            register_playwright_agents()

    def test_playwright_markdown_fetch_type_registered(
        self, mock_groq_api_key: str
    ) -> None:
        """playwright_markdown_fetch type should be registered."""
        with (
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_playwright_available"
            ),
            patch(
                "mixseek_plus.agents.base_playwright_agent._check_markitdown_available"
            ),
        ):
            from mixseek.agents.member.factory import MemberAgentFactory

            from mixseek_plus.agents import register_playwright_agents

            register_playwright_agents()

            # The factory should have the agent class registered
            assert "playwright_markdown_fetch" in MemberAgentFactory._agent_classes
