"""Tests for unpatched groq: usage detection (GR-063).

This module tests that when groq: prefix is used without calling patch_core(),
a clear and helpful error message is displayed to guide the user.
"""

import pytest

from mixseek_plus.core_patch import is_patched, reset_patch_state


class TestUnpatchedGroqUsageDetection:
    """Test suite for unpatched groq: usage detection."""

    def setup_method(self) -> None:
        """Reset patch state before each test."""
        reset_patch_state()

    def teardown_method(self) -> None:
        """Reset patch state after each test."""
        reset_patch_state()

    def test_unpatched_groq_usage_raises_error(self, mock_groq_api_key: str) -> None:
        """Test that using groq: without patch_core() raises a helpful error.

        GR-063: When groq: is used without patch_core(), error should:
        1. Clearly indicate the problem
        2. Provide guidance to call patch_core()
        """
        from mixseek_plus.core_patch import check_groq_support, GroqNotPatchedError

        # Ensure patch is not applied
        assert not is_patched()

        # Attempting to check groq support when not patched should raise error
        with pytest.raises(GroqNotPatchedError) as exc_info:
            check_groq_support()

        error_message = str(exc_info.value)
        # Should mention patch_core
        assert "patch_core" in error_message.lower()
        # Should indicate it's about Groq
        assert "groq" in error_message.lower()

    def test_error_message_contains_solution_guidance(
        self, mock_groq_api_key: str
    ) -> None:
        """Test that error message includes how to fix the issue.

        The error message should guide the user to call mixseek_plus.patch_core().
        """
        from mixseek_plus.core_patch import check_groq_support, GroqNotPatchedError

        reset_patch_state()

        with pytest.raises(GroqNotPatchedError) as exc_info:
            check_groq_support()

        error_message = str(exc_info.value)
        # Should include the fix suggestion
        assert "mixseek_plus.patch_core()" in error_message

    def test_no_error_after_patch_core(self, mock_groq_api_key: str) -> None:
        """Test that no error is raised after patch_core() is called."""
        from mixseek_plus.core_patch import check_groq_support, patch_core

        # Apply the patch
        patch_core()
        assert is_patched()

        # Should not raise any error
        check_groq_support()  # No exception should be raised

    def test_unpatched_error_is_descriptive(self, mock_groq_api_key: str) -> None:
        """Test that the error message is descriptive for developers.

        The error should explain:
        - What went wrong (groq: used without patching)
        - Why it happened (patch not applied)
        - How to fix it (call patch_core)
        """
        from mixseek_plus.core_patch import GroqNotPatchedError

        error = GroqNotPatchedError()
        message = str(error)

        # Check for key informative components
        assert len(message) > 50  # Should be reasonably detailed
        assert "groq" in message.lower()
        assert "patch" in message.lower()


class TestGroqNotPatchedErrorClass:
    """Test the GroqNotPatchedError exception class."""

    def test_error_inherits_from_exception(self) -> None:
        """Test that GroqNotPatchedError is a proper exception."""
        from mixseek_plus.core_patch import GroqNotPatchedError

        assert issubclass(GroqNotPatchedError, Exception)

    def test_error_can_be_caught_as_exception(self) -> None:
        """Test that GroqNotPatchedError can be caught."""
        from mixseek_plus.core_patch import GroqNotPatchedError

        try:
            raise GroqNotPatchedError()
        except Exception as e:
            assert isinstance(e, GroqNotPatchedError)

    def test_error_has_default_message(self) -> None:
        """Test that GroqNotPatchedError has a meaningful default message."""
        from mixseek_plus.core_patch import GroqNotPatchedError

        error = GroqNotPatchedError()
        assert str(error)  # Should have a message
        assert "patch_core" in str(error).lower()
