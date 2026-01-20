"""Type definitions for mixseek-plus.

This module provides TypedDict definitions for type-safe dictionaries
used throughout the package.
"""

from typing import TypedDict


class UsageInfo(TypedDict, total=False):
    """Usage information from model execution.

    All fields are optional as availability depends on the model provider.
    """

    total_tokens: int | None
    prompt_tokens: int | None
    completion_tokens: int | None
    requests: int | None


class AgentMetadata(TypedDict, total=False):
    """Metadata for agent execution results.

    All fields are optional to allow flexible metadata structure.
    """

    model_id: str
    temperature: float | None
    max_tokens: int | None
    context: dict[str, str | int | float | bool | None]
    agent_type: str


class PlaywrightAgentMetadata(AgentMetadata, total=False):
    """Metadata specific to Playwright-based agents.

    Extends AgentMetadata with Playwright-specific fields.
    """

    playwright_headless: bool
    playwright_timeout_ms: int
    playwright_wait_for_load_state: str


class ExecutionContext(TypedDict, total=False):
    """Context information passed to agent execution.

    Provides type-safe access to common context fields.
    """

    task: str
    kwargs: dict[str, object]
    error_type: str
