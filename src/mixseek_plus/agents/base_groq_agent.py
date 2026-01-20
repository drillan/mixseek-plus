"""Base class for Groq Member Agents.

This module provides a common base class for Groq-based agents,
eliminating code duplication between GroqPlainAgent and GroqWebSearchAgent.
"""

import time
from abc import abstractmethod
from typing import Any, cast

from httpx import HTTPStatusError
from pydantic_ai import Agent, IncompleteToolCall
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings

from mixseek.agents.member.base import BaseMemberAgent
from mixseek.models.member_agent import MemberAgentConfig, MemberAgentResult

from mixseek_plus.errors import ModelCreationError
from mixseek_plus.model_factory import create_model
from mixseek_plus.types import AgentMetadata, UsageInfo


class BaseGroqAgent(BaseMemberAgent):
    """Base class for Groq-based Member Agents.

    Provides common functionality shared by GroqPlainAgent and GroqWebSearchAgent:
    - Model creation via mixseek-plus
    - ModelSettings creation from config
    - API error extraction with detailed messages
    - Common execute() flow with error handling

    Subclasses must implement:
    - _create_agent(): Create the Pydantic AI agent with appropriate configuration
    - _create_deps(): Create dependencies for agent execution
    - _get_agent_type_metadata(): Return agent-type specific metadata
    """

    _model: Model

    def __init__(self, config: MemberAgentConfig) -> None:
        """Initialize Base Groq Agent.

        Args:
            config: Validated agent configuration

        Raises:
            ValueError: If model creation fails (e.g., missing API key)
        """
        super().__init__(config)

        # Use mixseek-plus create_model for Groq support
        try:
            self._model = create_model(config.model)
        except ModelCreationError as e:
            raise ValueError(f"Model creation failed: {e}") from e

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

    def _extract_api_error_details(self, error: Exception) -> tuple[str, str]:
        """Extract detailed error message and code from API errors.

        GR-032: Provides user-friendly error messages for common API errors.

        Args:
            error: The exception that was raised

        Returns:
            Tuple of (error_message, error_code)
        """
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

    @abstractmethod
    def _get_agent(self) -> Agent[Any, str]:
        """Get the Pydantic AI agent instance.

        Returns:
            The configured Pydantic AI agent
        """
        ...

    @abstractmethod
    def _create_deps(self) -> object:
        """Create dependencies for agent execution.

        Returns:
            Dependencies object appropriate for the agent type
        """
        ...

    @abstractmethod
    def _get_agent_type_metadata(self) -> dict[str, str]:
        """Get agent-type specific metadata.

        Returns:
            Dictionary with agent-type specific metadata fields
        """
        ...

    async def execute(
        self,
        task: str,
        context: dict[str, object] | None = None,
        **kwargs: object,
    ) -> MemberAgentResult:
        """Execute task with Groq agent.

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
            # Create dependencies (implemented by subclass)
            deps = self._create_deps()

            # Execute with Pydantic AI agent
            # Note: Type ignore needed for kwargs compatibility with pydantic-ai's overloaded run()
            result = await self._get_agent().run(task, deps=deps, **kwargs)  # type: ignore[call-overload]

            # Capture complete message history
            all_messages = result.all_messages()

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Extract usage information if available
            usage_info: UsageInfo = {}
            if hasattr(result, "usage"):
                usage = result.usage()
                usage_info = UsageInfo(
                    total_tokens=getattr(usage, "total_tokens", None),
                    prompt_tokens=getattr(usage, "prompt_tokens", None),
                    completion_tokens=getattr(usage, "completion_tokens", None),
                    requests=getattr(usage, "requests", None),
                )

            # Build metadata
            metadata: AgentMetadata = AgentMetadata(
                model_id=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            # Add agent-type specific metadata
            metadata.update(self._get_agent_type_metadata())  # type: ignore[typeddict-item]
            if context:
                metadata["context"] = context  # type: ignore[typeddict-item]

            # Cast TypedDicts to dict[str, Any] for API compatibility
            usage_dict = cast(dict[str, Any], usage_info) if usage_info else None
            metadata_dict = cast(dict[str, Any], metadata)

            result_obj = MemberAgentResult.success(
                content=str(result.output),
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                execution_time_ms=execution_time_ms,
                usage_info=usage_dict,
                metadata=metadata_dict,
                all_messages=all_messages,
            )

            # Log completion
            self.logger.log_execution_complete(
                execution_id=execution_id, result=result_obj, usage_info=usage_dict
            )

            return result_obj

        except Exception as e:
            return self._handle_execution_error(
                e, task, kwargs, execution_id, start_time
            )

    def _handle_execution_error(
        self,
        error: Exception,
        task: str,
        kwargs: dict[str, object],
        execution_id: str,
        start_time: float,
    ) -> MemberAgentResult:
        """Handle execution errors with proper logging and result creation.

        Args:
            error: The exception that was raised
            task: The task that was being executed
            kwargs: Additional execution parameters
            execution_id: The execution ID for logging
            start_time: When execution started

        Returns:
            MemberAgentResult with error information
        """
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Handle IncompleteToolCall explicitly
        if isinstance(error, IncompleteToolCall):
            error_context: dict[str, object] = {
                "task": task,
                "kwargs": kwargs,
                "error_type": "IncompleteToolCall",
            }
            self.logger.log_error(
                execution_id=execution_id,
                error=error,
                context=error_context,
            )

            result_obj = MemberAgentResult.error(
                error_message=f"Tool call generation incomplete due to token limit: {error}",
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
        error_message, error_code = self._extract_api_error_details(error)

        self.logger.log_error(
            execution_id=execution_id,
            error=error,
            context={"task": task, "kwargs": kwargs},
        )

        result_obj = MemberAgentResult.error(
            error_message=error_message,
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            error_code=error_code,
            execution_time_ms=execution_time_ms,
        )

        self.logger.log_execution_complete(execution_id=execution_id, result=result_obj)
        return result_obj
