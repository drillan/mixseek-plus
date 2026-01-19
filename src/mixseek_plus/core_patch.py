"""Core patching functionality for mixseek-core integration.

This module provides patch_core() which extends mixseek-core's
create_authenticated_model to support Groq and ClaudeCode models.

Also provides configure_claudecode_tool_settings() for configuring
ClaudeCode-specific tool settings (permission_mode, working_directory, etc.)
that are used by Leader/Evaluator/Judgment agents.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic_ai.models import Model

from mixseek_plus.providers import CLAUDECODE_PROVIDER_PREFIX, GROQ_PROVIDER_PREFIX
from mixseek_plus.providers.claudecode import ClaudeCodeToolSettings

if TYPE_CHECKING:
    from mixseek.config.schema import TeamSettings

logger = logging.getLogger(__name__)

# Module-level state to track if patch has been applied
_PATCH_APPLIED = False
_ORIGINAL_FUNCTION: Callable[[str], Model] | None = None

# Module-level state for ClaudeCode tool_settings
_CLAUDECODE_TOOL_SETTINGS: ClaudeCodeToolSettings | None = None

# Module-level state for ConfigurationManager patch
# TeamSettings is imported at runtime in _patch_configuration_manager()
_ORIGINAL_LOAD_TEAM_SETTINGS: Callable[..., TeamSettings] | None = None

# Module-level state for AggregationStore patch (Issue #19)
_ORIGINAL_SAVE_AGGREGATION: Callable[..., Coroutine[Any, Any, None]] | None = None

# Module-level state for create_leader_agent patch (Issue #23)
_ORIGINAL_CREATE_LEADER_AGENT: Callable[..., Any] | None = None


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


def apply_leader_tool_settings(leader_dict: dict[str, object]) -> None:
    """Apply leader tool_settings from TOML configuration.

    Extracts tool_settings.claudecode from leader dict and
    calls configure_claudecode_tool_settings() automatically.

    Args:
        leader_dict: TeamSettings.leader dict from TOML
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
            configure_claudecode_tool_settings(claudecode_settings)  # type: ignore[arg-type]
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

        # Auto-apply leader.tool_settings.claudecode with defensive programming
        leader = getattr(team_settings, "leader", None)
        if leader is not None:
            try:
                apply_leader_tool_settings(leader)
            except Exception as e:
                logger.warning("leader.tool_settings の自動適用に失敗しました: %s", e)
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

    # Patch create_leader_agent for ClaudeCodeModel set_agent_toolsets (Issue #23)
    _patch_leader_agent()

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

        AggregationStore.save_aggregation = _ORIGINAL_SAVE_AGGREGATION  # type: ignore[method-assign, assignment]
        _ORIGINAL_SAVE_AGGREGATION = None


def _patch_leader_agent() -> None:
    """Patch create_leader_agent to call set_agent_toolsets for ClaudeCodeModel.

    This patch intercepts create_leader_agent to extract Tool objects from
    the Leader agent's _function_toolset and pass them to ClaudeCodeModel's
    set_agent_toolsets() method. This enables ClaudeCode to properly handle
    member agent tools.

    Background:
        - claudecode-model Issue #37 added set_agent_toolsets()
        - Pydantic AI's standard flow passes ToolDefinition (schema only)
        - set_agent_toolsets() needs Tool objects (executable functions)
        - Without this patch, Leader warns "did not call any member tools"

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
    from mixseek.agents.leader.config import TeamConfig

    _ORIGINAL_CREATE_LEADER_AGENT = original_func

    def patched_create_leader_agent(
        team_config: TeamConfig,
        member_agents: dict[str, Any],
    ) -> Any:
        """Patched create_leader_agent with ClaudeCodeModel toolset support.

        This wrapper calls the original create_leader_agent, then extracts
        Tool objects from the leader's _function_toolset and passes them
        to ClaudeCodeModel.set_agent_toolsets() if applicable.
        """
        leader_agent = original_func(team_config, member_agents)

        model = leader_agent.model
        if isinstance(model, ClaudeCodeModel):
            # Extract Tool objects from the leader's function toolset
            # _function_toolset is Pydantic AI internal API (version-specific)
            tools = list(leader_agent._function_toolset.tools.values())
            if tools:
                model.set_agent_toolsets(tools)  # type: ignore[arg-type]
                logger.debug(
                    "Applied set_agent_toolsets with %d tools for team %s",
                    len(tools),
                    team_config.team_id,
                )

        return leader_agent

    leader_module.create_leader_agent = patched_create_leader_agent  # type: ignore[assignment]


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
