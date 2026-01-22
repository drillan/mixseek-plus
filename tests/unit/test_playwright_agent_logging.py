"""PlaywrightMarkdownFetchAgent のロギング機能の単体テスト.

US1: MCPツール呼び出しのログ確認
T008: PlaywrightMarkdownFetchAgent のMCPツールログテスト
"""

from dataclasses import dataclass
from typing import Callable, Coroutine
from unittest.mock import patch

import pytest


@dataclass
class MockTool:
    """Dataclass-compatible tool mock for testing _wrap_tool_for_mcp_impl."""

    name: str
    description: str | None
    function: Callable[..., Coroutine[object, object, str]]


class TestPlaywrightAgentMCPToolLogging:
    """PlaywrightMarkdownFetchAgent の _wrap_tool_for_mcp_impl() ログ機能テスト."""

    def test_wrap_tool_for_mcp_impl_exists(self) -> None:
        """_wrap_tool_for_mcp_impl メソッドが存在することを確認."""
        from mixseek_plus.agents.playwright_markdown_fetch_agent import (
            PlaywrightMarkdownFetchAgent,
        )

        assert hasattr(PlaywrightMarkdownFetchAgent, "_wrap_tool_for_mcp_impl")

    def test_wrap_tool_for_mcp_impl_returns_tool_like(self) -> None:
        """_wrap_tool_for_mcp_impl がToolLikeオブジェクトを返すことを確認."""
        from mixseek_plus.agents.playwright_markdown_fetch_agent import (
            PlaywrightMarkdownFetchAgent,
        )

        # Create a dataclass-compatible mock tool
        async def mock_func(**kwargs: object) -> str:
            return "result"

        mock_tool = MockTool(
            name="test_tool", description="Test description", function=mock_func
        )

        # Create agent with mocked initialization
        with patch.object(
            PlaywrightMarkdownFetchAgent, "__init__", lambda self, config: None
        ):
            agent = PlaywrightMarkdownFetchAgent.__new__(PlaywrightMarkdownFetchAgent)

            result = agent._wrap_tool_for_mcp_impl(mock_tool)  # type: ignore[arg-type]

            # Verify it has the required attributes
            assert hasattr(result, "name")
            assert hasattr(result, "description")
            assert hasattr(result, "function")
            assert callable(result.function)

    @pytest.mark.asyncio
    async def test_wrap_tool_for_mcp_impl_injects_context(self) -> None:
        """_wrap_tool_for_mcp_impl がPlaywrightDepsコンテキストを注入することを確認."""
        from mixseek_plus.agents.playwright_markdown_fetch_agent import (
            PlaywrightDeps,
            PlaywrightMarkdownFetchAgent,
        )

        # Track if context was injected
        received_ctx = None

        async def mock_func(ctx: object, **kwargs: object) -> str:
            nonlocal received_ctx
            received_ctx = ctx
            return "result"

        mock_tool = MockTool(
            name="fetch_page", description="Fetch a page", function=mock_func
        )

        with patch.object(
            PlaywrightMarkdownFetchAgent, "__init__", lambda self, config: None
        ):
            agent = PlaywrightMarkdownFetchAgent.__new__(PlaywrightMarkdownFetchAgent)

            wrapped_tool = agent._wrap_tool_for_mcp_impl(mock_tool)  # type: ignore[arg-type]

            # Call the wrapped function
            await wrapped_tool.function(url="https://example.com")

            # Verify context was injected
            assert received_ctx is not None
            assert hasattr(received_ctx, "deps")
            assert isinstance(received_ctx.deps, PlaywrightDeps)
            assert received_ctx.deps.agent is agent

    @pytest.mark.asyncio
    async def test_wrap_tool_for_mcp_impl_preserves_function_metadata(self) -> None:
        """_wrap_tool_for_mcp_impl が関数メタデータを保持することを確認."""
        from mixseek_plus.agents.playwright_markdown_fetch_agent import (
            PlaywrightMarkdownFetchAgent,
        )

        async def original_func(ctx: object, **kwargs: object) -> str:
            """Original docstring."""
            return "result"

        mock_tool = MockTool(
            name="fetch_page", description="Fetch a page", function=original_func
        )

        with patch.object(
            PlaywrightMarkdownFetchAgent, "__init__", lambda self, config: None
        ):
            agent = PlaywrightMarkdownFetchAgent.__new__(PlaywrightMarkdownFetchAgent)

            wrapped_tool = agent._wrap_tool_for_mcp_impl(mock_tool)  # type: ignore[arg-type]

            # Function metadata should be preserved
            assert wrapped_tool.function.__name__ == "original_func"
            assert wrapped_tool.function.__doc__ == "Original docstring."
