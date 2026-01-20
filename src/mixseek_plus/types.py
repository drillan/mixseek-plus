"""Type definitions for mixseek-plus.

This module provides TypedDict definitions for type-safe dictionaries
used throughout the package.
"""

from typing import Literal, TypedDict

# Playwright wait state literal type
WaitForLoadState = Literal["load", "domcontentloaded", "networkidle"]


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
    playwright_wait_for_load_state: WaitForLoadState


class ExecutionContext(TypedDict, total=False):
    """Context information passed to agent execution.

    Provides type-safe access to common context fields.
    """

    task: str
    kwargs: dict[str, object]
    error_type: str


# Tavily API TypedDicts


class TavilySearchResultItemDict(TypedDict, total=False):
    """検索結果アイテムの辞書型."""

    title: str
    url: str
    content: str
    score: float
    raw_content: str | None


class TavilySearchResultDict(TypedDict, total=False):
    """検索結果全体の辞書型."""

    query: str
    answer: str | None
    results: list[TavilySearchResultItemDict]
    images: list[str] | None
    response_time: float


class TavilyExtractResultItemDict(TypedDict, total=False):
    """抽出結果アイテムの辞書型."""

    url: str
    raw_content: str


class TavilyExtractFailedItemDict(TypedDict, total=False):
    """抽出失敗アイテムの辞書型."""

    url: str
    error: str


class TavilyExtractResultDict(TypedDict, total=False):
    """抽出結果全体の辞書型."""

    results: list[TavilyExtractResultItemDict]
    failed_results: list[TavilyExtractFailedItemDict]
    response_time: float
