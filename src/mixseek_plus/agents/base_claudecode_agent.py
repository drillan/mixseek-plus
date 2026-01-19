"""Base class for ClaudeCode Member Agents.

This module provides a common base class for ClaudeCode-based agents,
following the same pattern as BaseGroqAgent.
"""

from __future__ import annotations

import logging
import os
import time
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from claudecode_model import CLIExecutionError, CLINotFoundError, CLIResponseParseError
from pydantic_ai import Agent
from pydantic_ai.models import Model

from mixseek.agents.member.base import BaseMemberAgent
from mixseek.models.member_agent import MemberAgentConfig, MemberAgentResult

from mixseek_plus.providers import CLAUDECODE_PROVIDER_PREFIX
from mixseek_plus.providers.claudecode import (
    ClaudeCodeToolSettings,
    create_claudecode_model,
)
from mixseek_plus.types import AgentMetadata, UsageInfo

logger = logging.getLogger(__name__)

# Environment variable for workspace path (used by Member agents)
WORKSPACE_ENV_VAR = "MIXSEEK_WORKSPACE"


@dataclass
class ClaudeCodeAgentDeps:
    """Dependencies for ClaudeCode agents."""

    config: MemberAgentConfig


class BaseClaudeCodeAgent(BaseMemberAgent):
    """Base class for ClaudeCode-based Member Agents.

    Provides common functionality shared by ClaudeCode agents:
    - Model creation via mixseek-plus
    - ClaudeCode-specific error handling
    - Common execute() flow with error handling

    Subclasses must implement:
    - _get_agent(): Return the Pydantic AI agent instance
    - _create_deps(): Create dependencies for agent execution
    - _get_agent_type_metadata(): Return agent-type specific metadata
    """

    _model: Model

    def __init__(self, config: MemberAgentConfig) -> None:
        """Initialize Base ClaudeCode Agent.

        Args:
            config: Validated agent configuration

        Raises:
            ValueError: If model creation fails
        """
        super().__init__(config)

        # Extract ClaudeCode-specific tool_settings if available
        claudecode_tool_settings = self._extract_claudecode_tool_settings(config)

        # Extract model name from model ID (remove prefix)
        model_name = config.model
        if model_name.startswith(CLAUDECODE_PROVIDER_PREFIX):
            model_name = model_name[len(CLAUDECODE_PROVIDER_PREFIX) :]

        # Use create_claudecode_model directly with tool_settings
        try:
            self._model = create_claudecode_model(
                model_name, tool_settings=claudecode_tool_settings
            )
        except Exception as e:
            raise ValueError(f"Model creation failed: {e}") from e

    def _extract_claudecode_tool_settings(
        self, config: MemberAgentConfig
    ) -> ClaudeCodeToolSettings | None:
        """Extract ClaudeCode-specific settings from config.tool_settings.

        If the settings contain a 'preset' key and the MIXSEEK_WORKSPACE
        environment variable is set, the preset is resolved from
        configs/presets/claudecode.toml and merged with any local settings.

        Args:
            config: Agent configuration

        Returns:
            ClaudeCodeToolSettings if claudecode section exists, None otherwise
        """
        if config.tool_settings is None:
            return None

        # Access claudecode as an attribute (ToolSettings is a Pydantic model)
        claudecode_settings = getattr(config.tool_settings, "claudecode", None)
        if claudecode_settings is None:
            return None

        # Cast to ClaudeCodeToolSettings
        settings = cast(ClaudeCodeToolSettings, claudecode_settings)

        # Resolve preset if specified
        return self._resolve_preset_if_needed(settings)

    def _resolve_preset_if_needed(
        self, settings: ClaudeCodeToolSettings
    ) -> ClaudeCodeToolSettings:
        """Resolve preset settings if specified and workspace is available.

        Args:
            settings: ClaudeCode tool settings that may contain a 'preset' key.

        Returns:
            Resolved and merged settings, or original settings if no preset
            or workspace is not available.
        """
        preset_name = settings.get("preset")
        if preset_name is None:
            return settings

        workspace = self._get_workspace()
        if workspace is None:
            logger.warning(
                "プリセット '%s' が指定されていますが、%s 環境変数が設定されていないため"
                "プリセット解決をスキップします。preset キーは無視されます。",
                preset_name,
                WORKSPACE_ENV_VAR,
            )
            # Remove preset key and return other settings
            return {k: v for k, v in settings.items() if k != "preset"}  # type: ignore[return-value]

        # Import here to avoid circular imports
        from mixseek_plus.presets import resolve_and_merge_preset

        logger.debug(
            "プリセット '%s' を %s から解決しています (エージェント: %s)...",
            preset_name,
            workspace,
            self.agent_name,
        )
        return resolve_and_merge_preset(settings, workspace)

    def _get_workspace(self) -> Path | None:
        """Get workspace directory from environment variable.

        Member agents determine the workspace from the MIXSEEK_WORKSPACE
        environment variable, which should be set by the orchestrator.

        Returns:
            Workspace directory path, or None if not set.
        """
        workspace_str = os.environ.get(WORKSPACE_ENV_VAR)
        if workspace_str is None:
            return None

        workspace = Path(workspace_str)
        if not workspace.exists():
            logger.warning(
                "%s 環境変数で指定されたディレクトリが存在しません: %s",
                WORKSPACE_ENV_VAR,
                workspace,
            )
            return None

        return workspace

    def _extract_api_error_details(self, error: Exception) -> tuple[str, str]:
        """Extract detailed error message and code from ClaudeCode API errors.

        Args:
            error: The exception that was raised

        Returns:
            Tuple of (error_message, error_code)
        """
        if isinstance(error, CLINotFoundError):
            return (
                "Claude Code CLI not found. Please install it first:\n"
                "  curl -fsSL https://claude.ai/install.sh | bash",
                "CLI_NOT_FOUND",
            )
        elif isinstance(error, CLIExecutionError):
            return (
                f"Claude Code CLI execution error: {error}",
                "CLI_EXECUTION_ERROR",
            )
        elif isinstance(error, CLIResponseParseError):
            return (
                f"Failed to parse Claude Code response: {error}",
                "CLI_PARSE_ERROR",
            )

        # Default for other errors
        return (str(error), "EXECUTION_ERROR")

    @abstractmethod
    def _get_agent(self) -> Agent[ClaudeCodeAgentDeps, str]:
        """Get the Pydantic AI agent instance.

        Returns:
            The configured Pydantic AI agent
        """
        ...

    @abstractmethod
    def _create_deps(self) -> ClaudeCodeAgentDeps:
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
        """Execute task with ClaudeCode agent.

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

        # Handle ClaudeCode-specific errors with detailed messages
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
