"""Verbose mode utilities for mixseek-plus.

This module provides shared functions for verbose mode handling,
including environment variable checking and logging configuration.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


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
