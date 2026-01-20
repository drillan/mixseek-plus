"""Custom Member Agents for mixseek-plus.

This module provides custom agent implementations that extend mixseek-core
with additional provider support (e.g., Groq, ClaudeCode, Playwright).
"""

from mixseek_plus.agents.claudecode_agent import ClaudeCodePlainAgent
from mixseek_plus.agents.claudecode_tavily_search_agent import (
    ClaudeCodeTavilySearchAgent,
)
from mixseek_plus.agents.groq_agent import GroqPlainAgent
from mixseek_plus.agents.groq_tavily_search_agent import GroqTavilySearchAgent
from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

__all__ = [
    "GroqPlainAgent",
    "GroqWebSearchAgent",
    "GroqTavilySearchAgent",
    "ClaudeCodePlainAgent",
    "ClaudeCodeTavilySearchAgent",
    "register_groq_agents",
    "register_claudecode_agents",
    "register_tavily_agents",
    "register_all_agents",
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


def register_tavily_agents() -> None:
    """Register Tavily search agents with MemberAgentFactory.

    Call this function to enable tavily_search and claudecode_tavily_search
    agent types in TOML configuration files.

    Example TOML (Groq version):
        [[members]]
        name = "tavily-researcher"
        type = "tavily_search"
        model = "groq:llama-3.3-70b-versatile"
        system_prompt = "You are a helpful research assistant."

    Example TOML (ClaudeCode version):
        [[members]]
        name = "claudecode-tavily-researcher"
        type = "claudecode_tavily_search"
        model = "claudecode:claude-sonnet-4-5"
        system_prompt = "You are a helpful research assistant."

    Note:
        This function is idempotent - calling it multiple times is safe.
        Requires TAVILY_API_KEY environment variable to be set.
    """
    from mixseek.agents.member.factory import MemberAgentFactory

    MemberAgentFactory.register_agent("tavily_search", GroqTavilySearchAgent)
    MemberAgentFactory.register_agent(
        "claudecode_tavily_search", ClaudeCodeTavilySearchAgent
    )


def register_all_agents() -> None:
    """Register all custom agents with MemberAgentFactory.

    This is a convenience function that registers all available agent types:
    - Groq agents (groq_plain, groq_web_search)
    - ClaudeCode agents (claudecode_plain)
    - Tavily search agents (tavily_search, claudecode_tavily_search)

    Note:
        Playwright agents are NOT included as they require optional dependencies.
        Use register_playwright_agents() separately if needed.
    """
    register_groq_agents()
    register_claudecode_agents()
    register_tavily_agents()


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
