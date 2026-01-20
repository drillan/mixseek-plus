"""Verbose mode utilities for mixseek-plus.

This module provides shared functions for verbose mode handling,
including environment variable checking and logging configuration.
Also provides unified verbose logging helpers for tool invocations.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Literal, Protocol

from mixseek_plus.utils.constants import (
    PARAM_VALUE_MAX_LENGTH,
    PARAMS_SUMMARY_MAX_LENGTH,
    RESULT_PREVIEW_MAX_LENGTH,
    TRUNCATION_SUFFIX_LENGTH,
)

# Status type for tool execution results
ToolStatus = Literal["success", "error", "unknown"]

logger = logging.getLogger(__name__)

# Logger for verbose output - uses mixseek.member_agents for proper handler configuration
_member_logger = logging.getLogger("mixseek.member_agents")


def is_verbose_mode() -> bool:
    """Check if verbose mode is enabled via environment variable.

    Verbose mode enables detailed console logging for debugging purposes.

    Returns:
        True if MIXSEEK_VERBOSE environment variable is set to '1' or 'true'
        (case-insensitive), False otherwise.
    """
    return os.getenv("MIXSEEK_VERBOSE", "").lower() in ("1", "true")


# Module-level flag to track if verbose logging has been configured
_VERBOSE_LOGGING_CONFIGURED = False


def _configure_member_agents_logging() -> None:
    """Configure member_agents logger for DEBUG level (internal common function).

    Sets the mixseek.member_agents logger and its file handlers to DEBUG level.
    This is the shared implementation used by both ensure_verbose_logging_configured()
    and configure_verbose_logging_for_mode().
    """
    member_agents_logger = logging.getLogger("mixseek.member_agents")
    member_agents_logger.setLevel(logging.DEBUG)

    for handler in member_agents_logger.handlers:
        if hasattr(handler, "baseFilename"):  # FileHandler
            handler.setLevel(logging.DEBUG)


def ensure_verbose_logging_configured() -> None:
    """Ensure verbose logging is configured for member_agents logger.

    This function is called lazily when verbose mode is enabled and a tool
    is about to be invoked. It configures the mixseek.member_agents logger
    to show DEBUG level messages, which enables log_tool_invocation() output.

    This lazy configuration is necessary because the logger handlers are
    created by MemberAgentLogger when an agent is instantiated, which happens
    after patch_core() is called.
    """
    global _VERBOSE_LOGGING_CONFIGURED

    if _VERBOSE_LOGGING_CONFIGURED:
        return

    if not is_verbose_mode():
        return

    _configure_member_agents_logging()

    _VERBOSE_LOGGING_CONFIGURED = True
    logger.debug("Verbose logging configured for member_agents (lazy init)")


def configure_verbose_logging_for_mode() -> None:
    """Configure logging level for verbose mode if MIXSEEK_VERBOSE is set.

    This function checks if verbose mode is enabled via environment variable
    and configures the mixseek.member_agents logger to show DEBUG level messages.
    This ensures that log_tool_invocation() output appears in the log file.

    Called automatically by patch_core() to handle cases where MIXSEEK_VERBOSE
    is set before patch_core() is called.
    """
    if not is_verbose_mode():
        return

    _configure_member_agents_logging()

    logger.debug("Verbose logging configured for member_agents (MIXSEEK_VERBOSE=1)")


class ToolLike(Protocol):
    """Protocol for objects that behave like pydantic-ai Tool.

    This protocol defines the minimal interface needed for MCP tool handling.
    Both pydantic_ai.tools.Tool and our ToolWrapper class implement this interface.
    """

    name: str
    description: str | None
    function: Callable[..., Awaitable[str]]


@dataclass
class MockRunContext[T]:
    """Mock RunContext for MCP tool calls.

    When tools are called via MCP, pydantic-ai's RunContext is not available.
    This mock provides the minimal interface needed by tool functions that
    access ctx.deps.

    Attributes:
        deps: The dependencies instance for the current execution.
    """

    deps: T


def _format_params_for_verbose(params: dict[str, object]) -> str:
    """Format parameters dictionary for verbose output.

    Args:
        params: Dictionary of parameter names and values.

    Returns:
        Formatted string like "key1=value1, key2=value2" with truncation.
    """
    if not params:
        return ""

    parts = []
    for key, value in params.items():
        value_str = str(value)
        truncate_at = PARAM_VALUE_MAX_LENGTH - TRUNCATION_SUFFIX_LENGTH
        if len(value_str) > PARAM_VALUE_MAX_LENGTH:
            value_str = value_str[:truncate_at] + "..."
        parts.append(f"{key}={value_str}")

    result = ", ".join(parts)
    # Truncate total params string if too long
    if len(result) > PARAMS_SUMMARY_MAX_LENGTH:
        truncate_at = PARAMS_SUMMARY_MAX_LENGTH - TRUNCATION_SUFFIX_LENGTH
        result = result[:truncate_at] + "..."

    return result


def log_verbose_tool_start(tool_name: str, params: dict[str, object]) -> None:
    """Log tool start in verbose mode.

    Outputs "[Tool Start] tool_name: params" to the member_agents logger
    if verbose mode is enabled.

    Args:
        tool_name: Name of the tool being invoked.
        params: Dictionary of tool parameters.

    Example:
        >>> log_verbose_tool_start("fetch_page", {"url": "https://example.com"})
        # Output (if verbose): [Tool Start] fetch_page: url=https://example.com
    """
    if not is_verbose_mode():
        return

    ensure_verbose_logging_configured()

    params_str = _format_params_for_verbose(params)
    _member_logger.info("[Tool Start] %s: %s", tool_name, params_str)


def log_verbose_tool_done(
    tool_name: str,
    status: ToolStatus,
    execution_time_ms: int,
    result_preview: str | None = None,
) -> None:
    """Log tool completion in verbose mode.

    Outputs "[Tool Done] tool_name: status in Xms" to the member_agents logger
    if verbose mode is enabled. Optionally logs a result preview.

    Args:
        tool_name: Name of the tool that completed.
        status: Completion status ("success", "error", or "unknown").
        execution_time_ms: Execution time in milliseconds.
        result_preview: Optional preview of the result content.

    Example:
        >>> log_verbose_tool_done("fetch_page", "success", 1234, "# Page Title...")
        # Output (if verbose):
        # [Tool Done] fetch_page: success in 1234ms
        # [Tool Result Preview] # Page Title...
    """
    if not is_verbose_mode():
        return

    ensure_verbose_logging_configured()

    _member_logger.info(
        "[Tool Done] %s: %s in %dms", tool_name, status, execution_time_ms
    )

    if result_preview:
        # Truncate and escape newlines for single-line output
        truncated = result_preview[:RESULT_PREVIEW_MAX_LENGTH]
        if len(result_preview) > RESULT_PREVIEW_MAX_LENGTH:
            truncate_at = RESULT_PREVIEW_MAX_LENGTH - TRUNCATION_SUFFIX_LENGTH
            truncated = result_preview[:truncate_at] + "..."
        escaped = truncated.replace("\n", "\\n")
        _member_logger.info("[Tool Result Preview] %s", escaped)
