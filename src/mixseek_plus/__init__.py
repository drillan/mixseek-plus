"""mixseek-plus: mixseek-coreの拡張パッケージ."""

from mixseek_plus.agents import (
    ClaudeCodePlainAgent,
    ClaudeCodeTavilySearchAgent,
    GroqPlainAgent,
    GroqTavilySearchAgent,
    GroqWebSearchAgent,
    register_claudecode_agents,
    register_groq_agents,
    register_playwright_agents,
    register_tavily_agents,
)
from mixseek_plus.core_patch import (
    GroqNotPatchedError,
    apply_leader_tool_settings,
    check_groq_support,
    clear_claudecode_tool_settings,
    configure_claudecode_tool_settings,
    disable_verbose_mode,
    enable_verbose_mode,
    get_claudecode_tool_settings,
    patch_core,
    reset_configuration_manager_patch,
)
from mixseek_plus.errors import (
    ClaudeCodeNotPatchedError,
    ConversionError,
    FetchError,
    ModelCreationError,
    PlaywrightNotInstalledError,
    TavilyAPIError,
)
from mixseek_plus.model_factory import create_model
from mixseek_plus.presets import (
    PRESET_FILE_PATH,
    PresetFileNotFoundError,
    PresetNotFoundError,
    resolve_and_merge_preset,
    resolve_claudecode_preset,
)
from mixseek_plus.providers.claudecode import create_claudecode_model

__all__ = [
    "create_model",
    "create_claudecode_model",
    "ModelCreationError",
    "ClaudeCodeNotPatchedError",
    # Playwright errors
    "PlaywrightNotInstalledError",
    "FetchError",
    "ConversionError",
    # Tavily errors
    "TavilyAPIError",
    "GroqPlainAgent",
    "GroqWebSearchAgent",
    "GroqTavilySearchAgent",
    "ClaudeCodePlainAgent",
    "ClaudeCodeTavilySearchAgent",
    "register_groq_agents",
    "register_claudecode_agents",
    "register_tavily_agents",
    # Playwright agents (loaded lazily)
    "PlaywrightMarkdownFetchAgent",
    "register_playwright_agents",
    "patch_core",
    "configure_claudecode_tool_settings",
    "get_claudecode_tool_settings",
    "clear_claudecode_tool_settings",
    "apply_leader_tool_settings",
    "reset_configuration_manager_patch",
    "GroqNotPatchedError",
    "check_groq_support",
    # Verbose mode (ClaudeCode only)
    "enable_verbose_mode",
    "disable_verbose_mode",
    # Presets
    "PRESET_FILE_PATH",
    "PresetFileNotFoundError",
    "PresetNotFoundError",
    "resolve_claudecode_preset",
    "resolve_and_merge_preset",
]


def __getattr__(name: str) -> object:
    """Lazy loading for Playwright agents to avoid import errors.

    This allows importing from mixseek_plus without having playwright installed,
    raising a clear error only when the Playwright agent is actually used.
    """
    if name == "PlaywrightMarkdownFetchAgent":
        from mixseek_plus.agents.playwright_markdown_fetch_agent import (
            PlaywrightMarkdownFetchAgent,
        )

        return PlaywrightMarkdownFetchAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
