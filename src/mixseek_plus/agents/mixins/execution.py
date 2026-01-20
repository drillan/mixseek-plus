"""Execution mixin for Pydantic AI-based agents.

This module provides a reusable mixin that eliminates code duplication
in execute() and related methods across BaseGroqAgent and BasePlaywrightAgent.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol, cast

from mixseek.models.member_agent import MemberAgentConfig, MemberAgentResult
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from mixseek_plus.types import UsageInfo
from mixseek_plus.utils.tool_logging import PydanticAIToolCallExtractor
from mixseek_plus.utils.verbose import (
    log_verbose_tool_done,
    log_verbose_tool_start,
)

if TYPE_CHECKING:
    from mixseek.utils.logging import MemberAgentLogger

logger = logging.getLogger(__name__)


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

    def _log_tool_calls_if_verbose(
        self: AgentProtocol,
        execution_id: str,
        messages: list[ModelMessage],
    ) -> None:
        """Extract and log tool calls from message history in verbose mode.

        Uses PydanticAIToolCallExtractor to extract tool call info from
        pydantic-ai message history and logs via verbose helpers.

        Args:
            execution_id: The execution ID for log correlation.
            messages: List of pydantic-ai ModelMessage objects.
        """
        if not messages:
            return

        extractor = PydanticAIToolCallExtractor()
        tool_calls = extractor.extract_tool_calls(messages)

        for call in tool_calls:
            # Log via verbose helpers (checks is_verbose_mode internally)
            log_verbose_tool_start(call["tool_name"], {"args": call["args_summary"]})
            log_verbose_tool_done(
                call["tool_name"],
                call["status"],
                0,  # execution_time_ms not available from history
                result_preview=call["result_summary"],
            )

            # Always log via MemberAgentLogger (file logging)
            self.logger.log_tool_invocation(
                execution_id=execution_id,
                tool_name=call["tool_name"],
                parameters={"args_summary": call["args_summary"]},
                execution_time_ms=0,  # Not available from history
                status=call["status"],
            )

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

            # Log tool calls from message history (verbose + file logging)
            # Note: type ignore needed because mixin pattern with self: AgentProtocol
            # confuses mypy when called via PydanticAgentExecutorMixin cast
            mixin_self._log_tool_calls_if_verbose(execution_id, all_messages)  # type: ignore[misc]

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
