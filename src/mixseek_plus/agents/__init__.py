"""Custom Member Agents for mixseek-plus.

This module provides custom agent implementations that extend mixseek-core
with additional provider support (e.g., Groq).
"""

from mixseek_plus.agents.groq_agent import GroqPlainAgent
from mixseek_plus.agents.groq_web_search_agent import GroqWebSearchAgent

__all__ = ["GroqPlainAgent", "GroqWebSearchAgent", "register_groq_agents"]


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
