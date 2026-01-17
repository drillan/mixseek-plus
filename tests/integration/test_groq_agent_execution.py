"""Integration tests for GroqPlainAgent execution.

These tests require a valid GROQ_API_KEY environment variable.
Mark with @pytest.mark.integration to skip in regular test runs.
"""

import os

import pytest
from mixseek.models.member_agent import MemberAgentConfig, ResultStatus

from mixseek_plus.agents import GroqPlainAgent


@pytest.mark.integration
class TestGroqPlainAgentIntegration:
    """Integration tests for GroqPlainAgent with real API."""

    @pytest.fixture
    def real_api_key(self) -> str:
        """Get real GROQ_API_KEY from environment or skip test."""
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or not api_key.startswith("gsk_"):
            pytest.skip("Valid GROQ_API_KEY not available")
        return api_key

    @pytest.mark.asyncio
    async def test_simple_query(self, real_api_key: str) -> None:
        """GroqPlainAgent should respond to simple queries."""
        config = MemberAgentConfig(
            name="integration-test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful assistant. Be brief.",
            max_tokens=100,
        )

        agent = GroqPlainAgent(config)
        result = await agent.execute("What is 2 + 2? Answer with just the number.")

        assert result.status == ResultStatus.SUCCESS
        assert result.content is not None
        assert len(result.content) > 0
        assert result.execution_time_ms is not None and result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_returns_usage_info(self, real_api_key: str) -> None:
        """Real API calls should return usage information."""
        config = MemberAgentConfig(
            name="integration-test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful assistant. Be very brief.",
            max_tokens=50,
        )

        agent = GroqPlainAgent(config)
        result = await agent.execute("Say 'hello' only")

        assert result.status == ResultStatus.SUCCESS
        assert result.usage_info is not None
        # Usage info should have token counts
        assert result.usage_info.get("total_tokens", 0) > 0

    @pytest.mark.asyncio
    async def test_respects_temperature_setting(self, real_api_key: str) -> None:
        """Temperature setting should affect response generation."""
        config = MemberAgentConfig(
            name="integration-test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful assistant.",
            temperature=0.0,  # Deterministic
            max_tokens=50,
        )

        agent = GroqPlainAgent(config)

        # With temperature=0, same prompt should give consistent results
        result1 = await agent.execute("What is the capital of Japan? One word only.")
        result2 = await agent.execute("What is the capital of Japan? One word only.")

        assert result1.status == ResultStatus.SUCCESS
        assert result2.status == ResultStatus.SUCCESS
        # Both should contain "Tokyo"
        assert "Tokyo" in result1.content or "tokyo" in result1.content.lower()
        assert "Tokyo" in result2.content or "tokyo" in result2.content.lower()

    @pytest.mark.asyncio
    async def test_handles_context_parameter(self, real_api_key: str) -> None:
        """Context parameter should be included in metadata."""
        config = MemberAgentConfig(
            name="integration-test-agent",
            type="custom",
            model="groq:llama-3.3-70b-versatile",
            system_instruction="You are a helpful assistant. Be brief.",
            max_tokens=50,
        )

        agent = GroqPlainAgent(config)
        context: dict[str, object] = {"user_id": "test123", "session": "integration"}
        result = await agent.execute("Say 'ok'", context=context)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata is not None
        assert result.metadata.get("context") == context

    @pytest.mark.asyncio
    async def test_different_model(self, real_api_key: str) -> None:
        """Should work with different Groq models."""
        config = MemberAgentConfig(
            name="integration-test-agent",
            type="custom",
            model="groq:llama-3.1-8b-instant",  # Faster, smaller model
            system_instruction="You are a helpful assistant. Be very brief.",
            max_tokens=30,
        )

        agent = GroqPlainAgent(config)
        result = await agent.execute("Say 'hello'")

        assert result.status == ResultStatus.SUCCESS
        assert result.content is not None
