"""Execution mixin for Pydantic AI-based agents.

This module provides a reusable mixin that eliminates code duplication
in execute() and related methods across BaseGroqAgent and BasePlaywrightAgent.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol, cast

from mixseek.models.member_agent import MemberAgentConfig, MemberAgentResult
from pydantic_ai import Agent

from mixseek_plus.types import UsageInfo

if TYPE_CHECKING:
    from mixseek.utils.logging import MemberAgentLogger


class AgentProtocol(Protocol):
    """Protocol defining the interface required by PydanticAgentExecutorMixin.

    This protocol ensures that any class using the mixin has the necessary
    attributes and methods for execution.
    """

    @property
    def agent_name(self) -> str:
        """Agent name for logging and result creation."""
        ...

    @property
    def agent_type(self) -> str:
        """Agent type for logging and result creation."""
        ...

    @property
    def config(self) -> MemberAgentConfig:
        """Agent configuration."""
        ...

    @property
    def logger(self) -> MemberAgentLogger:
        """Logger instance for execution logging.

        Returns MemberAgentLogger from mixseek.utils.logging.
        """
        ...

    def _get_agent(self) -> Agent[object, str]:
        """Get the Pydantic AI agent instance."""
        ...

    def _create_deps(self) -> object:
        """Create dependencies for agent execution."""
        ...


class PydanticAgentExecutorMixin(ABC):
    """Mixin providing common Pydantic AI agent execution logic.

    This mixin extracts the shared execution flow from BaseGroqAgent and
    BasePlaywrightAgent, reducing code duplication while allowing for
    agent-specific customization through hook methods.

    Classes using this mixin must satisfy AgentProtocol and implement:
    - _build_agent_metadata(): Return agent-specific metadata
    - _handle_execution_error(): Handle exceptions with agent-specific logic
    """

    def _extract_usage_info(self, result: object) -> UsageInfo | None:
        """Extract usage information from Pydantic AI result.

        Args:
            result: The result from agent.run()

        Returns:
            UsageInfo TypedDict with token counts, or None if unavailable.
            None is returned when the model provider does not provide usage
            information, which is a valid scenario per UsageInfo design.
        """
        if not hasattr(result, "usage"):
            return None
        usage_func = getattr(result, "usage")
        usage = usage_func()
        return UsageInfo(
            total_tokens=getattr(usage, "total_tokens", None),
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            requests=getattr(usage, "requests", None),
        )

    @abstractmethod
    def _build_agent_metadata(
        self, context: dict[str, object] | None
    ) -> dict[str, object]:
        """Build agent-specific metadata.

        Args:
            context: Optional context information

        Returns:
            Metadata dictionary for the result
        """
        ...

    @abstractmethod
    def _handle_execution_error(
        self,
        error: Exception,
        task: str,
        kwargs: dict[str, object],
        execution_id: str,
        start_time: float,
    ) -> MemberAgentResult:
        """Handle execution errors with agent-specific logic.

        Args:
            error: The exception that was raised
            task: The task that was being executed
            kwargs: Additional execution parameters
            execution_id: The execution ID for logging
            start_time: When execution started

        Returns:
            MemberAgentResult with error information
        """
        ...

    async def _execute_pydantic_agent(
        self: AgentProtocol,
        task: str,
        context: dict[str, object] | None = None,
        **kwargs: object,
    ) -> MemberAgentResult:
        """Execute task with Pydantic AI agent.

        This method provides the common execution flow shared by all
        Pydantic AI-based agents (Groq, Playwright, etc.).

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
            result = await self._get_agent().run(task, deps=deps, **kwargs)  # type: ignore[call-overload]

            # Capture complete message history
            all_messages = result.all_messages()

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Type cast to access mixin methods from protocol-typed self
            mixin_self = cast(PydanticAgentExecutorMixin, self)

            # Extract usage information
            usage_info = mixin_self._extract_usage_info(result)

            # Build metadata (implemented by subclass via _build_agent_metadata)
            metadata = mixin_self._build_agent_metadata(context)

            # Cast TypedDicts to dict for API compatibility
            usage_dict = cast(dict[str, object], usage_info) if usage_info else None

            result_obj = MemberAgentResult.success(
                content=str(result.output),
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                execution_time_ms=execution_time_ms,
                usage_info=usage_dict,
                metadata=metadata,
                all_messages=all_messages,
            )

            # Log completion
            self.logger.log_execution_complete(
                execution_id=execution_id, result=result_obj, usage_info=usage_dict
            )

            return result_obj

        except (TypeError, AttributeError, NameError):
            # Re-raise programming errors to aid debugging
            # These indicate bugs in the code, not runtime issues
            raise
        except Exception as e:
            # Delegate runtime errors to subclass-specific error handling
            mixin_self = cast(PydanticAgentExecutorMixin, self)
            return mixin_self._handle_execution_error(
                e, task, kwargs, execution_id, start_time
            )
