"""Core patching functionality for mixseek-core integration.

This module provides patch_core() which extends mixseek-core's
create_authenticated_model to support Groq and ClaudeCode models.
"""

from collections.abc import Callable

from pydantic_ai.models import Model

# Module-level state to track if patch has been applied
_PATCH_APPLIED = False
_ORIGINAL_FUNCTION: Callable[[str], Model] | None = None

# Constants for provider prefixes
GROQ_PROVIDER_PREFIX = "groq:"
CLAUDECODE_PROVIDER_PREFIX = "claudecode:"


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
            return create_claudecode_model(model_name)
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
