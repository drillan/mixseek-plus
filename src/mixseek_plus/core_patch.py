"""Core patching functionality for mixseek-core integration.

This module provides patch_core() which extends mixseek-core's
create_authenticated_model to support Groq and ClaudeCode models.

Also provides configure_claudecode_tool_settings() for configuring
ClaudeCode-specific tool settings (permission_mode, working_directory, etc.)
that are used by Leader/Evaluator/Judgment agents.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Coroutine, Mapping
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic_ai.agent import Agent
from pydantic_ai.models import Model
from pydantic_ai.tools import Tool

from mixseek.exceptions import WorkspacePathNotSpecifiedError
from mixseek.utils.env import get_workspace_for_config

from mixseek_plus.presets import PresetError
from mixseek_plus.providers import CLAUDECODE_PROVIDER_PREFIX, GROQ_PROVIDER_PREFIX
from mixseek_plus.providers.claudecode import ClaudeCodeToolSettings
from mixseek_plus.utils.verbose import (
    MockRunContext,
    ToolLike,
    ToolStatus,
    configure_verbose_logging_for_mode,
    ensure_verbose_logging_configured,
    log_verbose_tool_done,
    log_verbose_tool_start,
)

if TYPE_CHECKING:
    from mixseek.agents.leader.config import TeamConfig
    from mixseek.agents.leader.dependencies import TeamDependencies
    from mixseek.config.schema import TeamSettings

logger = logging.getLogger(__name__)


def enable_verbose_mode() -> None:
    """Enable verbose mode by setting MIXSEEK_VERBOSE environment variable.

    This function sets MIXSEEK_VERBOSE=1 in the current process environment
    and configures logging to show DEBUG level messages for member_agents.
    Verbose mode enables detailed console and file logging for ClaudeCode agents,
    including MCP tool call details.

    Usage:
        import mixseek_plus
        mixseek_plus.enable_verbose_mode()
        mixseek_plus.patch_core()

        # Now ClaudeCode agents will output verbose logs
        # Console output:
        # [MCP Tool Start] fetch_page: url=https://example.com
        # [MCP Tool Done] fetch_page: success in 1234ms
        #
        # File output ($WORKSPACE/logs/member-agent-YYYY-MM-DD.log):
        # tool_invocation events with full details

    Note:
        - This is equivalent to setting MIXSEEK_VERBOSE=1 environment variable
        - Affects only ClaudeCode agents (groq: and other providers are unaffected)
        - Can be called before or after patch_core()
        - Use disable_verbose_mode() to turn off verbose logging
        - Configures mixseek.member_agents logger to DEBUG level

    See Also:
        - Issue #35: Unified verbose mode for all models (future work)
    """
    import os

    os.environ["MIXSEEK_VERBOSE"] = "1"

    # Configure logging level for member_agents to show DEBUG messages
    # This enables log_tool_invocation() output (which uses DEBUG level)
    member_agents_logger = logging.getLogger("mixseek.member_agents")
    member_agents_logger.setLevel(logging.DEBUG)

    # Also set file handler level to DEBUG if it exists
    for handler in member_agents_logger.handlers:
        if hasattr(handler, "baseFilename"):  # FileHandler
            handler.setLevel(logging.DEBUG)

    logger.debug("Verbose mode enabled via enable_verbose_mode()")


def disable_verbose_mode() -> None:
    """Disable verbose mode by removing MIXSEEK_VERBOSE environment variable.

    This function removes the MIXSEEK_VERBOSE environment variable from
    the current process environment, disabling verbose logging for
    ClaudeCode agents.

    Usage:
        import mixseek_plus
        mixseek_plus.disable_verbose_mode()

    Note:
        - Safe to call even if verbose mode was never enabled
        - Takes effect immediately for subsequent agent executions
    """
    import os

    if "MIXSEEK_VERBOSE" in os.environ:
        del os.environ["MIXSEEK_VERBOSE"]
        logger.debug("Verbose mode disabled via disable_verbose_mode()")


def _is_logfire_mode() -> bool:
    """Check if Logfire mode is enabled via environment variable.

    Logfire mode enables pydantic-ai auto-instrumentation for observability.

    Returns:
        True if MIXSEEK_LOGFIRE environment variable is set to '1' or 'true'
        (case-insensitive), False otherwise.
    """
    import os

    return os.getenv("MIXSEEK_LOGFIRE", "").lower() in ("1", "true")


# ContextVar for TeamDependencies - used to pass deps to MCP tool calls
# This allows tool functions that require RunContext[TeamDependencies] to
# access the current deps when called via MCP (which bypasses pydantic-ai's
# normal context injection).
_current_deps: ContextVar[TeamDependencies | None] = ContextVar(
    "_current_deps", default=None
)


# Module-level state to track if patch has been applied
_PATCH_APPLIED = False
_ORIGINAL_FUNCTION: Callable[[str], Model] | None = None

# Module-level state for ClaudeCode tool_settings
_CLAUDECODE_TOOL_SETTINGS: ClaudeCodeToolSettings | None = None

# Module-level state for ConfigurationManager patch
# TeamSettings is imported at runtime in _patch_configuration_manager()
_ORIGINAL_LOAD_TEAM_SETTINGS: Callable[..., TeamSettings] | None = None

# Module-level state for AggregationStore patch (Issue #19)
_ORIGINAL_SAVE_AGGREGATION: Callable[..., Coroutine[object, object, None]] | None = None

# Module-level state for create_leader_agent patch (Issue #23)
# Type mirrors mixseek.agents.leader.agent.create_leader_agent signature
_ORIGINAL_CREATE_LEADER_AGENT: (
    Callable[
        [TeamConfig, Mapping[str, object]],
        Agent[TeamDependencies, str],
    ]
    | None
) = None


class GroqNotPatchedError(Exception):
    """Error raised when groq: model is used without calling patch_core().

    This error indicates that the user is attempting to use a Groq model
    with Leader/Evaluator agents without first enabling Groq support.

    The error message provides clear guidance on how to resolve the issue
    by calling mixseek_plus.patch_core() before using groq: models.
    """

    def __init__(self, message: str | None = None) -> None:
        """Initialize GroqNotPatchedError with a helpful message.

        Args:
            message: Optional custom error message. If not provided,
                    a default helpful message is used.
        """
        if message is None:
            message = (
                "Groq models are not yet enabled for Leader/Evaluator. "
                "Please call mixseek_plus.patch_core() before using groq: models. "
                "Example:\n"
                "    import mixseek_plus\n"
                "    mixseek_plus.patch_core()\n"
                "    # Now you can use groq: models with Leader/Evaluator"
            )
        super().__init__(message)


def is_patched() -> bool:
    """Check if patch_core() has been applied.

    Returns:
        True if patch has been applied, False otherwise
    """
    return _PATCH_APPLIED


def check_groq_support() -> None:
    """Check if Groq support is enabled via patch_core().

    This function verifies that patch_core() has been called,
    which is required before using groq: models with Leader/Evaluator.

    Raises:
        GroqNotPatchedError: If patch_core() has not been called
    """
    if not _PATCH_APPLIED:
        raise GroqNotPatchedError()


def reset_patch_state() -> None:
    """Reset the patch state to unpatched (for testing only).

    This function is intended for use in tests to ensure a clean state
    between test cases. It should not be used in production code.

    Warning:
        This does not actually unpatch the modules - it only resets
        the tracking state. A new patch_core() call will apply new patches.
    """
    global _PATCH_APPLIED, _ORIGINAL_FUNCTION
    _PATCH_APPLIED = False
    _ORIGINAL_FUNCTION = None


def configure_claudecode_tool_settings(
    settings: ClaudeCodeToolSettings,
) -> None:
    """Configure ClaudeCode-specific tool_settings for Leader/Evaluator/Judgment.

    This function registers tool_settings that will be applied when
    ClaudeCode models are created via patch_core(). This allows
    Leader/Evaluator/Judgment agents to use ClaudeCode features
    like permission_mode, working_directory, etc.

    Args:
        settings: ClaudeCode tool settings dictionary containing:
            - permission_mode: Permission mode (e.g., "bypassPermissions")
            - working_directory: Working directory path
            - allowed_tools: List of allowed tools
            - disallowed_tools: List of disallowed tools
            - max_turns: Maximum number of turns

    Usage:
        import mixseek_plus

        # Configure tool_settings before patching
        mixseek_plus.configure_claudecode_tool_settings({
            "permission_mode": "bypassPermissions",
            "working_directory": "/workspace",
        })

        # Apply patch - will use configured settings
        mixseek_plus.patch_core()

        # Now Leader/Evaluator can use claudecode: with tool_settings
        from mixseek.agents.leader import LeaderConfig
        config = LeaderConfig(model="claudecode:claude-sonnet-4-5", ...)

    Note:
        - Settings can be configured before or after patch_core() is called
        - New settings override previous settings
        - Use clear_claudecode_tool_settings() to remove settings
    """
    global _CLAUDECODE_TOOL_SETTINGS
    _CLAUDECODE_TOOL_SETTINGS = settings


def get_claudecode_tool_settings() -> ClaudeCodeToolSettings | None:
    """Get the currently configured ClaudeCode tool_settings.

    Returns:
        ClaudeCode tool settings if configured, None otherwise
    """
    return _CLAUDECODE_TOOL_SETTINGS


def clear_claudecode_tool_settings() -> None:
    """Clear the configured ClaudeCode tool_settings.

    This removes any previously configured tool_settings,
    reverting to default ClaudeCode behavior.
    """
    global _CLAUDECODE_TOOL_SETTINGS
    _CLAUDECODE_TOOL_SETTINGS = None


def apply_leader_tool_settings(
    leader_dict: dict[str, object],
    workspace: Path | None = None,
) -> None:
    """Apply leader tool_settings from TOML configuration.

    Extracts tool_settings.claudecode from leader dict and
    calls configure_claudecode_tool_settings() automatically.

    If the settings contain a 'preset' key and workspace is provided,
    the preset is resolved from configs/presets/claudecode.toml and
    merged with any local settings before being applied.

    Args:
        leader_dict: TeamSettings.leader dict from TOML
        workspace: Optional workspace directory for preset resolution.
                  If not provided, preset resolution is skipped.
    """
    tool_settings = leader_dict.get("tool_settings")
    if not tool_settings:
        logger.debug("leader.tool_settings が設定されていません。スキップします。")
        return

    if not isinstance(tool_settings, dict):
        logger.debug(
            "leader.tool_settings は dict である必要がありますが、%s が指定されました。スキップします。",
            type(tool_settings).__name__,
        )
        return

    claudecode_settings = tool_settings.get("claudecode")
    if claudecode_settings:
        if isinstance(claudecode_settings, dict):
            # Resolve preset if specified and workspace is available
            resolved_settings = _resolve_preset_settings(
                claudecode_settings,  # type: ignore[arg-type]
                workspace,
            )
            configure_claudecode_tool_settings(resolved_settings)
            logger.debug("leader.tool_settings.claudecode を適用しました。")
        else:
            logger.debug(
                "leader.tool_settings.claudecode は dict である必要がありますが、%s が指定されました。スキップします。",
                type(claudecode_settings).__name__,
            )
    else:
        logger.debug(
            "leader.tool_settings.claudecode が設定されていません。スキップします。"
        )


def _resolve_preset_settings(
    settings: ClaudeCodeToolSettings,
    workspace: Path | None,
) -> ClaudeCodeToolSettings:
    """Resolve preset settings if specified and workspace is available.

    Args:
        settings: ClaudeCode tool settings that may contain a 'preset' key.
        workspace: Workspace directory for preset resolution, or None.

    Returns:
        Resolved and merged settings, or original settings if no preset
        or workspace is not available.
    """
    preset_name = settings.get("preset")

    if preset_name is None:
        # No preset specified, return original settings
        return settings

    if workspace is None:
        logger.warning(
            "プリセット '%s' が指定されていますが、workspace が不明なため"
            "プリセット解決をスキップします。preset キーは無視されます。"
            "注意: disallowed_tools などのセキュリティ設定が適用されない可能性があります。",
            preset_name,
        )
        # Remove preset key and return other settings
        return {k: v for k, v in settings.items() if k != "preset"}  # type: ignore[return-value]

    # Import here to avoid circular imports
    from mixseek_plus.presets import resolve_and_merge_preset

    logger.debug(
        "プリセット '%s' を %s から解決しています...",
        preset_name,
        workspace,
    )
    return resolve_and_merge_preset(settings, workspace)


def _patch_configuration_manager() -> None:
    """Patch ConfigurationManager.load_team_settings to auto-apply leader tool_settings.

    This internal function wraps the original load_team_settings method
    to automatically extract and apply leader.tool_settings.claudecode
    when TOML configuration is loaded.

    Called internally by patch_core(). Stores the original method in
    _ORIGINAL_LOAD_TEAM_SETTINGS for potential restoration.

    Raises:
        ImportError: If ConfigurationManager cannot be imported from mixseek-core.
            This indicates a version incompatibility or missing dependency.

    Note:
        This is a module-level patch that affects all ConfigurationManager
        instances for the duration of the session.
    """
    global _ORIGINAL_LOAD_TEAM_SETTINGS

    # Import must succeed - raise ImportError if mixseek-core is incompatible
    from mixseek.config.manager import ConfigurationManager

    _ORIGINAL_LOAD_TEAM_SETTINGS = ConfigurationManager.load_team_settings

    original_func = _ORIGINAL_LOAD_TEAM_SETTINGS

    def patched_load_team_settings(
        self: ConfigurationManager, toml_file: Path, **extra_kwargs: object
    ) -> TeamSettings:
        team_settings = original_func(self, toml_file, **extra_kwargs)

        # Determine workspace using mixseek-core's utility
        try:
            workspace = get_workspace_for_config()
        except WorkspacePathNotSpecifiedError:
            workspace = None

        # Auto-apply leader.tool_settings.claudecode with defensive programming
        leader = getattr(team_settings, "leader", None)
        if leader is not None:
            try:
                apply_leader_tool_settings(leader, workspace)
            except PresetError:
                # PresetError indicates a configuration issue that should be surfaced
                # (e.g., missing preset file, invalid preset name, invalid TOML syntax)
                raise
            except (KeyError, TypeError, ValueError) as e:
                # Configuration structure issues - log with details for debugging
                logger.warning(
                    "leader.tool_settings の構造に問題があります: %s",
                    e,
                    exc_info=True,
                )
            except Exception as e:
                # Unexpected errors - log at error level with full traceback
                logger.error(
                    "leader.tool_settings の自動適用で予期しないエラーが発生しました: %s",
                    e,
                    exc_info=True,
                )
        else:
            logger.debug(
                "team_settings.leader が存在しません。tool_settings の適用をスキップします。"
            )

        return team_settings

    ConfigurationManager.load_team_settings = patched_load_team_settings  # type: ignore[method-assign]


def reset_configuration_manager_patch() -> None:
    """Reset ConfigurationManager.load_team_settings to original (for testing only)."""
    global _ORIGINAL_LOAD_TEAM_SETTINGS

    if _ORIGINAL_LOAD_TEAM_SETTINGS is not None:
        from mixseek.config.manager import ConfigurationManager

        ConfigurationManager.load_team_settings = _ORIGINAL_LOAD_TEAM_SETTINGS  # type: ignore[method-assign]
        _ORIGINAL_LOAD_TEAM_SETTINGS = None


def patch_core() -> None:
    """Extend mixseek-core's create_authenticated_model to support Groq and ClaudeCode.

    This function patches mixseek-core's authentication module to add
    support for the groq: and claudecode: model prefixes. After calling
    this function, Leader and Evaluator agents can use these models.

    Usage:
        import mixseek_plus
        mixseek_plus.patch_core()

        # Now Leader/Evaluator can use groq: and claudecode: models
        from mixseek.agents.leader import LeaderConfig
        config = LeaderConfig(model="groq:llama-3.3-70b-versatile", ...)
        config = LeaderConfig(model="claudecode:claude-sonnet-4-5", ...)

    Note:
        - This function is idempotent - calling it multiple times is safe
        - The patch is applied at module level and persists for the session
        - Must be called explicitly before using groq:/claudecode: with Leader/Evaluator
    """
    global _PATCH_APPLIED, _ORIGINAL_FUNCTION

    # Idempotency check
    if _PATCH_APPLIED:
        return

    from mixseek.core import auth

    from mixseek_plus.providers.claudecode import create_claudecode_model
    from mixseek_plus.providers.groq import create_groq_model

    # Store original function for delegation
    # Capture the current function reference before patching
    original_func = auth.create_authenticated_model
    _ORIGINAL_FUNCTION = original_func

    def patched_create_authenticated_model(model_id: str) -> Model:
        """Extended create_authenticated_model with Groq and ClaudeCode support.

        Args:
            model_id: Model identifier with provider prefix
                     (e.g., "groq:llama-3.3-70b-versatile",
                      "claudecode:claude-sonnet-4-5")

        Returns:
            Model instance appropriate for the provider

        Raises:
            ModelCreationError: If model creation fails
                               (including Groq/ClaudeCode-specific errors)
        """
        if model_id.startswith(CLAUDECODE_PROVIDER_PREFIX):
            model_name = model_id[len(CLAUDECODE_PROVIDER_PREFIX) :]
            # Use globally configured tool_settings if available
            return create_claudecode_model(
                model_name, tool_settings=_CLAUDECODE_TOOL_SETTINGS
            )
        if model_id.startswith(GROQ_PROVIDER_PREFIX):
            model_name = model_id[len(GROQ_PROVIDER_PREFIX) :]
            return create_groq_model(model_name)
        # Use the captured original function, not the module reference
        return original_func(model_id)

    # Apply the patch to the auth module
    # Note: Type ignore needed because auth module's type annotation is more specific
    auth.create_authenticated_model = patched_create_authenticated_model  # type: ignore[assignment]

    # Also patch modules that have already imported the function directly
    # These modules hold their own reference that won't be updated by
    # patching auth.create_authenticated_model alone
    _patch_module_references(patched_create_authenticated_model)

    # Patch ConfigurationManager.load_team_settings for auto leader.tool_settings
    _patch_configuration_manager()

    # Patch AggregationStore.save_aggregation for member tool usage warning (Issue #19)
    _patch_aggregation_store()

    # Patch MemberAgentConfig.validate_model to support groq: and claudecode: prefixes
    _patch_member_agent_config_validator()

    # Patch create_leader_agent for ClaudeCodeModel set_agent_toolsets (Issue #23)
    # ImportError is caught here to allow partial patching if claudecode-model
    # is not installed (optional dependency)
    try:
        _patch_leader_agent()
    except ImportError as e:
        logger.warning(
            "Could not patch create_leader_agent: %s. "
            "ClaudeCodeModel set_agent_toolsets integration will not be available.",
            e,
        )

    # Configure verbose logging if MIXSEEK_VERBOSE is set
    configure_verbose_logging_for_mode()

    _PATCH_APPLIED = True


def _patch_module_references(patched_func: Callable[[str], Model]) -> None:
    """Patch all modules that have imported create_authenticated_model directly.

    mixseek-core has several modules that use:
        from mixseek.core.auth import create_authenticated_model

    These create local references that aren't updated when we patch the
    auth module. We need to explicitly update these references.

    Args:
        patched_func: The patched create_authenticated_model function
    """
    import sys

    # List of modules known to import create_authenticated_model directly
    modules_to_patch = [
        "mixseek.agents.leader.agent",
        "mixseek.round_controller.judgment_client",
        "mixseek.evaluator.llm_client",
    ]

    for module_name in modules_to_patch:
        if module_name in sys.modules:
            module = sys.modules[module_name]
            if hasattr(module, "create_authenticated_model"):
                setattr(module, "create_authenticated_model", patched_func)


def _patch_member_agent_config_validator() -> None:
    """Patch MemberAgentConfig.validate_model to support groq: and claudecode: prefixes.

    This patch extends the model validator in MemberAgentConfig to accept
    groq: and claudecode: model prefixes in addition to the standard ones.

    Without this patch, MemberAgentConfig will reject models like
    'groq:llama-3.3-70b-versatile' even for custom agent types that
    specify their own type like 'playwright_markdown_fetch'.

    Called internally by patch_core().

    Note:
        Pydantic v2 compiles field validators at class definition time into
        __pydantic_validator__. Simply replacing the classmethod attribute does
        NOT affect the compiled validator. To properly patch, we must:
        1. Replace the func reference in __pydantic_decorators__
        2. Call model_rebuild(force=True) to recompile the validator
    """
    from pydantic import ValidationInfo

    from mixseek.models.member_agent import MemberAgentConfig

    # Access the Pydantic decorator that holds the validator reference
    dec = MemberAgentConfig.__pydantic_decorators__.field_validators["validate_model"]
    original_func = dec.func

    @classmethod  # type: ignore[misc]
    def patched_validate_model(
        cls: type[MemberAgentConfig], v: str, info: ValidationInfo
    ) -> str:
        """Extended validate_model that accepts groq: and claudecode: prefixes."""
        # Accept groq: and claudecode: prefixes
        if v.startswith(GROQ_PROVIDER_PREFIX) or v.startswith(
            CLAUDECODE_PROVIDER_PREFIX
        ):
            return v

        # Fall back to original validator for other cases
        return original_func(v, info)  # type: ignore[no-any-return]

    # Replace both the classmethod and the decorator's func reference
    MemberAgentConfig.validate_model = patched_validate_model  # type: ignore[assignment]
    dec.func = patched_validate_model.__func__.__get__(MemberAgentConfig)  # type: ignore[attr-defined]

    # Rebuild the Pydantic model to recompile validators with the patched function
    MemberAgentConfig.model_rebuild(force=True)


def _patch_aggregation_store() -> None:
    """Patch AggregationStore.save_aggregation for member tool usage warning.

    This patch adds a warning when Leader has members but calls none (Issue #19).
    The warning helps identify models that don't properly support function_tools.

    We patch save_aggregation because it receives MemberSubmissionsRecord
    which contains the total_count of member tool calls.

    Called internally by patch_core(). Stores the original method in
    _ORIGINAL_SAVE_AGGREGATION for potential restoration.

    Raises:
        ImportError: If AggregationStore or MemberSubmissionsRecord cannot be
            imported from mixseek-core. This indicates a version incompatibility
            or missing dependency.
    """
    global _ORIGINAL_SAVE_AGGREGATION

    from mixseek.storage.aggregation_store import AggregationStore

    _ORIGINAL_SAVE_AGGREGATION = AggregationStore.save_aggregation

    original_func = _ORIGINAL_SAVE_AGGREGATION

    from mixseek.agents.leader.models import MemberSubmissionsRecord
    from pydantic_ai.messages import ModelRequest, ModelResponse

    async def patched_save_aggregation(
        self: AggregationStore,
        execution_id: str,
        aggregated: MemberSubmissionsRecord,
        message_history: list[ModelRequest | ModelResponse],
    ) -> None:
        """Patched save_aggregation with member tool usage warning.

        This wrapper checks if the Leader called any member tools based on
        MemberSubmissionsRecord before calling the original method.
        """
        # Check member tool usage before saving (Issue #19)
        # LIMITATION: Cannot determine if team has members from AggregationStore context.
        # This warning may fire for teams with no members (false positive).
        # Future improvement: Pass team configuration or lookup member count from team_id.
        if aggregated.total_count == 0:
            logger.warning(
                "Leader did not call any member tools (team_id=%s, round=%d). "
                "Model may not support function_tools properly. "
                "Check if the model implementation handles "
                "model_request_parameters.function_tools.",
                aggregated.team_id,
                aggregated.round_number,
            )

        # Call original method
        await original_func(self, execution_id, aggregated, message_history)

    AggregationStore.save_aggregation = patched_save_aggregation  # type: ignore[method-assign]


def reset_aggregation_store_patch() -> None:
    """Reset AggregationStore.save_aggregation to original (for testing only)."""
    global _ORIGINAL_SAVE_AGGREGATION

    if _ORIGINAL_SAVE_AGGREGATION is not None:
        from mixseek.storage.aggregation_store import AggregationStore

        AggregationStore.save_aggregation = _ORIGINAL_SAVE_AGGREGATION  # type: ignore[method-assign]
        _ORIGINAL_SAVE_AGGREGATION = None


def _wrap_tool_function_for_mcp(
    original_func: Callable[..., Coroutine[object, object, str]],
    tool_name: str,
) -> Callable[..., Coroutine[object, object, str]]:
    """Wrap a pydantic-ai tool function to inject context from contextvar.

    Pydantic-ai tool functions expect a RunContext as the first argument,
    which is normally injected by the framework. When tools are called via
    MCP (bypassing pydantic-ai), we need to inject a mock context.

    This wrapper:
    1. Gets the current TeamDependencies from the contextvar
    2. Creates a MockRunContext with those deps
    3. Injects it as the first argument to the original function
    4. Measures execution time and logs via MemberAgentLogger (if available)
    5. Outputs verbose console log if MIXSEEK_VERBOSE is enabled

    Args:
        original_func: The original tool function that expects ctx as first arg.
        tool_name: Name of the tool (for logging).

    Returns:
        A wrapped function that injects the context automatically.
    """

    async def wrapped(**kwargs: object) -> str:
        deps = _current_deps.get()
        if deps is None:
            raise RuntimeError(
                f"Tool '{tool_name}' called without context. "
                "Ensure leader_agent.run() is wrapped to set _current_deps."
            )

        mock_ctx = MockRunContext(deps=deps)
        logger.debug(
            "[MCP Tool] Injecting context for tool '%s': execution_id=%s",
            tool_name,
            deps.execution_id,
        )

        # Ensure verbose logging is configured (lazy init after handlers are created)
        ensure_verbose_logging_configured()

        # Log tool start via unified verbose helper
        log_verbose_tool_start(tool_name, dict(kwargs))

        start_time = time.perf_counter()
        status: ToolStatus = "success"
        try:
            result = await original_func(mock_ctx, **kwargs)
            return result
        except Exception:
            status = "error"
            raise
        finally:
            execution_time_ms = int((time.perf_counter() - start_time) * 1000)

            # Log tool completion via unified verbose helper
            # (wrapped to prevent masking original exceptions)
            try:
                log_verbose_tool_done(tool_name, status, execution_time_ms)
            except Exception as log_error:
                logger.warning(
                    "Failed to log tool completion for '%s': %s",
                    tool_name,
                    log_error,
                    exc_info=True,
                )

            # Log tool invocation via MemberAgentLogger if logger is available on deps
            deps_logger = getattr(deps, "logger", None)
            if deps_logger is not None and hasattr(deps_logger, "log_tool_invocation"):
                try:
                    deps_logger.log_tool_invocation(
                        execution_id=deps.execution_id,
                        tool_name=tool_name,
                        parameters=dict(kwargs),
                        execution_time_ms=execution_time_ms,
                        status=status,
                    )
                except Exception as log_error:
                    logger.warning(
                        "Failed to log tool invocation for '%s': %s",
                        tool_name,
                        log_error,
                        exc_info=True,
                    )

    # Preserve function metadata (handle missing attributes gracefully)
    # Also handle Mock objects that may be used in tests
    try:
        wrapped.__name__ = original_func.__name__
    except (AttributeError, TypeError):
        # Ensure tool_name is a string (might be a Mock in tests)
        wrapped.__name__ = (
            str(tool_name) if not isinstance(tool_name, str) else tool_name
        )
    try:
        wrapped.__doc__ = original_func.__doc__
    except (AttributeError, TypeError) as e:
        logger.debug(
            "Could not copy __doc__ from original_func to wrapped function "
            "for tool '%s': %s",
            tool_name,
            e,
        )

    return wrapped


def _create_mcp_compatible_tool(tool: Tool[object]) -> ToolLike:
    """Create an MCP-compatible tool by wrapping the function.

    This creates a new tool-like object with the function wrapped
    to inject context from the contextvar.

    Args:
        tool: A pydantic-ai Tool object.

    Returns:
        A modified tool object with wrapped function.

    Raises:
        TypeError: If dataclasses.replace() fails and wrapper creation also fails.
    """
    from dataclasses import replace

    original_function = tool.function
    # Ensure tool_name is a string (handle Mock objects in tests)
    tool_name = tool.name if isinstance(tool.name, str) else str(tool.name)
    wrapped_function = _wrap_tool_function_for_mcp(original_function, tool_name)

    # Create a new tool with the wrapped function
    # pydantic_ai.tools.Tool is a dataclass, so we can use replace()
    new_tool = replace(tool, function=wrapped_function)
    return new_tool


def _patch_leader_agent() -> None:
    """Patch create_leader_agent to call set_agent_toolsets for ClaudeCodeModel.

    This patch intercepts create_leader_agent to extract Tool objects from
    the Leader agent's _function_toolset and pass them to ClaudeCodeModel's
    set_agent_toolsets() method. This enables ClaudeCode to properly handle
    member agent tools.

    The patch also wraps tool functions to inject context from a contextvar,
    which is necessary because MCP tool calls bypass pydantic-ai's normal
    context injection.

    Background:
        - claudecode-model Issue #37 added set_agent_toolsets()
        - Pydantic AI's standard flow passes ToolDefinition (schema only)
        - set_agent_toolsets() needs Tool objects (executable functions)
        - Without this patch, Leader warns "did not call any member tools"
        - MCP calls don't have access to pydantic-ai's RunContext

    Called internally by patch_core(). Stores the original function in
    _ORIGINAL_CREATE_LEADER_AGENT for potential restoration.

    Raises:
        ImportError: If create_leader_agent or ClaudeCodeModel cannot be imported.
            This indicates a version incompatibility or missing dependency.
    """
    global _ORIGINAL_CREATE_LEADER_AGENT

    from claudecode_model import ClaudeCodeModel

    import mixseek.agents.leader.agent as leader_module
    from mixseek.agents.leader.agent import create_leader_agent as original_func

    _ORIGINAL_CREATE_LEADER_AGENT = original_func

    def patched_create_leader_agent(
        team_config: TeamConfig,
        member_agents: Mapping[str, object],
    ) -> Agent[TeamDependencies, str]:
        """Patched create_leader_agent with ClaudeCodeModel toolset support.

        This wrapper calls the original create_leader_agent, then:
        1. Extracts Tool objects from the leader's _function_toolset
        2. Wraps tool functions to inject context from contextvar
        3. Passes wrapped tools to ClaudeCodeModel.set_agent_toolsets()
        4. Patches leader_agent.run() to set the contextvar
        """
        leader_agent = original_func(team_config, member_agents)

        model = leader_agent.model
        if isinstance(model, ClaudeCodeModel):
            # Extract Tool objects from the leader's function toolset
            # _function_toolset is Pydantic AI internal API (version-specific)
            # Use try-except to handle potential API changes gracefully
            try:
                toolset = getattr(leader_agent, "_function_toolset", None)
                if toolset is None:
                    logger.warning(
                        "Could not access _function_toolset on Leader agent (team=%s). "
                        "Pydantic AI internal API may have changed.",
                        team_config.team_id,
                    )
                    return leader_agent
                tools = list(toolset.tools.values())
            except AttributeError as e:
                logger.warning(
                    "Pydantic AI internal API (_function_toolset) not found: %s",
                    e,
                )
                return leader_agent

            if tools:
                # Wrap tools to inject context from contextvar
                mcp_tools = [_create_mcp_compatible_tool(t) for t in tools]

                tool_names = [t.name for t in mcp_tools]
                logger.debug(
                    "Wrapping %d tools for MCP compatibility: %s",
                    len(mcp_tools),
                    tool_names,
                )
                model.set_agent_toolsets(mcp_tools)  # type: ignore[arg-type]

                logger.debug(
                    "Applied set_agent_toolsets with %d tools for team %s",
                    len(mcp_tools),
                    team_config.team_id,
                )

                # Patch leader_agent.run() to set the contextvar
                original_run = leader_agent.run

                async def patched_run(
                    *args: object,
                    deps: TeamDependencies | None = None,
                    **kwargs: object,
                ) -> object:
                    """Patched run() that sets _current_deps contextvar."""
                    if deps is not None:
                        token = _current_deps.set(deps)
                        logger.debug(
                            "[Patched run] Set _current_deps: execution_id=%s",
                            deps.execution_id,
                        )
                        try:
                            return await original_run(*args, deps=deps, **kwargs)  # type: ignore[call-overload]
                        finally:
                            _current_deps.reset(token)
                    else:
                        return await original_run(*args, **kwargs)  # type: ignore[call-overload]

                # Replace run method
                leader_agent.run = patched_run  # type: ignore[method-assign, assignment]
                logger.debug("Patched leader_agent.run() to set _current_deps")
            else:
                logger.debug(
                    "No tools found in Leader's _function_toolset for team %s",
                    team_config.team_id,
                )

        return leader_agent

    leader_module.create_leader_agent = patched_create_leader_agent

    # Also patch modules that have already imported create_leader_agent directly
    # These modules hold their own reference that won't be updated by
    # patching leader_module.create_leader_agent alone
    _patch_leader_agent_module_references(patched_create_leader_agent)


def _patch_leader_agent_module_references(
    patched_func: Callable[
        [TeamConfig, Mapping[str, object]], Agent[TeamDependencies, str]
    ],
) -> None:
    """Patch all modules that have imported create_leader_agent directly.

    mixseek-core has several modules that use:
        from mixseek.agents.leader.agent import create_leader_agent

    These create local references that aren't updated when we patch the
    leader_module. We need to explicitly update these references.

    Note:
        This function imports the target modules if they haven't been imported yet.
        This ensures the patch is applied regardless of import order.

    Args:
        patched_func: The patched create_leader_agent function
    """
    import importlib

    # List of modules known to import create_leader_agent directly
    modules_to_patch = [
        "mixseek.round_controller.controller",
        "mixseek.cli.commands.team",
    ]

    for module_name in modules_to_patch:
        try:
            # Import the module if not already imported
            module = importlib.import_module(module_name)
            if hasattr(module, "create_leader_agent"):
                setattr(module, "create_leader_agent", patched_func)
                logger.debug("Patched create_leader_agent reference in %s", module_name)
        except ImportError as e:
            logger.warning(
                "Could not import %s for patching create_leader_agent: %s",
                module_name,
                e,
            )


def reset_leader_agent_patch() -> None:
    """Reset create_leader_agent to original (for testing only).

    This function restores the original create_leader_agent function
    that was stored before patching. It should only be used in tests
    to ensure a clean state between test cases.
    """
    global _ORIGINAL_CREATE_LEADER_AGENT

    if _ORIGINAL_CREATE_LEADER_AGENT is not None:
        import mixseek.agents.leader.agent as leader_module

        leader_module.create_leader_agent = _ORIGINAL_CREATE_LEADER_AGENT  # type: ignore[assignment]
        _ORIGINAL_CREATE_LEADER_AGENT = None
