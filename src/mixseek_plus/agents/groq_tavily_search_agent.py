"""GroqTavilySearchAgent - Groq + Tavily検索エージェント.

このモジュールはGroqモデルとTavily検索機能を組み合わせた
Member Agentを提供します。
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from pydantic_ai import Agent

from mixseek_plus.agents.base_groq_agent import BaseGroqAgent
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


class GroqTavilySearchAgent(TavilyToolsRepositoryMixin, BaseGroqAgent):
    """Groqモデル + Tavilyツールのエージェント.

    このエージェントはGroqの高速推論とTavilyの3つのツールを組み合わせます:
    - tavily_search: Web検索
    - tavily_extract: URL群からコンテンツ抽出
    - tavily_context: RAG用検索コンテキスト取得

    Example TOML configuration:
        [[members]]
        name = "tavily-researcher"
        type = "tavily_search"
        model = "groq:llama-3.3-70b-versatile"
        system_prompt = "You are a helpful research assistant."
        temperature = 0.3
        max_tokens = 4000
    """

    _agent: Agent[TavilySearchDeps, str]
    _tavily_client: TavilyAPIClient
    _tavily_tools: list[Callable[..., Any]]

    def __init__(self, config: MemberAgentConfig) -> None:
        """Initialize GroqTavilySearchAgent.

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

        # Initialize base class (creates Groq model)
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

    def _create_deps(self) -> TavilySearchDeps:
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
            Metadata indicating this is a Tavily search agent
        """
        return {"agent_type": "tavily_search"}
