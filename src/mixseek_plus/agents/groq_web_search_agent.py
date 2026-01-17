"""Groq Web Search Member Agent implementation.

This module implements a custom Member Agent that uses Groq models
with Web Search capability via Tavily API.
"""

from dataclasses import dataclass
from typing import Any

from httpx import HTTPStatusError
from pydantic_ai import Agent, RunContext
from tavily import AsyncTavilyClient  # type: ignore[import-untyped]

from mixseek.models.member_agent import MemberAgentConfig

from mixseek_plus.agents.base_groq_agent import BaseGroqAgent
from mixseek_plus.errors import ModelCreationError
from mixseek_plus.providers.tavily import validate_tavily_credentials


class TavilySearchError(Exception):
    """Error raised when Tavily search fails.

    This error wraps various Tavily API failures including:
    - Authentication errors (invalid API key)
    - Rate limit errors
    - Network errors
    - Invalid response format
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize TavilySearchError.

        Args:
            message: Error description
            original_error: The underlying exception that caused this error
        """
        super().__init__(message)
        self.original_error = original_error


@dataclass
class GroqWebSearchDeps:
    """Dependencies for Groq Web Search Agent."""

    config: MemberAgentConfig
    tavily_client: AsyncTavilyClient


class GroqWebSearchAgent(BaseGroqAgent):
    """Web Search Member Agent using Groq models via mixseek-plus.

    This custom agent enables the use of Groq models (groq:*) with
    web search capability within mixseek-core's orchestration framework.

    Uses Tavily's AsyncTavilyClient for search functionality.
    Requires both GROQ_API_KEY and TAVILY_API_KEY environment variables to be set.
    """

    _agent: Agent[GroqWebSearchDeps, str]
    _tavily_client: AsyncTavilyClient

    def __init__(self, config: MemberAgentConfig) -> None:
        """Initialize Groq Web Search Agent.

        Args:
            config: Validated agent configuration

        Raises:
            ValueError: If authentication fails (GROQ_API_KEY or TAVILY_API_KEY
                       missing/invalid)
        """
        # Validate Tavily credentials before base class init
        try:
            validate_tavily_credentials()
        except ModelCreationError as e:
            raise ValueError(f"Tavily credential validation failed: {e}") from e

        super().__init__(config)

        # Create ModelSettings from config
        model_settings = self._create_model_settings()

        # Create Tavily client (uses TAVILY_API_KEY env var)
        self._tavily_client = AsyncTavilyClient()

        # Create Pydantic AI agent with web search tool
        if config.system_prompt is not None:
            self._agent = Agent(
                model=self._model,
                deps_type=GroqWebSearchDeps,
                output_type=str,
                instructions=config.system_instruction,
                system_prompt=config.system_prompt,
                model_settings=model_settings,
                retries=config.max_retries,
            )
        else:
            self._agent = Agent(
                model=self._model,
                deps_type=GroqWebSearchDeps,
                output_type=str,
                instructions=config.system_instruction,
                model_settings=model_settings,
                retries=config.max_retries,
            )

        # Register web search tool
        @self._agent.tool
        async def web_search(ctx: RunContext[GroqWebSearchDeps], query: str) -> str:
            """Search the web for information.

            Args:
                ctx: Run context with dependencies
                query: The search query to execute

            Returns:
                Search results as formatted text

            Raises:
                TavilySearchError: If the search fails
            """
            client = ctx.deps.tavily_client
            try:
                results = await client.search(query)
            except HTTPStatusError as e:
                status_code = e.response.status_code
                if status_code == 401:
                    raise TavilySearchError(
                        "Tavily API authentication failed. Please check your TAVILY_API_KEY.",
                        original_error=e,
                    ) from e
                elif status_code == 429:
                    raise TavilySearchError(
                        "Tavily API rate limit exceeded. Please wait and retry.",
                        original_error=e,
                    ) from e
                else:
                    raise TavilySearchError(
                        f"Tavily API error (HTTP {status_code}): {e}",
                        original_error=e,
                    ) from e
            except Exception as e:
                raise TavilySearchError(
                    f"Tavily search failed: {e}",
                    original_error=e,
                ) from e

            # Format results for LLM consumption
            result_items = results.get("results", [])
            if not result_items:
                return "No results found"

            formatted = []
            for result in result_items:
                if not isinstance(result, dict):
                    continue
                formatted.append(
                    f"Title: {result.get('title', 'N/A')}\n"
                    f"URL: {result.get('url', 'N/A')}\n"
                    f"Content: {result.get('content', 'N/A')}\n"
                )
            return "\n---\n".join(formatted) if formatted else "No results found"

    def _get_agent(self) -> Agent[Any, str]:
        """Get the Pydantic AI agent instance.

        Returns:
            The configured Pydantic AI agent
        """
        return self._agent

    def _create_deps(self) -> GroqWebSearchDeps:
        """Create dependencies for agent execution.

        Returns:
            GroqWebSearchDeps with configuration and Tavily client
        """
        return GroqWebSearchDeps(
            config=self.config,
            tavily_client=self._tavily_client,
        )

    def _get_agent_type_metadata(self) -> dict[str, str]:
        """Get agent-type specific metadata.

        Returns:
            Metadata indicating this is a web search agent
        """
        return {"agent_type": "groq_web_search"}
