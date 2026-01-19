"""CLI wrapper for mixseek-plus.

This module provides a CLI entry point that wraps mixseek-core's CLI
and automatically enables Groq and ClaudeCode provider support.

Requirements:
- GR-070: Provide mixseek-plus/mskp command wrapping mixseek-core CLI
- GR-071: Automatically call patch_core() on startup
- GR-072: Groq models work without additional setup
- GR-073: Full compatibility with mixseek-core CLI
- CC-052: ClaudeCode models work without additional setup
"""

# IMPORTANT: Apply patch BEFORE importing mixseek.cli.main
# This ensures Groq and ClaudeCode support is enabled before any mixseek-core
# modules are loaded. The order of imports here is critical.
from mixseek_plus.agents import register_claudecode_agents, register_groq_agents
from mixseek_plus.core_patch import patch_core

patch_core()
register_groq_agents()
register_claudecode_agents()

# Now import the core app after patching
from mixseek.cli.main import app as core_app  # noqa: E402

# Create our app by directly using the core app
# This ensures full compatibility with mixseek-core (GR-073)
app = core_app


def ensure_patched() -> None:
    """Ensure patch_core() has been applied.

    This function is idempotent and safe to call multiple times.
    Called by main() to guarantee patch is applied.
    """
    from mixseek_plus.core_patch import is_patched

    if not is_patched():
        patch_core()


def main() -> None:
    """CLI entry point.

    This function is called when the user runs `mixseek-plus` or `mskp` command
    after installing mixseek-plus.
    """
    ensure_patched()
    app()
