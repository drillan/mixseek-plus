"""Groq Plain Member Agent implementation.

This module implements a custom Member Agent that uses Groq models
via mixseek-plus's create_model() function.
"""

import time
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from mixseek.agents.member.base import BaseMemberAgent
from mixseek.models.member_agent import MemberAgentConfig, MemberAgentResult

from mixseek_plus.errors import ModelCreationError
from mixseek_plus.model_factory import create_model


@dataclass
class GroqAgentDeps:
    """Dependencies for Groq Plain Agent."""

    config: MemberAgentConfig


class GroqPlainAgent(BaseMemberAgent):
    """Plain Member Agent using Groq models via mixseek-plus.

    This custom agent enables the use of Groq models (groq:*) within
    mixseek-core's orchestration framework.
    """

    def __init__(self, config: MemberAgentConfig) -> None:
        """Initialize Groq Plain Agent.

        Args:
            config: Validated agent configuration

        Raises:
            ValueError: If authentication fails
        """
        super().__init__(config)

        # Use mixseek-plus create_model for Groq support
        try:
            model = create_model(config.model)
        except ModelCreationError as e:
            raise ValueError(f"Model creation failed: {e}") from e

        # Create ModelSettings from config
        model_settings = self._create_model_settings()

        # Create Pydantic AI agent
        if config.system_prompt is not None:
            self._agent: Agent[GroqAgentDeps, str] = Agent(
                model=model,
                deps_type=GroqAgentDeps,
                output_type=str,
                instructions=config.system_instruction,
                system_prompt=config.system_prompt,
                model_settings=model_settings,
                retries=config.max_retries,
            )
        else:
            self._agent = Agent(
                model=model,
                deps_type=GroqAgentDeps,
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

    async def execute(
        self, task: str, context: dict[str, Any] | None = None, **kwargs: Any
    ) -> MemberAgentResult:
        """Execute task with Groq plain reasoning agent.

        Args:
            task: User task or prompt to execute
            context: Optional context information
            **kwargs: Additional execution parameters

        Returns:
            MemberAgentResult with execution outcome
        """
        start_time = time.time()

        # Log execution start
        execution_id = self.logger.log_execution_start(
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            task=task,
            model_id=self.config.model,
            context=context,
            **kwargs,
        )

        # Validate input
        if not task.strip():
            return MemberAgentResult.error(
                error_message="Task cannot be empty or contain only whitespace",
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                error_code="EMPTY_TASK",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        try:
            # Create dependencies
            deps = GroqAgentDeps(config=self.config)

            # Execute with Pydantic AI agent
            result = await self._agent.run(task, deps=deps, **kwargs)

            # Capture complete message history
            all_messages = result.all_messages()

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Extract usage information if available
            usage_info: dict[str, Any] = {}
            if hasattr(result, "usage"):
                usage = result.usage()
                usage_info = {
                    "total_tokens": getattr(usage, "total_tokens", None),
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "completion_tokens": getattr(usage, "completion_tokens", None),
                    "requests": getattr(usage, "requests", None),
                }

            # Build metadata
            metadata: dict[str, Any] = {
                "model_id": self.config.model,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }
            if context:
                metadata["context"] = context

            result_obj = MemberAgentResult.success(
                content=str(result.output),
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                execution_time_ms=execution_time_ms,
                usage_info=usage_info if usage_info else None,
                metadata=metadata,
                all_messages=all_messages,
            )

            # Log completion
            self.logger.log_execution_complete(
                execution_id=execution_id, result=result_obj, usage_info=usage_info
            )

            return result_obj

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Handle IncompleteToolCall explicitly
            from pydantic_ai import IncompleteToolCall

            if isinstance(e, IncompleteToolCall):
                self.logger.log_error(
                    execution_id=execution_id,
                    error=e,
                    context={
                        "task": task,
                        "kwargs": kwargs,
                        "error_type": "IncompleteToolCall",
                    },
                )

                result_obj = MemberAgentResult.error(
                    error_message=f"Tool call generation incomplete due to token limit: {e}",
                    agent_name=self.agent_name,
                    agent_type=self.agent_type,
                    error_code="TOKEN_LIMIT_EXCEEDED",
                    execution_time_ms=execution_time_ms,
                )

                self.logger.log_execution_complete(
                    execution_id=execution_id, result=result_obj
                )

                return result_obj

            # Handle HTTP status errors with detailed messages (GR-032)
            error_message, error_code = self._extract_api_error_details(e)

            self.logger.log_error(
                execution_id=execution_id,
                error=e,
                context={"task": task, "kwargs": kwargs},
            )

            result_obj = MemberAgentResult.error(
                error_message=error_message,
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                error_code=error_code,
                execution_time_ms=execution_time_ms,
            )

            self.logger.log_execution_complete(
                execution_id=execution_id, result=result_obj
            )

            return result_obj

    def _extract_api_error_details(self, error: Exception) -> tuple[str, str]:
        """Extract detailed error message and code from API errors.

        GR-032: Provides user-friendly error messages for common API errors.

        Args:
            error: The exception that was raised

        Returns:
            Tuple of (error_message, error_code)
        """
        from httpx import HTTPStatusError

        if isinstance(error, HTTPStatusError):
            status_code = error.response.status_code

            if status_code == 401:
                return (
                    "Groq API authentication failed. Please check your GROQ_API_KEY.",
                    "AUTH_ERROR",
                )
            elif status_code == 429:
                return (
                    "Groq API rate limit exceeded. Please wait and retry.",
                    "RATE_LIMIT_ERROR",
                )
            elif status_code == 503:
                return (
                    "Groq service temporarily unavailable. Please try again later.",
                    "SERVICE_UNAVAILABLE_ERROR",
                )
            else:
                return (
                    f"Groq API error (HTTP {status_code}): {error}",
                    "EXECUTION_ERROR",
                )

        # Default for non-HTTP errors
        return (str(error), "EXECUTION_ERROR")
