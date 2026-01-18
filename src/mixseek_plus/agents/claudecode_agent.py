"""ClaudeCode Plain Member Agent implementation.

This module implements a custom Member Agent that uses ClaudeCode models
via mixseek-plus's create_model() function.
"""

from typing import Any

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from mixseek.models.member_agent import MemberAgentConfig

from mixseek_plus.agents.base_claudecode_agent import (
    BaseClaudeCodeAgent,
    ClaudeCodeAgentDeps,
)


class ClaudeCodePlainAgent(BaseClaudeCodeAgent):
    """Plain Member Agent using ClaudeCode models via mixseek-plus.

    This custom agent enables the use of ClaudeCode models (claudecode:*)
    within mixseek-core's orchestration framework.

    ClaudeCode provides built-in tools like Bash, Read/Write/Edit, Glob/Grep,
    WebFetch/WebSearch, making this agent suitable for complex tasks without
    additional tool configuration.
    """

    _agent: Agent[ClaudeCodeAgentDeps, str]

    def __init__(self, config: MemberAgentConfig) -> None:
        """Initialize ClaudeCode Plain Agent.

        Args:
            config: Validated agent configuration

        Raises:
            ValueError: If model creation fails
        """
        super().__init__(config)

        # Create ModelSettings from config
        model_settings = self._create_model_settings()

        # Create Pydantic AI agent
        if config.system_prompt is not None:
            self._agent = Agent(
                model=self._model,
                deps_type=ClaudeCodeAgentDeps,
                output_type=str,
                instructions=config.system_instruction,
                system_prompt=config.system_prompt,
                model_settings=model_settings,
                retries=config.max_retries,
            )
        else:
            self._agent = Agent(
                model=self._model,
                deps_type=ClaudeCodeAgentDeps,
                output_type=str,
                instructions=config.system_instruction,
                model_settings=model_settings,
                retries=config.max_retries,
            )

    def _create_model_settings(self) -> ModelSettings:
        """Create ModelSettings from MemberAgentConfig.

        Returns:
            ModelSettings TypedDict with configured values
        """
        settings: ModelSettings = {}

        if self.config.temperature is not None:
            settings["temperature"] = self.config.temperature
        if self.config.max_tokens is not None:
            settings["max_tokens"] = self.config.max_tokens
        if self.config.stop_sequences is not None:
            settings["stop_sequences"] = self.config.stop_sequences
        if self.config.top_p is not None:
            settings["top_p"] = self.config.top_p
        if self.config.seed is not None:
            settings["seed"] = self.config.seed
        if self.config.timeout_seconds is not None:
            settings["timeout"] = float(self.config.timeout_seconds)

        return settings

    def _get_agent(self) -> Agent[Any, str]:
        """Get the Pydantic AI agent instance.

        Returns:
            The configured Pydantic AI agent
        """
        return self._agent

    def _create_deps(self) -> ClaudeCodeAgentDeps:
        """Create dependencies for agent execution.

        Returns:
            ClaudeCodeAgentDeps with configuration
        """
        return ClaudeCodeAgentDeps(config=self.config)

    def _get_agent_type_metadata(self) -> dict[str, str]:
        """Get agent-type specific metadata.

        Returns:
            Empty dict as plain agent has no special metadata
        """
        return {}
