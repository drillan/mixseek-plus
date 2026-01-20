"""PlaywrightMarkdownFetchAgent - Web page fetcher with Markdown conversion.

This module provides an agent that fetches web pages using Playwright
and converts them to Markdown format using MarkItDown.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from mixseek.models.member_agent import MemberAgentConfig

from mixseek_plus.agents.base_playwright_agent import (
    BasePlaywrightAgent,
    FetchResult,
)
from mixseek_plus.utils.verbose import (
    MockRunContext,
    ToolLike,
    ToolStatus,
    log_verbose_tool_done,
    log_verbose_tool_start,
)

logger = logging.getLogger(__name__)


@dataclass
class PlaywrightDeps:
    """Dependencies for PlaywrightMarkdownFetchAgent execution.

    Attributes:
        agent: Reference to the PlaywrightMarkdownFetchAgent instance
    """

    agent: PlaywrightMarkdownFetchAgent


class PlaywrightMarkdownFetchAgent(BasePlaywrightAgent):
    """Playwright-based web page fetcher with Markdown conversion.

    This agent fetches web pages using Playwright browser automation and
    converts the HTML content to Markdown format using MarkItDown.
    It integrates with any LLM provider through the model configuration.

    Features:
        - Headed/headless browser modes for bot detection bypass
        - Configurable timeouts and wait conditions
        - Resource blocking for performance optimization
        - Retry logic with exponential backoff
        - HTML to Markdown conversion

    Example TOML configuration:
        [[members]]
        name = "web-fetcher"
        type = "playwright_markdown_fetch"
        model = "groq:llama-3.3-70b-versatile"
        system_prompt = "You are a web content assistant..."

        [members.playwright]
        headless = false
        timeout_ms = 60000
        wait_for_load_state = "networkidle"
    """

    _agent: Agent[PlaywrightDeps, str] | None

    def __init__(self, config: MemberAgentConfig) -> None:
        """Initialize PlaywrightMarkdownFetchAgent.

        Args:
            config: Validated agent configuration

        Raises:
            PlaywrightNotInstalledError: If playwright is not installed
            ValueError: If model creation fails
        """
        super().__init__(config)
        self._agent = None

    def _get_agent(self) -> Agent[object, str]:
        """Get or create the Pydantic AI agent instance.

        Returns:
            The configured Pydantic AI agent with fetch_page tool
        """
        if self._agent is None:
            self._agent = Agent(
                self._model,
                deps_type=PlaywrightDeps,
                output_type=str,
                system_prompt=self.config.system_prompt
                or self._default_system_prompt(),
                model_settings=self._create_model_settings(),
            )

            # Register the fetch_page tool
            @self._agent.tool
            async def fetch_page(ctx: RunContext[PlaywrightDeps], url: str) -> str:
                """Fetch a web page and return its content as Markdown.

                Args:
                    ctx: Run context with agent dependencies
                    url: The URL to fetch

                Returns:
                    Markdown formatted content of the page, or error message
                """
                result: FetchResult = await ctx.deps.agent._fetch_with_retry(url)

                if result.status == "error":
                    return f"Error fetching {url}: {result.error}"

                return result.content

            # ClaudeCodeModel requires explicit toolset registration
            self._register_toolsets_if_claudecode()

        return self._agent  # type: ignore[return-value]

    def _register_toolsets_if_claudecode(self) -> None:
        """Register toolsets with ClaudeCodeModel if applicable.

        ClaudeCodeModel requires explicit registration of tool functions
        via set_agent_toolsets() after Agent creation. This method also:
        - Wraps tool functions to inject PlaywrightDeps context
        - Adds MCP tool names to allowed_tools to ensure Claude can call them

        The MCP tool naming convention is: mcp__<server_name>__<tool_name>
        For pydantic-ai tools, the server name is 'pydantic_tools'.
        """
        try:
            from claudecode_model import ClaudeCodeModel
            from claudecode_model.mcp_integration import MCP_SERVER_NAME

            if isinstance(self._model, ClaudeCodeModel) and self._agent is not None:
                # Access the internal toolset from the agent
                toolset = getattr(self._agent, "_function_toolset", None)
                if toolset is not None:
                    tools = list(toolset.tools.values())
                    if tools:
                        # Wrap tools to inject PlaywrightDeps context
                        wrapped_tools = [
                            self._wrap_tool_for_mcp(tool) for tool in tools
                        ]
                        self._model.set_agent_toolsets(wrapped_tools)  # type: ignore[arg-type]

                        # Add MCP tool names to allowed_tools
                        # MCP tools are named: mcp__<server_name>__<tool_name>
                        mcp_tool_names = [
                            f"mcp__{MCP_SERVER_NAME}__{tool.name}" for tool in tools
                        ]

                        # Update allowed_tools on the model
                        if self._model._allowed_tools is None:
                            self._model._allowed_tools = mcp_tool_names
                        else:
                            # Extend existing allowed_tools
                            self._model._allowed_tools = list(
                                set(self._model._allowed_tools) | set(mcp_tool_names)
                            )
        except ImportError as e:
            # Only suppress if claudecode_model package itself is missing
            # Use ImportError.name attribute for reliable module detection
            missing_module = getattr(e, "name", None)
            if missing_module is None or not missing_module.startswith(
                "claudecode_model"
            ):
                # Log unexpected import errors with full traceback for debugging
                logger.error(
                    "ClaudeCode model import failed unexpectedly: %s",
                    e,
                    exc_info=True,
                )

    def _wrap_tool_for_mcp(self, tool: ToolLike) -> ToolLike:
        """Wrap a pydantic-ai tool to inject PlaywrightDeps context.

        When tools are called via MCP, pydantic-ai's RunContext is not available.
        This wrapper injects a mock context with PlaywrightDeps.

        This wrapper also:
        - Measures execution time
        - Logs tool invocation via MemberAgentLogger
        - Outputs verbose console log if MIXSEEK_VERBOSE is enabled

        Args:
            tool: A pydantic-ai Tool object

        Returns:
            A new Tool object with wrapped function

        Raises:
            TypeError: If dataclasses.replace() fails.
        """
        from dataclasses import replace

        original_function = tool.function
        agent_ref = self
        tool_name = tool.name

        async def wrapped_function(**kwargs: object) -> str:
            """Wrapper that injects PlaywrightDeps context and logs invocation."""
            logger.debug(
                "[MCP Wrapper] Tool '%s' called with kwargs: %s",
                tool_name,
                list(kwargs.keys()),
            )
            # Create deps and mock context
            deps = PlaywrightDeps(agent=agent_ref)
            mock_ctx = MockRunContext(deps=deps)

            # Log tool start via unified verbose helper
            log_verbose_tool_start(tool_name, dict(kwargs))

            start_time = time.perf_counter()
            status: ToolStatus = "success"
            result_str = ""
            try:
                result = await original_function(mock_ctx, **kwargs)
                result_str = str(result)
                return result_str
            except Exception:
                status = "error"
                raise
            finally:
                execution_time_ms = int((time.perf_counter() - start_time) * 1000)

                # Log tool completion via unified verbose helper
                # (wrapped to prevent masking original exceptions)
                try:
                    log_verbose_tool_done(
                        tool_name,
                        status,
                        execution_time_ms,
                        result_preview=result_str if result_str else None,
                    )
                except Exception as log_error:
                    logger.debug("Failed to log tool completion: %s", log_error)

                # Log tool invocation via MemberAgentLogger (file logging)
                has_logger = hasattr(agent_ref, "logger")
                has_method = has_logger and hasattr(
                    agent_ref.logger, "log_tool_invocation"
                )
                logger.debug(
                    "[MCP Wrapper] Logging check: has_logger=%s, has_method=%s",
                    has_logger,
                    has_method,
                )
                if has_logger and has_method:
                    try:
                        # Get execution_id - this might not be available for member agents
                        # so we generate a placeholder if not present
                        execution_id = getattr(
                            agent_ref, "_current_execution_id", "mcp"
                        )
                        agent_ref.logger.log_tool_invocation(
                            execution_id=execution_id,
                            tool_name=tool_name,
                            parameters=dict(kwargs),
                            execution_time_ms=execution_time_ms,
                            status=status,
                        )
                    except Exception as log_error:
                        logger.warning(
                            "Failed to log tool invocation for '%s': %s",
                            tool_name,
                            log_error,
                            exc_info=True,
                        )

        # Preserve function metadata
        wrapped_function.__name__ = original_function.__name__
        wrapped_function.__doc__ = original_function.__doc__

        # Create new tool with wrapped function
        return replace(tool, function=wrapped_function)  # type: ignore[type-var]

    def _create_deps(self) -> PlaywrightDeps:
        """Create dependencies for agent execution.

        Returns:
            PlaywrightDeps with reference to this agent
        """
        return PlaywrightDeps(agent=self)

    def _default_system_prompt(self) -> str:
        """Return the default system prompt for the agent.

        Returns:
            Default system prompt string

        Note:
            When using ClaudeCodeModel, tools are exposed via MCP with the name
            format `mcp__pydantic_tools__<tool_name>`. The system prompt must
            reference the correct MCP tool name for the model to call it.
        """
        return (
            "You are a helpful assistant that can fetch and analyze web pages. "
            "Use the mcp__pydantic_tools__fetch_page tool to retrieve web content "
            "when the user provides a URL or asks about a web page. "
            "After fetching, summarize or answer questions about the content."
        )

    def _get_agent_type_metadata(self) -> dict[str, object]:
        """Get agent-type specific metadata.

        Returns:
            Dictionary with Playwright agent metadata
        """
        return {
            "agent_type": "playwright_markdown_fetch",
            "playwright_headless": self._playwright_config.headless,
            "playwright_timeout_ms": self._playwright_config.timeout_ms,
            "playwright_wait_for_load_state": self._playwright_config.wait_for_load_state,
        }
