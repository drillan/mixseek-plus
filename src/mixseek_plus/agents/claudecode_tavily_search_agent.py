"""ClaudeCodeTavilySearchAgent - ClaudeCode + Tavily検索エージェント.

このモジュールはClaudeCodeモデルとTavily検索機能を組み合わせた
Member Agentを提供します。

Tavilyツールはpydantic-aiのツール機能としてエージェントに登録されます。
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from pydantic_ai import Agent

from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent
from mixseek_plus.agents.mixins.tavily_tools import (
    TavilySearchDeps,
    TavilyToolsRepositoryMixin,
)
from mixseek_plus.errors import ModelCreationError
from mixseek_plus.providers.tavily import validate_tavily_credentials
from mixseek_plus.providers.tavily_client import TavilyAPIClient

if TYPE_CHECKING:
    from typing import Any, Callable

    from mixseek.models.member_agent import MemberAgentConfig

logger = logging.getLogger(__name__)

# MCP tool name prefix for pydantic-ai tools
MCP_TOOL_PREFIX = "mcp__pydantic_tools__"


class ClaudeCodeTavilySearchAgent(TavilyToolsRepositoryMixin, BaseClaudeCodeAgent):
    """ClaudeCodeモデル + Tavilyツールのエージェント.

    このエージェントはClaudeCodeの強力な機能とTavilyの3つのツールを組み合わせます:
    - tavily_search: Web検索
    - tavily_extract: URL群からコンテンツ抽出
    - tavily_context: RAG用検索コンテキスト取得

    ClaudeCodeでは、TavilyツールはMCPツールとしてラップされ、
    `mcp__pydantic_tools__tavily_*` という命名規則に従います。

    Example TOML configuration:
        [[members]]
        name = "claudecode-tavily-researcher"
        type = "claudecode_tavily_search"
        model = "claudecode:claude-sonnet-4-5"
        system_prompt = "You are a helpful research assistant."
        temperature = 0.3
        max_tokens = 4000
    """

    _agent: Agent[TavilySearchDeps, str]
    _tavily_client: TavilyAPIClient
    _tavily_tools: list[Callable[..., Any]]

    def __init__(self, config: MemberAgentConfig) -> None:
        """Initialize ClaudeCodeTavilySearchAgent.

        Args:
            config: Validated agent configuration

        Raises:
            ValueError: If authentication fails (TAVILY_API_KEY missing/invalid)
        """
        # Validate Tavily credentials before base class init
        try:
            validate_tavily_credentials()
        except ModelCreationError as e:
            raise ValueError(f"Tavily credential validation failed: {e}") from e

        # Initialize base class (creates ClaudeCode model)
        super().__init__(config)

        # Create Tavily client
        self._tavily_client = self._create_tavily_client()

        # Create ModelSettings from config
        model_settings = self._create_model_settings()

        # Create Pydantic AI agent
        if config.system_prompt is not None:
            self._agent = Agent(
                model=self._model,
                deps_type=TavilySearchDeps,
                output_type=str,
                instructions=config.system_instruction,
                system_prompt=config.system_prompt,
                model_settings=model_settings,
                retries=config.max_retries,
            )
        else:
            self._agent = Agent(
                model=self._model,
                deps_type=TavilySearchDeps,
                output_type=str,
                instructions=config.system_instruction,
                model_settings=model_settings,
                retries=config.max_retries,
            )

        # Register Tavily tools
        self._tavily_tools = self._register_tavily_tools()

    def _create_tavily_client(self) -> TavilyAPIClient:
        """Create TavilyAPIClient from environment variable.

        Returns:
            TavilyAPIClient instance

        Note:
            TAVILY_API_KEY environment variable must be set.
            validate_tavily_credentials() should be called before this method.
        """
        api_key = os.environ.get("TAVILY_API_KEY", "")
        return TavilyAPIClient(api_key=api_key)

    def _get_agent(self) -> Agent[TavilySearchDeps, str]:  # type: ignore[override]
        """Get the Pydantic AI agent instance.

        Returns:
            The configured Pydantic AI agent
        """
        return self._agent

    def _create_deps(self) -> TavilySearchDeps:  # type: ignore[override]
        """Create dependencies for agent execution.

        Returns:
            TavilySearchDeps with configuration and Tavily client
        """
        return TavilySearchDeps(
            config=self.config,
            tavily_client=self._tavily_client,
        )

    def _get_agent_type_metadata(self) -> dict[str, str]:
        """Get agent-type specific metadata.

        Returns:
            Metadata indicating this is a ClaudeCode Tavily search agent
        """
        return {"agent_type": "claudecode_tavily_search"}

    def _get_mcp_tool_names(self) -> list[str]:
        """Get MCP tool names for all registered Tavily tools.

        MCP tools follow naming convention: mcp__pydantic_tools__<tool_name>

        Returns:
            List of MCP tool names
        """
        return [f"{MCP_TOOL_PREFIX}{tool.__name__}" for tool in self._tavily_tools]

    def _get_wrapped_mcp_tools(self) -> dict[str, Callable[..., Any]]:
        """Get wrapped MCP tools with deps injection.

        Creates wrapper functions that inject TavilySearchDeps into tool calls,
        allowing the tools to be called without explicitly passing the deps.

        Returns:
            Dictionary mapping MCP tool names to wrapped tool functions
        """
        wrapped_tools: dict[str, Callable[..., Any]] = {}
        deps = self._create_deps()

        for tool in self._tavily_tools:
            mcp_name = f"{MCP_TOOL_PREFIX}{tool.__name__}"

            # Create a wrapper that injects deps
            wrapped_tools[mcp_name] = self._wrap_tool_for_mcp(tool, deps)

        return wrapped_tools

    def _wrap_tool_for_mcp(
        self,
        tool: Callable[..., Any],
        deps: TavilySearchDeps,
    ) -> Callable[..., Any]:
        """Wrap a tool function to inject TavilySearchDeps.

        Args:
            tool: Original tool function that expects RunContext
            deps: TavilySearchDeps to inject

        Returns:
            Wrapped async function that doesn't require ctx parameter
        """

        async def wrapped(**kwargs: Any) -> str:
            """Wrapped tool that injects deps via RunContext."""
            # Create a mock RunContext with our deps
            ctx = _create_mock_run_context(deps)
            result: str = await tool(ctx, **kwargs)
            return result

        # Preserve original function metadata
        wrapped.__name__ = tool.__name__
        wrapped.__doc__ = tool.__doc__

        return wrapped


def _create_mock_run_context(deps: TavilySearchDeps) -> Any:
    """Create a mock RunContext for MCP tool calls.

    Args:
        deps: TavilySearchDeps to include in context

    Returns:
        Mock object with deps attribute
    """

    class MockRunContext:
        """Mock RunContext that provides deps."""

        def __init__(self, deps: TavilySearchDeps) -> None:
            self.deps = deps

    return MockRunContext(deps)
