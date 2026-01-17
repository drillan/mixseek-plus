"""Groq Plain Member Agent implementation.

This module implements a custom Member Agent that uses Groq models
via mixseek-plus's create_model() function.
"""

from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent

from mixseek.models.member_agent import MemberAgentConfig

from mixseek_plus.agents.base_groq_agent import BaseGroqAgent


@dataclass
class GroqAgentDeps:
    """Dependencies for Groq Plain Agent."""

    config: MemberAgentConfig


class GroqPlainAgent(BaseGroqAgent):
    """Plain Member Agent using Groq models via mixseek-plus.

    This custom agent enables the use of Groq models (groq:*) within
    mixseek-core's orchestration framework.
    """

    _agent: Agent[GroqAgentDeps, str]

    def __init__(self, config: MemberAgentConfig) -> None:
        """Initialize Groq Plain Agent.

        Args:
            config: Validated agent configuration

        Raises:
            ValueError: If model creation fails (e.g., missing API key, invalid model ID)
        """
        super().__init__(config)

        # Create ModelSettings from config
        model_settings = self._create_model_settings()

        # Create Pydantic AI agent
        if config.system_prompt is not None:
            self._agent = Agent(
                model=self._model,
                deps_type=GroqAgentDeps,
                output_type=str,
                instructions=config.system_instruction,
                system_prompt=config.system_prompt,
                model_settings=model_settings,
                retries=config.max_retries,
            )
        else:
            self._agent = Agent(
                model=self._model,
                deps_type=GroqAgentDeps,
                output_type=str,
                instructions=config.system_instruction,
                model_settings=model_settings,
                retries=config.max_retries,
            )

    def _get_agent(self) -> Agent[Any, str]:
        """Get the Pydantic AI agent instance.

        Returns:
            The configured Pydantic AI agent
        """
        return self._agent

    def _create_deps(self) -> GroqAgentDeps:
        """Create dependencies for agent execution.

        Returns:
            GroqAgentDeps with configuration
        """
        return GroqAgentDeps(config=self.config)

    def _get_agent_type_metadata(self) -> dict[str, str]:
        """Get agent-type specific metadata.

        Returns:
            Empty dict as plain agent has no special metadata
        """
        return {}
