"""Observability module for mixseek-plus.

This module provides observability features including Logfire integration
for ClaudeCode agents.
"""

from mixseek_plus.observability.logfire_integration import setup_logfire_instrumentation

__all__ = ["setup_logfire_instrumentation"]
