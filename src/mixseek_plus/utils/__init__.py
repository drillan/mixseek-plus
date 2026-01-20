"""Utility modules for mixseek-plus.

This module provides utility classes and functions including
pydantic-ai tool call extraction for logging.
"""

from mixseek_plus.utils.tool_logging import (
    ClaudeCodeToolCallExtractor,  # Backward compatibility alias
    PydanticAIToolCallExtractor,
)
from mixseek_plus.utils.constants import (
    ARGS_SUMMARY_DEFAULT_MAX_LENGTH,
    PARAM_VALUE_MAX_LENGTH,
    PARAMS_SUMMARY_MAX_LENGTH,
    RESULT_PREVIEW_MAX_LENGTH,
    RESULT_SUMMARY_DEFAULT_MAX_LENGTH,
    TRUNCATION_SUFFIX_LENGTH,
)
from mixseek_plus.utils.verbose import (
    MockRunContext,
    ToolLike,
    ToolStatus,
    configure_verbose_logging_for_mode,
    ensure_verbose_logging_configured,
    is_verbose_mode,
    log_verbose_tool_done,
    log_verbose_tool_start,
)

__all__ = [
    # Constants
    "ARGS_SUMMARY_DEFAULT_MAX_LENGTH",
    "PARAM_VALUE_MAX_LENGTH",
    "PARAMS_SUMMARY_MAX_LENGTH",
    "RESULT_PREVIEW_MAX_LENGTH",
    "RESULT_SUMMARY_DEFAULT_MAX_LENGTH",
    "TRUNCATION_SUFFIX_LENGTH",
    # Verbose utilities
    "MockRunContext",
    "ToolLike",
    "ToolStatus",
    "configure_verbose_logging_for_mode",
    "ensure_verbose_logging_configured",
    "is_verbose_mode",
    "log_verbose_tool_done",
    "log_verbose_tool_start",
    # Logging utilities
    "ClaudeCodeToolCallExtractor",  # Backward compatibility alias
    "PydanticAIToolCallExtractor",
]
