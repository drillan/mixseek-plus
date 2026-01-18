"""Integration tests for ClaudeCodePlainAgent execution.

These tests require the Claude Code CLI to be installed.
Mark with @pytest.mark.integration to skip in regular test runs.
"""

import shutil

import pytest
from mixseek.models.member_agent import MemberAgentConfig, ResultStatus

from mixseek_plus.agents import ClaudeCodePlainAgent


def is_claude_code_available() -> bool:
    """Claude Code CLIが利用可能かチェック."""
    return shutil.which("claude") is not None


@pytest.mark.integration
class TestClaudeCodePlainAgentIntegration:
    """Integration tests for ClaudeCodePlainAgent with real CLI."""

    @pytest.fixture(autouse=True)
    def check_claude_code_cli(self) -> None:
        """Claude Code CLIがインストールされていない場合はテストをスキップする."""
        if not is_claude_code_available():
            pytest.skip("Claude Code CLI not installed")

    @pytest.mark.asyncio
    async def test_simple_query(self) -> None:
        """ClaudeCodePlainAgent should respond to simple queries."""
        config = MemberAgentConfig(
            name="integration-test-agent",
            type="custom",
            model="claudecode:claude-haiku-4-5",
            system_instruction="You are a helpful assistant. Be brief.",
            max_tokens=100,
        )

        agent = ClaudeCodePlainAgent(config)
        result = await agent.execute("What is 2 + 2? Answer with just the number.")

        assert result.status == ResultStatus.SUCCESS
        assert result.content is not None
        assert len(result.content) > 0
        assert result.execution_time_ms is not None and result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_returns_metadata(self) -> None:
        """Real CLI calls should return metadata information."""
        config = MemberAgentConfig(
            name="integration-test-agent",
            type="custom",
            model="claudecode:claude-haiku-4-5",
            system_instruction="You are a helpful assistant. Be very brief.",
            max_tokens=50,
        )

        agent = ClaudeCodePlainAgent(config)
        result = await agent.execute("Say 'hello' only")

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata is not None
        assert result.metadata.get("model_id") == "claudecode:claude-haiku-4-5"

    @pytest.mark.asyncio
    async def test_handles_context_parameter(self) -> None:
        """Context parameter should be included in metadata."""
        config = MemberAgentConfig(
            name="integration-test-agent",
            type="custom",
            model="claudecode:claude-haiku-4-5",
            system_instruction="You are a helpful assistant. Be brief.",
            max_tokens=50,
        )

        agent = ClaudeCodePlainAgent(config)
        context: dict[str, object] = {"user_id": "test123", "session": "integration"}
        result = await agent.execute("Say 'ok'", context=context)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata is not None
        assert result.metadata.get("context") == context

    @pytest.mark.asyncio
    async def test_different_model(self) -> None:
        """Should work with different ClaudeCode models."""
        config = MemberAgentConfig(
            name="integration-test-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant. Be very brief.",
            max_tokens=30,
        )

        agent = ClaudeCodePlainAgent(config)
        result = await agent.execute("Say 'hello'")

        assert result.status == ResultStatus.SUCCESS
        assert result.content is not None

    @pytest.mark.asyncio
    async def test_empty_task_returns_error(self) -> None:
        """Empty task should return error without calling CLI."""
        config = MemberAgentConfig(
            name="integration-test-agent",
            type="custom",
            model="claudecode:claude-haiku-4-5",
            system_instruction="You are a helpful assistant.",
        )

        agent = ClaudeCodePlainAgent(config)
        result = await agent.execute("   ")

        assert result.status == ResultStatus.ERROR
        assert result.error_code == "EMPTY_TASK"
