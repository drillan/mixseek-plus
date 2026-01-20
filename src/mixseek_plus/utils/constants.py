"""Shared constants for mixseek-plus.

This module provides constant values used across multiple modules
to avoid magic numbers and ensure consistency.
"""

from __future__ import annotations

# Truncation lengths for log output
PARAM_VALUE_MAX_LENGTH = 50
"""Maximum length for individual parameter values in log output."""

PARAMS_SUMMARY_MAX_LENGTH = 100
"""Maximum length for combined parameters summary in log output."""

ARGS_SUMMARY_DEFAULT_MAX_LENGTH = 100
"""Default maximum length for tool arguments summary."""

RESULT_SUMMARY_DEFAULT_MAX_LENGTH = 200
"""Default maximum length for tool result summary."""

RESULT_PREVIEW_MAX_LENGTH = 500
"""Maximum length for result preview in verbose output."""

TRUNCATION_SUFFIX_LENGTH = 3
"""Length of truncation suffix '...'."""
