"""PlaywrightMarkdownFetchAgent のロギング機能の単体テスト.

US1: MCPツール呼び出しのログ確認
T008: PlaywrightMarkdownFetchAgent のMCPツールログテスト
"""

from unittest.mock import MagicMock, patch

import pytest


class TestPlaywrightAgentMCPToolLogging:
    """PlaywrightMarkdownFetchAgent の _wrap_tool_for_mcp() ログ機能テスト."""

    def test_wrap_tool_for_mcp_exists(self) -> None:
        """_wrap_tool_for_mcp メソッドが存在することを確認."""
        from mixseek_plus.agents.playwright_markdown_fetch_agent import (
            PlaywrightMarkdownFetchAgent,
        )

        assert hasattr(PlaywrightMarkdownFetchAgent, "_wrap_tool_for_mcp")

    def test_wrap_tool_for_mcp_returns_tool_like(self) -> None:
        """_wrap_tool_for_mcp がToolLikeオブジェクトを返すことを確認."""
        from mixseek_plus.agents.playwright_markdown_fetch_agent import (
            PlaywrightMarkdownFetchAgent,
        )

        # Create a mock tool
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test description"

        async def mock_func(**kwargs: object) -> str:
            return "result"

        mock_tool.function = mock_func

        # Create agent with mocked initialization
        with patch.object(
            PlaywrightMarkdownFetchAgent, "__init__", lambda self, config: None
        ):
            agent = PlaywrightMarkdownFetchAgent.__new__(PlaywrightMarkdownFetchAgent)

            result = agent._wrap_tool_for_mcp(mock_tool)

            # Verify it has the required attributes
            assert hasattr(result, "name")
            assert hasattr(result, "description")
            assert hasattr(result, "function")
            assert callable(result.function)

    @pytest.mark.asyncio
    async def test_wrap_tool_for_mcp_injects_context(self) -> None:
        """_wrap_tool_for_mcp がPlaywrightDepsコンテキストを注入することを確認."""
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

        mock_tool = MagicMock()
        mock_tool.name = "fetch_page"
        mock_tool.description = "Fetch a page"
        mock_tool.function = mock_func

        with patch.object(
            PlaywrightMarkdownFetchAgent, "__init__", lambda self, config: None
        ):
            agent = PlaywrightMarkdownFetchAgent.__new__(PlaywrightMarkdownFetchAgent)

            wrapped_tool = agent._wrap_tool_for_mcp(mock_tool)

            # Call the wrapped function
            await wrapped_tool.function(url="https://example.com")

            # Verify context was injected
            assert received_ctx is not None
            assert hasattr(received_ctx, "deps")
            assert isinstance(received_ctx.deps, PlaywrightDeps)
            assert received_ctx.deps.agent is agent

    @pytest.mark.asyncio
    async def test_wrap_tool_for_mcp_preserves_function_metadata(self) -> None:
        """_wrap_tool_for_mcp が関数メタデータを保持することを確認."""
        from mixseek_plus.agents.playwright_markdown_fetch_agent import (
            PlaywrightMarkdownFetchAgent,
        )

        async def original_func(ctx: object, **kwargs: object) -> str:
            """Original docstring."""
            return "result"

        mock_tool = MagicMock()
        mock_tool.name = "fetch_page"
        mock_tool.description = "Fetch a page"
        mock_tool.function = original_func

        with patch.object(
            PlaywrightMarkdownFetchAgent, "__init__", lambda self, config: None
        ):
            agent = PlaywrightMarkdownFetchAgent.__new__(PlaywrightMarkdownFetchAgent)

            wrapped_tool = agent._wrap_tool_for_mcp(mock_tool)

            # Function metadata should be preserved
            assert wrapped_tool.function.__name__ == "original_func"
            assert wrapped_tool.function.__doc__ == "Original docstring."
