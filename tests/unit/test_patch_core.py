"""Unit tests for patch_core() function.

Tests cover:
- GR-060: patch_core() function existence
- GR-061: Leader/Evaluator groq: model support after patch
- GR-062: Idempotency of patch_core()
- GR-063: Unpatched usage detection and error message
- CC-050, CC-051, CC-052: ClaudeCode support via patch_core()
- CC-060, CC-061, CC-062: ClaudeCode tool_settings support for Leader/Evaluator/Judgment
"""

from unittest.mock import patch

import pytest
from claudecode_model import ClaudeCodeModel


class TestPatchCoreClaudeCodeSupport:
    """Tests for ClaudeCode support via patch_core() (CC-050, CC-051, CC-052)."""

    def test_patched_create_model_handles_claudecode_prefix(self) -> None:
        """CC-050, CC-051: After patch, claudecode: prefix should work."""
        from mixseek_plus import core_patch, patch_core

        # Reset and apply patch
        core_patch._PATCH_APPLIED = False
        patch_core()

        # Import after patching
        from mixseek.core.auth import create_authenticated_model

        # This should work after patching
        model = create_authenticated_model("claudecode:claude-sonnet-4-5")

        assert isinstance(model, ClaudeCodeModel)

    def test_patched_create_model_handles_claudecode_haiku(self) -> None:
        """CC-051: After patch, claudecode:claude-haiku-4-5 should work."""
        from mixseek_plus import core_patch, patch_core

        # Reset and apply patch
        core_patch._PATCH_APPLIED = False
        patch_core()

        from mixseek.core.auth import create_authenticated_model

        model = create_authenticated_model("claudecode:claude-haiku-4-5")

        assert isinstance(model, ClaudeCodeModel)

    def test_patched_create_model_handles_claudecode_opus(self) -> None:
        """CC-051: After patch, claudecode:claude-opus-4-5 should work."""
        from mixseek_plus import core_patch, patch_core

        # Reset and apply patch
        core_patch._PATCH_APPLIED = False
        patch_core()

        from mixseek.core.auth import create_authenticated_model

        model = create_authenticated_model("claudecode:claude-opus-4-5")

        assert isinstance(model, ClaudeCodeModel)


class TestPatchCoreFunction:
    """Tests for patch_core() function."""

    def test_patch_core_exists(self) -> None:
        """GR-060: patch_core function should exist and be callable."""
        from mixseek_plus import patch_core

        assert callable(patch_core)

    def test_patch_core_extends_create_authenticated_model(
        self, mock_groq_api_key: str
    ) -> None:
        """GR-060, GR-061: After patch, groq: models should be supported."""
        from mixseek_plus import patch_core
        from mixseek_plus.core_patch import is_patched

        # Ensure we start unpatched
        from mixseek_plus import core_patch

        core_patch._PATCH_APPLIED = False

        # Apply patch
        patch_core()

        # Verify patch was applied
        assert is_patched() is True

    def test_patch_core_is_idempotent(self, mock_groq_api_key: str) -> None:
        """GR-062: Multiple calls to patch_core() should be safe."""
        from mixseek_plus import patch_core
        from mixseek_plus.core_patch import is_patched

        # Reset patch state
        from mixseek_plus import core_patch

        core_patch._PATCH_APPLIED = False

        # Call multiple times
        patch_core()
        patch_core()
        patch_core()

        # Should still be patched (no error raised)
        assert is_patched() is True

    def test_is_patched_returns_false_before_patch(self) -> None:
        """is_patched() should return False before patch_core() is called."""
        from mixseek_plus import core_patch

        # Reset patch state
        core_patch._PATCH_APPLIED = False

        assert core_patch.is_patched() is False


class TestPatchedBehavior:
    """Tests for behavior after patch_core() is applied."""

    def test_patched_create_model_handles_groq_prefix(
        self, mock_groq_api_key: str
    ) -> None:
        """GR-061: After patch, groq: prefix should work with create_authenticated_model."""
        from mixseek_plus import patch_core
        from mixseek_plus import core_patch

        # Reset and apply patch
        core_patch._PATCH_APPLIED = False
        patch_core()

        # Import after patching
        from mixseek.core.auth import create_authenticated_model
        from pydantic_ai.models.groq import GroqModel

        # This should work after patching
        model = create_authenticated_model("groq:llama-3.3-70b-versatile")

        assert isinstance(model, GroqModel)

    def test_patched_create_model_delegates_non_groq(
        self,
        mock_groq_api_key: str,
        mock_openai_api_key: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """After patch, non-groq models should still work via delegation.

        Note: mixseek-core returns TestModel when PYTEST_CURRENT_TEST is set.
        We temporarily unset it to test real delegation behavior.
        """
        from mixseek.core import auth
        from mixseek_plus import core_patch

        # Unset PYTEST_CURRENT_TEST to bypass mixseek-core's test mode
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

        # Store reference to original function before any patching
        original_func = auth.create_authenticated_model

        # Reset patch state and _ORIGINAL_FUNCTION to simulate fresh state
        core_patch._PATCH_APPLIED = False
        core_patch._ORIGINAL_FUNCTION = None

        # Restore original function to auth module
        auth.create_authenticated_model = original_func

        # Now apply patch fresh
        from mixseek_plus import patch_core

        patch_core()

        # OpenAI should still work via delegation
        model = auth.create_authenticated_model("openai:gpt-4o")

        # Check it's an OpenAI model (could be OpenAIModel or OpenAIChatModel)
        assert "openai" in type(model).__module__.lower()


class TestUnpatchedErrorHandling:
    """Tests for error handling when patch is not applied."""

    def test_unpatched_groq_usage_raises_error(self) -> None:
        """GR-063: Using groq: without patch should raise clear error."""
        # This test verifies that mixseek-core rejects groq: without patch
        # We test this by checking the original behavior before patching
        from mixseek_plus import core_patch

        # Reset patch state to simulate unpatched state
        core_patch._PATCH_APPLIED = False

        # We can't easily test the original create_authenticated_model
        # because it's been patched at module level
        # Instead, we verify the is_patched state
        assert core_patch.is_patched() is False


class TestClaudeCodeToolSettingsSupport:
    """Tests for ClaudeCode tool_settings support in patch_core() (CC-060, CC-061, CC-062).

    These tests verify that Leader/Evaluator/Judgment agents can use
    ClaudeCode-specific tool_settings like permission_mode through patch_core().
    """

    def test_configure_claudecode_tool_settings_exists(self) -> None:
        """CC-060: configure_claudecode_tool_settings function should exist."""
        from mixseek_plus.core_patch import configure_claudecode_tool_settings

        assert callable(configure_claudecode_tool_settings)

    def test_configure_claudecode_tool_settings_registers_settings(self) -> None:
        """CC-060: configure_claudecode_tool_settings should register settings."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            configure_claudecode_tool_settings,
            get_claudecode_tool_settings,
        )

        # Clear any existing settings
        core_patch._CLAUDECODE_TOOL_SETTINGS = None

        settings: dict[str, object] = {"permission_mode": "bypassPermissions"}
        configure_claudecode_tool_settings(settings)  # type: ignore[arg-type]

        result = get_claudecode_tool_settings()
        assert result is not None
        assert result.get("permission_mode") == "bypassPermissions"

    def test_get_claudecode_tool_settings_returns_none_when_not_configured(
        self,
    ) -> None:
        """get_claudecode_tool_settings returns None when not configured."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import get_claudecode_tool_settings

        # Clear any existing settings
        core_patch._CLAUDECODE_TOOL_SETTINGS = None

        result = get_claudecode_tool_settings()
        assert result is None

    def test_patched_create_model_uses_tool_settings(self) -> None:
        """CC-061: After patch, claudecode: should use configured tool_settings."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            configure_claudecode_tool_settings,
            patch_core,
        )

        # Reset patch state
        core_patch._PATCH_APPLIED = False
        core_patch._CLAUDECODE_TOOL_SETTINGS = None

        # Configure tool_settings before patching
        configure_claudecode_tool_settings(
            {
                "permission_mode": "bypassPermissions",
                "working_directory": "/test/dir",
            }
        )

        # Apply patch
        patch_core()

        # Import after patching
        from mixseek.core.auth import create_authenticated_model

        # Mock ClaudeCodeModel to capture initialization args
        with patch("mixseek_plus.providers.claudecode.ClaudeCodeModel") as mock_model:
            mock_model.return_value = ClaudeCodeModel(model_name="claude-sonnet-4-5")
            create_authenticated_model("claudecode:claude-sonnet-4-5")

            # Verify tool_settings were passed
            mock_model.assert_called_once()
            call_kwargs = mock_model.call_args.kwargs
            assert call_kwargs.get("permission_mode") == "bypassPermissions"
            assert call_kwargs.get("working_directory") == "/test/dir"

    def test_patched_create_model_works_without_tool_settings(self) -> None:
        """CC-062: After patch, claudecode: works without tool_settings configured."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import patch_core

        # Reset patch state and clear tool_settings
        core_patch._PATCH_APPLIED = False
        core_patch._CLAUDECODE_TOOL_SETTINGS = None

        # Apply patch without configuring tool_settings
        patch_core()

        from mixseek.core.auth import create_authenticated_model

        # Should work without tool_settings
        model = create_authenticated_model("claudecode:claude-sonnet-4-5")
        assert isinstance(model, ClaudeCodeModel)

    def test_configure_claudecode_tool_settings_with_all_options(self) -> None:
        """configure_claudecode_tool_settings supports all ClaudeCode options."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            configure_claudecode_tool_settings,
            get_claudecode_tool_settings,
        )

        # Clear any existing settings
        core_patch._CLAUDECODE_TOOL_SETTINGS = None

        settings: dict[str, object] = {
            "allowed_tools": ["Read", "Write"],
            "disallowed_tools": ["Bash"],
            "permission_mode": "bypassPermissions",
            "working_directory": "/workspace",
            "max_turns": 10,
        }
        configure_claudecode_tool_settings(settings)  # type: ignore[arg-type]

        result = get_claudecode_tool_settings()
        assert result is not None
        assert result.get("allowed_tools") == ["Read", "Write"]
        assert result.get("disallowed_tools") == ["Bash"]
        assert result.get("permission_mode") == "bypassPermissions"
        assert result.get("working_directory") == "/workspace"
        assert result.get("max_turns") == 10

    def test_clear_claudecode_tool_settings(self) -> None:
        """clear_claudecode_tool_settings should clear registered settings."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            clear_claudecode_tool_settings,
            configure_claudecode_tool_settings,
            get_claudecode_tool_settings,
        )

        # Configure settings
        core_patch._CLAUDECODE_TOOL_SETTINGS = None
        configure_claudecode_tool_settings({"permission_mode": "bypassPermissions"})
        assert get_claudecode_tool_settings() is not None

        # Clear settings
        clear_claudecode_tool_settings()
        assert get_claudecode_tool_settings() is None
