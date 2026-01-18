"""Custom Member Agents for mixseek-plus.

This module provides custom agent implementations that extend mixseek-core
with additional provider support (e.g., Groq, ClaudeCode).
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
]


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
