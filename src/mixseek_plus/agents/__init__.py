"""Custom Member Agents for mixseek-plus.

This module provides custom agent implementations that extend mixseek-core
with additional provider support (e.g., Groq, ClaudeCode, Playwright).
"""

from mixseek_plus.agents.claudecode_agent import ClaudeCodePlainAgent
from mixseek_plus.agents.groq_agent import GroqPlainAgent
from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

__all__ = [
    "GroqPlainAgent",
    "GroqWebSearchAgent",
    "ClaudeCodePlainAgent",
    "register_groq_agents",
    "register_claudecode_agents",
    # Playwright agents (loaded lazily to avoid import errors when playwright is not installed)
    "PlaywrightMarkdownFetchAgent",
    "register_playwright_agents",
]


def __getattr__(name: str) -> object:
    """Lazy loading for Playwright agents to avoid import errors.

    This allows importing from mixseek_plus.agents without having playwright installed,
    raising a clear error only when the Playwright agent is actually used.
    """
    if name == "PlaywrightMarkdownFetchAgent":
        from mixseek_plus.agents.playwright_markdown_fetch_agent import (
            PlaywrightMarkdownFetchAgent,
        )

        return PlaywrightMarkdownFetchAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def register_groq_agents() -> None:
    """Register Groq agents with MemberAgentFactory.

    Call this function to enable groq_plain and groq_web_search agent types
    in TOML configuration files.

    Example TOML:
        [[members]]
        name = "groq-assistant"
        type = "groq_plain"
        model = "groq:llama-3.3-70b-versatile"

    Note:
        This function is idempotent - calling it multiple times is safe.
    """
    from mixseek.agents.member.factory import MemberAgentFactory

    MemberAgentFactory.register_agent("groq_plain", GroqPlainAgent)
    MemberAgentFactory.register_agent("groq_web_search", GroqWebSearchAgent)


def register_claudecode_agents() -> None:
    """Register ClaudeCode agents with MemberAgentFactory.

    Call this function to enable claudecode_plain agent type
    in TOML configuration files.

    Example TOML:
        [[members]]
        name = "claudecode-assistant"
        type = "claudecode_plain"
        model = "claudecode:claude-sonnet-4-5"

    Note:
        This function is idempotent - calling it multiple times is safe.
    """
    from mixseek.agents.member.factory import MemberAgentFactory

    MemberAgentFactory.register_agent("claudecode_plain", ClaudeCodePlainAgent)


def register_playwright_agents() -> None:
    """Register Playwright agents with MemberAgentFactory.

    Call this function to enable playwright_markdown_fetch agent type
    in TOML configuration files.

    Example TOML:
        [[members]]
        name = "web-fetcher"
        type = "playwright_markdown_fetch"
        model = "groq:llama-3.3-70b-versatile"

        [members.playwright]
        headless = false
        timeout_ms = 60000

    Note:
        This function is idempotent - calling it multiple times is safe.
        Requires playwright optional dependencies to be installed:
            pip install mixseek-plus[playwright]
            playwright install chromium
    """
    from mixseek.agents.member.factory import MemberAgentFactory

    from mixseek_plus.agents.playwright_markdown_fetch_agent import (
        PlaywrightMarkdownFetchAgent,
    )

    MemberAgentFactory.register_agent(
        "playwright_markdown_fetch", PlaywrightMarkdownFetchAgent
    )
