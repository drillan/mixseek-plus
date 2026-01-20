"""Logfire integration for pydantic-ai observability.

This module provides optional Logfire instrumentation for pydantic-ai
when the MIXSEEK_LOGFIRE environment variable is enabled.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def _is_logfire_mode() -> bool:
    """Check if Logfire mode is enabled via environment variable.

    Returns:
        True if MIXSEEK_LOGFIRE is set to '1' or 'true'
    """
    return os.getenv("MIXSEEK_LOGFIRE", "").lower() in ("1", "true")


def setup_logfire_instrumentation() -> bool:
    """Setup Logfire instrumentation for pydantic-ai if enabled.

    This function checks the MIXSEEK_LOGFIRE environment variable and,
    if enabled, attempts to configure Logfire auto-instrumentation for
    pydantic-ai.

    Returns:
        True if instrumentation was successfully enabled, False otherwise

    Note:
        - If MIXSEEK_LOGFIRE is not set or 'false', this returns False without action
        - If logfire package is not installed, logs a warning and returns False
        - If logfire.instrument_pydantic_ai() is not available, logs a warning
    """
    if not _is_logfire_mode():
        logger.debug("Logfire mode is disabled (MIXSEEK_LOGFIRE not set)")
        return False

    try:
        import logfire
    except ImportError:
        logger.warning(
            "Logfire mode is enabled (MIXSEEK_LOGFIRE=1) but 'logfire' package is not installed. "
            "Install it with: uv add mixseek-plus[logfire] or pip install logfire"
        )
        return False

    # Check if instrument_pydantic_ai is available
    if not hasattr(logfire, "instrument_pydantic_ai"):
        logger.warning(
            "logfire package is installed but 'instrument_pydantic_ai' is not available. "
            "You may need to upgrade logfire to a newer version."
        )
        return False

    try:
        logfire.instrument_pydantic_ai()
        logger.info("Logfire pydantic-ai instrumentation enabled")
        return True
    except Exception as e:
        logger.warning("Failed to enable Logfire instrumentation: %s", e)
        return False
