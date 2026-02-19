"""Tests for MemberAgentConfig.validate_model patch (Issue #50).

Tests verify that _patch_member_agent_config_validator() properly patches
Pydantic v2's compiled validator via __pydantic_decorators__ and model_rebuild().

The patch is applied in conftest.py::pytest_configure via patch_core().
"""

import pytest
from pydantic import ValidationError

from mixseek.models.member_agent import MemberAgentConfig


class TestMemberAgentConfigValidatorPatch:
    """Tests for MemberAgentConfig.validate_model after patch_core().

    Issue #50: _patch_member_agent_config_validator() was only replacing
    the classmethod attribute, but Pydantic v2 compiles validators at class
    definition time. The fix replaces dec.func in __pydantic_decorators__
    and calls model_rebuild(force=True) to recompile.
    """

    def test_claudecode_model_accepted(self) -> None:
        """claudecode: prefix should be accepted after patch_core()."""
        config = MemberAgentConfig(
            name="test-agent",
            type="claudecode_plain",
            model="claudecode:claude-opus-4-6",
        )
        assert config.model == "claudecode:claude-opus-4-6"

    def test_groq_model_accepted(self) -> None:
        """groq: prefix should be accepted after patch_core()."""
        config = MemberAgentConfig(
            name="test-agent",
            type="groq_plain",
            model="groq:llama-3.3-70b-versatile",
        )
        assert config.model == "groq:llama-3.3-70b-versatile"

    def test_google_gla_model_still_accepted(self) -> None:
        """google-gla: prefix should still work (existing behavior preserved)."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="google-gla:gemini-2.5-flash",
        )
        assert config.model == "google-gla:gemini-2.5-flash"

    def test_openai_model_still_accepted(self) -> None:
        """openai: prefix should still work (existing behavior preserved)."""
        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="openai:gpt-4o",
        )
        assert config.model == "openai:gpt-4o"

    def test_invalid_model_rejected(self) -> None:
        """Invalid model prefix should still be rejected."""
        with pytest.raises(ValidationError, match="Unsupported model"):
            MemberAgentConfig(
                name="test-agent",
                type="plain",
                model="invalid-model",
            )

    def test_claudecode_with_playwright_agent_type(self) -> None:
        """claudecode: model with playwright_markdown_fetch type should work."""
        config = MemberAgentConfig(
            name="browser-agent",
            type="playwright_markdown_fetch",
            model="claudecode:claude-sonnet-4-5",
        )
        assert config.model == "claudecode:claude-sonnet-4-5"

    def test_groq_with_web_search_agent_type(self) -> None:
        """groq: model with groq_web_search type should work."""
        config = MemberAgentConfig(
            name="search-agent",
            type="groq_web_search",
            model="groq:llama-3.3-70b-versatile",
        )
        assert config.model == "groq:llama-3.3-70b-versatile"
