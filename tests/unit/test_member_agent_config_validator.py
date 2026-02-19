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

    @pytest.mark.parametrize(
        ("name", "agent_type", "model"),
        [
            ("test-agent", "claudecode_plain", "claudecode:claude-opus-4-6"),
            ("test-agent", "groq_plain", "groq:llama-3.3-70b-versatile"),
            ("test-agent", "custom", "google-gla:gemini-2.5-flash"),
            ("test-agent", "custom", "openai:gpt-4o"),
            (
                "browser-agent",
                "playwright_markdown_fetch",
                "claudecode:claude-sonnet-4-5",
            ),
            ("search-agent", "groq_web_search", "groq:llama-3.3-70b-versatile"),
        ],
        ids=[
            "claudecode-prefix",
            "groq-prefix",
            "google-gla-prefix-preserved",
            "openai-prefix-preserved",
            "claudecode-with-playwright-type",
            "groq-with-web-search-type",
        ],
    )
    def test_valid_model_accepted(self, name: str, agent_type: str, model: str) -> None:
        """Valid model prefixes should be accepted after patch_core()."""
        config = MemberAgentConfig(name=name, type=agent_type, model=model)
        assert config.model == model

    def test_invalid_model_rejected(self) -> None:
        """Invalid model prefix should still be rejected."""
        with pytest.raises(ValidationError, match="Unsupported model"):
            MemberAgentConfig(
                name="test-agent",
                type="plain",
                model="invalid-model",
            )
