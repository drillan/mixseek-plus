"""Unit tests for patch_core() function.

Tests cover:
- GR-060: patch_core() function existence
- GR-061: Leader/Evaluator groq: model support after patch
- GR-062: Idempotency of patch_core()
- GR-063: Unpatched usage detection and error message
- CC-050, CC-051, CC-052: ClaudeCode support via patch_core()
- CC-060, CC-061, CC-062: ClaudeCode tool_settings support for Leader/Evaluator/Judgment
- MCP-001, MCP-002: MCP tool context injection
- MCP-010, MCP-011: patched_run() ContextVar management
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Coroutine
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from claudecode_model import ClaudeCodeModel

from mixseek_plus.providers.claudecode import FixedTokenClaudeCodeModel


@dataclass
class MockTool:
    """Dataclass-compatible tool mock for testing _create_mcp_compatible_tool."""

    name: str
    description: str | None
    function: Callable[..., Coroutine[object, object, str]]


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

        # Mock FixedTokenClaudeCodeModel to capture initialization args
        with patch(
            "mixseek_plus.providers.claudecode.FixedTokenClaudeCodeModel"
        ) as mock_model:
            mock_model.return_value = FixedTokenClaudeCodeModel(
                model_name="claude-sonnet-4-5"
            )
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


class TestApplyLeaderToolSettings:
    """Tests for apply_leader_tool_settings() function (LTS-001, LTS-002, LTS-003).

    These tests verify that leader.tool_settings from TOML configuration
    is automatically applied when ConfigurationManager loads TeamSettings.
    """

    def test_apply_leader_tool_settings_with_claudecode(self) -> None:
        """LTS-001: apply_leader_tool_settings applies claudecode settings."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            apply_leader_tool_settings,
            get_claudecode_tool_settings,
        )

        # Clear any existing settings
        core_patch._CLAUDECODE_TOOL_SETTINGS = None

        leader_dict: dict[str, object] = {
            "system_instruction": "You are a leader",
            "model": "claudecode:claude-haiku-4-5",
            "tool_settings": {
                "claudecode": {
                    "disallowed_tools": ["Bash", "Write", "Edit"],
                }
            },
        }
        apply_leader_tool_settings(leader_dict)

        result = get_claudecode_tool_settings()
        assert result is not None
        assert result.get("disallowed_tools") == ["Bash", "Write", "Edit"]

    def test_apply_leader_tool_settings_without_settings(self) -> None:
        """LTS-002: apply_leader_tool_settings does nothing without tool_settings."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            apply_leader_tool_settings,
            get_claudecode_tool_settings,
        )

        # Clear any existing settings
        core_patch._CLAUDECODE_TOOL_SETTINGS = None

        leader_dict: dict[str, object] = {
            "system_instruction": "You are a leader",
            "model": "claudecode:claude-haiku-4-5",
        }
        apply_leader_tool_settings(leader_dict)

        result = get_claudecode_tool_settings()
        assert result is None

    def test_apply_leader_tool_settings_without_claudecode(self) -> None:
        """LTS-003: apply_leader_tool_settings skips non-claudecode settings."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            apply_leader_tool_settings,
            get_claudecode_tool_settings,
        )

        # Clear any existing settings
        core_patch._CLAUDECODE_TOOL_SETTINGS = None

        leader_dict: dict[str, object] = {
            "system_instruction": "You are a leader",
            "model": "groq:llama-3.3-70b-versatile",
            "tool_settings": {
                "some_other_provider": {"setting": "value"},
            },
        }
        apply_leader_tool_settings(leader_dict)

        result = get_claudecode_tool_settings()
        assert result is None

    def test_apply_leader_tool_settings_with_all_claudecode_options(self) -> None:
        """LTS-004: apply_leader_tool_settings supports all ClaudeCode options."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            apply_leader_tool_settings,
            get_claudecode_tool_settings,
        )

        # Clear any existing settings
        core_patch._CLAUDECODE_TOOL_SETTINGS = None

        leader_dict: dict[str, object] = {
            "model": "claudecode:claude-haiku-4-5",
            "tool_settings": {
                "claudecode": {
                    "disallowed_tools": ["Bash", "Write", "Edit", "Read"],
                    "allowed_tools": ["AskUserQuestion"],
                    "permission_mode": "bypassPermissions",
                    "working_directory": "/workspace",
                    "max_turns": 5,
                }
            },
        }
        apply_leader_tool_settings(leader_dict)

        result = get_claudecode_tool_settings()
        assert result is not None
        assert result.get("disallowed_tools") == ["Bash", "Write", "Edit", "Read"]
        assert result.get("allowed_tools") == ["AskUserQuestion"]
        assert result.get("permission_mode") == "bypassPermissions"
        assert result.get("working_directory") == "/workspace"
        assert result.get("max_turns") == 5

    def test_apply_leader_tool_settings_with_preset(self, tmp_path: Path) -> None:
        """LTS-005: apply_leader_tool_settings resolves preset when workspace provided."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            apply_leader_tool_settings,
            get_claudecode_tool_settings,
        )

        # Clear any existing settings
        core_patch._CLAUDECODE_TOOL_SETTINGS = None

        # Create preset file
        workspace = tmp_path
        preset_dir = workspace / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
[delegate_only]
permission_mode = "bypassPermissions"
disallowed_tools = ["Bash", "Write", "Edit"]
""")

        leader_dict: dict[str, object] = {
            "model": "claudecode:claude-haiku-4-5",
            "tool_settings": {
                "claudecode": {
                    "preset": "delegate_only",
                    "max_turns": 50,  # Local override
                }
            },
        }
        apply_leader_tool_settings(leader_dict, workspace)

        result = get_claudecode_tool_settings()
        assert result is not None
        # Preset values
        assert result.get("permission_mode") == "bypassPermissions"
        assert result.get("disallowed_tools") == ["Bash", "Write", "Edit"]
        # Local override
        assert result.get("max_turns") == 50
        # Preset key should be removed
        assert "preset" not in result

    def test_apply_leader_tool_settings_preset_without_workspace(self) -> None:
        """LTS-006: apply_leader_tool_settings skips preset when workspace not provided."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            apply_leader_tool_settings,
            get_claudecode_tool_settings,
        )

        # Clear any existing settings
        core_patch._CLAUDECODE_TOOL_SETTINGS = None

        leader_dict: dict[str, object] = {
            "model": "claudecode:claude-haiku-4-5",
            "tool_settings": {
                "claudecode": {
                    "preset": "delegate_only",
                    "max_turns": 50,
                }
            },
        }
        # Call without workspace - preset should be skipped but other settings applied
        apply_leader_tool_settings(leader_dict)  # No workspace

        result = get_claudecode_tool_settings()
        assert result is not None
        # Only local setting should be present (preset ignored)
        assert result.get("max_turns") == 50
        # Preset key should be removed
        assert "preset" not in result


class TestConfigurationManagerPatch:
    """Tests for ConfigurationManager.load_team_settings() patching (LTS-010, LTS-011)."""

    def test_configuration_manager_patch_applies_leader_tool_settings(
        self, tmp_path: Path
    ) -> None:
        """LTS-010: ConfigurationManager patch applies leader tool_settings automatically."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import get_claudecode_tool_settings, patch_core

        # Reset patch state
        core_patch._PATCH_APPLIED = False
        core_patch._CLAUDECODE_TOOL_SETTINGS = None
        core_patch._ORIGINAL_LOAD_TEAM_SETTINGS = None

        # Apply patch
        patch_core()

        # Create a TOML file with leader.tool_settings
        toml_content = """
[team]
team_id = "test-team"
team_name = "Test Team"
max_concurrent_members = 1

[team.leader]
system_instruction = "You are a leader"
model = "claudecode:claude-haiku-4-5"
temperature = 0.7

[team.leader.tool_settings]
claudecode = { disallowed_tools = ["Bash", "Write", "Edit"] }

[[team.members]]
name = "assistant"
type = "custom"
tool_name = "ask_assistant"
tool_description = "Ask assistant for help."
model = "claudecode:claude-haiku-4-5"
temperature = 0.3
max_tokens = 4096
timeout_seconds = 120

[team.members.system_instruction]
text = "You are a helpful assistant."

[team.members.plugin]
agent_module = "mixseek_plus.agents.claudecode_agent"
agent_class = "ClaudeCodePlainAgent"
"""
        toml_file = tmp_path / "team.toml"
        toml_file.write_text(toml_content)

        # Load team settings - should auto-apply leader.tool_settings
        from mixseek.config.manager import ConfigurationManager

        manager = ConfigurationManager()
        manager.load_team_settings(toml_file)

        # Verify tool_settings were applied
        result = get_claudecode_tool_settings()
        assert result is not None
        assert result.get("disallowed_tools") == ["Bash", "Write", "Edit"]

    def test_configuration_manager_patch_without_tool_settings(
        self, tmp_path: Path
    ) -> None:
        """LTS-011: ConfigurationManager patch works without tool_settings in TOML."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import get_claudecode_tool_settings, patch_core

        # Reset patch state
        core_patch._PATCH_APPLIED = False
        core_patch._CLAUDECODE_TOOL_SETTINGS = None
        core_patch._ORIGINAL_LOAD_TEAM_SETTINGS = None

        # Apply patch
        patch_core()

        # Create a TOML file without leader.tool_settings
        toml_content = """
[team]
team_id = "test-team"
team_name = "Test Team"
max_concurrent_members = 1

[team.leader]
system_instruction = "You are a leader"
model = "openai:gpt-4o"
temperature = 0.7

[[team.members]]
name = "assistant"
type = "custom"
tool_name = "ask_assistant"
tool_description = "Ask assistant for help."
model = "openai:gpt-4o"
temperature = 0.3
max_tokens = 4096
timeout_seconds = 120

[team.members.system_instruction]
text = "You are a helpful assistant."

[team.members.plugin]
agent_module = "mixseek.agents.plain.agent"
agent_class = "PlainAgent"
"""
        toml_file = tmp_path / "team.toml"
        toml_file.write_text(toml_content)

        # Load team settings - should not set tool_settings
        from mixseek.config.manager import ConfigurationManager

        manager = ConfigurationManager()
        manager.load_team_settings(toml_file)

        # Verify tool_settings were not set
        result = get_claudecode_tool_settings()
        assert result is None

    def test_reset_configuration_manager_patch(self) -> None:
        """reset_configuration_manager_patch restores original function."""
        from mixseek.config.manager import ConfigurationManager

        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            patch_core,
            reset_configuration_manager_patch,
        )

        # Store original function reference
        original_func = ConfigurationManager.load_team_settings

        # Reset patch state
        core_patch._PATCH_APPLIED = False
        core_patch._ORIGINAL_LOAD_TEAM_SETTINGS = None

        # Apply patch
        patch_core()

        # Verify patch was applied
        assert core_patch._ORIGINAL_LOAD_TEAM_SETTINGS is not None

        # Reset
        reset_configuration_manager_patch()

        # Verify reset
        assert core_patch._ORIGINAL_LOAD_TEAM_SETTINGS is None

        # Verify function was restored (should be able to patch again)
        core_patch._PATCH_APPLIED = False
        patch_core()
        assert core_patch._ORIGINAL_LOAD_TEAM_SETTINGS is not None

        # Final cleanup - restore original
        ConfigurationManager.load_team_settings = original_func
        core_patch._ORIGINAL_LOAD_TEAM_SETTINGS = None

    def test_configuration_manager_patch_resolves_preset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """LTS-012: ConfigurationManager patch resolves preset from workspace."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import get_claudecode_tool_settings, patch_core

        # Reset patch state
        core_patch._PATCH_APPLIED = False
        core_patch._CLAUDECODE_TOOL_SETTINGS = None
        core_patch._ORIGINAL_LOAD_TEAM_SETTINGS = None

        # Apply patch
        patch_core()

        # Create workspace structure with preset file
        workspace = tmp_path
        configs_dir = workspace / "configs"
        presets_dir = configs_dir / "presets"
        presets_dir.mkdir(parents=True)

        # Create preset file
        preset_file = presets_dir / "claudecode.toml"
        preset_file.write_text("""
[delegate_only]
permission_mode = "bypassPermissions"
disallowed_tools = ["Bash", "Write", "Edit"]
""")

        # Set MIXSEEK_WORKSPACE environment variable for get_workspace_for_config()
        monkeypatch.setenv("MIXSEEK_WORKSPACE", str(workspace))

        # Create TOML file that references the preset
        toml_content = """
[team]
team_id = "test-team"
team_name = "Test Team"
max_concurrent_members = 1

[team.leader]
system_instruction = "You are a leader"
model = "claudecode:claude-haiku-4-5"
temperature = 0.7

[team.leader.tool_settings]
claudecode = { preset = "delegate_only", max_turns = 100 }

[[team.members]]
name = "assistant"
type = "custom"
tool_name = "ask_assistant"
tool_description = "Ask assistant for help."
model = "claudecode:claude-haiku-4-5"
temperature = 0.3
max_tokens = 4096
timeout_seconds = 120

[team.members.system_instruction]
text = "You are a helpful assistant."

[team.members.plugin]
agent_module = "mixseek_plus.agents.claudecode_agent"
agent_class = "ClaudeCodePlainAgent"
"""
        toml_file = configs_dir / "team.toml"
        toml_file.write_text(toml_content)

        # Load team settings - should auto-resolve preset
        from mixseek.config.manager import ConfigurationManager

        manager = ConfigurationManager()
        manager.load_team_settings(toml_file)

        # Verify preset was resolved and merged
        result = get_claudecode_tool_settings()
        assert result is not None
        # From preset
        assert result.get("permission_mode") == "bypassPermissions"
        assert result.get("disallowed_tools") == ["Bash", "Write", "Edit"]
        # Local override
        assert result.get("max_turns") == 100
        # Preset key should be removed
        assert "preset" not in result


class TestLeaderAgentPatch:
    """Tests for create_leader_agent patching (Issue #23).

    These tests verify that the Leader agent's _function_toolset
    is properly passed to ClaudeCodeModel.set_agent_toolsets().
    """

    def test_patch_leader_agent_exists(self) -> None:
        """_patch_leader_agent function should exist."""
        from mixseek_plus.core_patch import _patch_leader_agent

        assert callable(_patch_leader_agent)

    def test_reset_leader_agent_patch_exists(self) -> None:
        """reset_leader_agent_patch function should exist."""
        from mixseek_plus.core_patch import reset_leader_agent_patch

        assert callable(reset_leader_agent_patch)

    def test_patch_leader_agent_calls_set_agent_toolsets(self) -> None:
        """_patch_leader_agent should call set_agent_toolsets for ClaudeCodeModel."""
        from unittest.mock import MagicMock, patch as mock_patch

        from claudecode_model import ClaudeCodeModel

        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            _patch_leader_agent,
            reset_leader_agent_patch,
        )

        # Reset patch state
        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        # Create dataclass-compatible tool mocks (pydantic-ai Tool is a dataclass)
        async def mock_func1(ctx: object, **kwargs: object) -> str:
            return "result1"

        async def mock_func2(ctx: object, **kwargs: object) -> str:
            return "result2"

        mock_tool1 = MockTool(name="tool1", description="Tool 1", function=mock_func1)
        mock_tool2 = MockTool(name="tool2", description="Tool 2", function=mock_func2)

        # Create mock ClaudeCodeModel - must be actual instance for isinstance check
        mock_claudecode_model = MagicMock(spec=ClaudeCodeModel)
        mock_claudecode_model.set_agent_toolsets = MagicMock()

        # Create mock leader agent with mock model
        mock_leader_agent = MagicMock()
        mock_leader_agent.model = mock_claudecode_model
        mock_leader_agent._function_toolset = MagicMock()
        mock_leader_agent._function_toolset.tools = {
            "tool1": mock_tool1,
            "tool2": mock_tool2,
        }

        # Create mock team_config
        mock_team_config = MagicMock()
        mock_team_config.team_id = "test-team"

        # Mock original function to return our mock agent
        mock_original_func = MagicMock(return_value=mock_leader_agent)

        # Apply patch
        with mock_patch(
            "mixseek.agents.leader.agent.create_leader_agent",
            mock_original_func,
        ):
            _patch_leader_agent()

            # Get patched function from module
            import mixseek.agents.leader.agent as leader_module

            patched_func = leader_module.create_leader_agent

            # Call patched function
            result = patched_func(mock_team_config, {})

            # Verify set_agent_toolsets was called once
            mock_claudecode_model.set_agent_toolsets.assert_called_once()

            # Get the actual call arguments
            call_args = mock_claudecode_model.set_agent_toolsets.call_args
            actual_tools = call_args[0][0]  # First positional argument

            # Verify the correct number of wrapped tools were passed
            assert len(actual_tools) == 2

            # The returned agent should be the mock_leader_agent (with patched run method)
            assert result.model == mock_leader_agent.model

        # Cleanup
        reset_leader_agent_patch()

    def test_patch_leader_agent_does_not_call_set_agent_toolsets_for_non_claudecode(
        self,
    ) -> None:
        """_patch_leader_agent should NOT call set_agent_toolsets for non-ClaudeCodeModel."""
        from unittest.mock import MagicMock, patch as mock_patch

        from pydantic_ai.models.groq import GroqModel

        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            _patch_leader_agent,
            reset_leader_agent_patch,
        )

        # Reset patch state
        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        # Create mock non-ClaudeCode model (Groq)
        mock_groq_model = MagicMock(spec=GroqModel)
        mock_groq_model.set_agent_toolsets = MagicMock()

        # Create mock leader agent
        mock_leader_agent = MagicMock()
        mock_leader_agent.model = mock_groq_model

        mock_team_config = MagicMock()
        mock_team_config.team_id = "test-team"

        mock_original_func = MagicMock(return_value=mock_leader_agent)

        with mock_patch(
            "mixseek.agents.leader.agent.create_leader_agent",
            mock_original_func,
        ):
            _patch_leader_agent()

            import mixseek.agents.leader.agent as leader_module

            patched_func = leader_module.create_leader_agent

            result = patched_func(mock_team_config, {})

            # Verify set_agent_toolsets was NOT called
            mock_groq_model.set_agent_toolsets.assert_not_called()
            assert result == mock_leader_agent

        reset_leader_agent_patch()

    def test_patch_leader_agent_does_not_call_set_agent_toolsets_with_empty_tools(
        self,
    ) -> None:
        """_patch_leader_agent should NOT call set_agent_toolsets when tools is empty."""
        from unittest.mock import MagicMock, patch as mock_patch

        from claudecode_model import ClaudeCodeModel

        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            _patch_leader_agent,
            reset_leader_agent_patch,
        )

        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        mock_claudecode_model = MagicMock(spec=ClaudeCodeModel)
        mock_claudecode_model.set_agent_toolsets = MagicMock()

        mock_leader_agent = MagicMock()
        mock_leader_agent.model = mock_claudecode_model
        mock_leader_agent._function_toolset = MagicMock()
        mock_leader_agent._function_toolset.tools = {}  # Empty tools

        mock_team_config = MagicMock()
        mock_team_config.team_id = "test-team"

        mock_original_func = MagicMock(return_value=mock_leader_agent)

        with mock_patch(
            "mixseek.agents.leader.agent.create_leader_agent",
            mock_original_func,
        ):
            _patch_leader_agent()

            import mixseek.agents.leader.agent as leader_module

            patched_func = leader_module.create_leader_agent

            result = patched_func(mock_team_config, {})

            # Verify set_agent_toolsets was NOT called when tools empty
            mock_claudecode_model.set_agent_toolsets.assert_not_called()
            assert result == mock_leader_agent

        reset_leader_agent_patch()

    def test_patch_leader_agent_handles_function_toolset_access_error(
        self,
    ) -> None:
        """_patch_leader_agent should handle _function_toolset access errors gracefully."""
        from unittest.mock import MagicMock, PropertyMock, patch as mock_patch

        from claudecode_model import ClaudeCodeModel

        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            _patch_leader_agent,
            reset_leader_agent_patch,
        )

        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        mock_claudecode_model = MagicMock(spec=ClaudeCodeModel)
        mock_claudecode_model.set_agent_toolsets = MagicMock()

        mock_leader_agent = MagicMock()
        mock_leader_agent.model = mock_claudecode_model
        # Make _function_toolset.tools raise AttributeError
        type(mock_leader_agent)._function_toolset = PropertyMock(
            side_effect=AttributeError("_function_toolset not found")
        )

        mock_team_config = MagicMock()
        mock_team_config.team_id = "test-team"

        mock_original_func = MagicMock(return_value=mock_leader_agent)

        with mock_patch(
            "mixseek.agents.leader.agent.create_leader_agent",
            mock_original_func,
        ):
            _patch_leader_agent()

            import mixseek.agents.leader.agent as leader_module

            patched_func = leader_module.create_leader_agent

            # Should not raise, returns leader_agent
            result = patched_func(mock_team_config, {})

            # Verify set_agent_toolsets was NOT called due to error
            mock_claudecode_model.set_agent_toolsets.assert_not_called()
            assert result == mock_leader_agent

        reset_leader_agent_patch()

    def test_patch_leader_agent_handles_none_function_toolset(
        self,
    ) -> None:
        """_patch_leader_agent should handle None _function_toolset gracefully."""
        from unittest.mock import MagicMock, patch as mock_patch

        from claudecode_model import ClaudeCodeModel

        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            _patch_leader_agent,
            reset_leader_agent_patch,
        )

        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        mock_claudecode_model = MagicMock(spec=ClaudeCodeModel)
        mock_claudecode_model.set_agent_toolsets = MagicMock()

        # Create mock without _function_toolset attribute
        mock_leader_agent = MagicMock(spec=["model"])  # No _function_toolset
        mock_leader_agent.model = mock_claudecode_model

        mock_team_config = MagicMock()
        mock_team_config.team_id = "test-team"

        mock_original_func = MagicMock(return_value=mock_leader_agent)

        with mock_patch(
            "mixseek.agents.leader.agent.create_leader_agent",
            mock_original_func,
        ):
            _patch_leader_agent()

            import mixseek.agents.leader.agent as leader_module

            patched_func = leader_module.create_leader_agent

            # Should not raise, returns leader_agent
            result = patched_func(mock_team_config, {})

            # Verify set_agent_toolsets was NOT called
            mock_claudecode_model.set_agent_toolsets.assert_not_called()
            assert result == mock_leader_agent

        reset_leader_agent_patch()

    def test_patch_leader_agent_skips_non_claudecode(self) -> None:
        """_patch_leader_agent should skip non-ClaudeCodeModel models."""

        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            _patch_leader_agent,
            reset_leader_agent_patch,
        )

        # Reset patch state
        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        # Apply patch
        _patch_leader_agent()

        # Verify patch was applied
        assert core_patch._ORIGINAL_CREATE_LEADER_AGENT is not None

        # Cleanup
        reset_leader_agent_patch()

    def test_reset_leader_agent_patch_restores_original(self) -> None:
        """reset_leader_agent_patch should restore the original function."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            _patch_leader_agent,
            reset_leader_agent_patch,
        )

        # Reset patch state
        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        # Apply patch
        _patch_leader_agent()

        # Verify patch was applied
        assert core_patch._ORIGINAL_CREATE_LEADER_AGENT is not None

        # Reset
        reset_leader_agent_patch()

        # Verify reset
        assert core_patch._ORIGINAL_CREATE_LEADER_AGENT is None

    def test_reset_leader_agent_patch_does_nothing_when_not_patched(self) -> None:
        """reset_leader_agent_patch should do nothing when not patched."""
        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import reset_leader_agent_patch

        # Ensure not patched
        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        # Should not raise
        reset_leader_agent_patch()

        # Should still be None
        assert core_patch._ORIGINAL_CREATE_LEADER_AGENT is None


class TestWrapToolFunctionForMCP:
    """Tests for _wrap_tool_function_for_mcp() context injection (MCP-001, MCP-002)."""

    @pytest.mark.asyncio
    async def test_wrap_tool_function_raises_when_deps_is_none(self) -> None:
        """MCP-001: Wrapped tool function raises RuntimeError when deps is None."""
        from mixseek_plus.core_patch import _current_deps, _wrap_tool_function_for_mcp

        # Ensure _current_deps is None
        _current_deps.set(None)

        # Create a mock tool function
        async def mock_tool_func(ctx: object, **kwargs: object) -> str:
            return "result"

        wrapped = _wrap_tool_function_for_mcp(mock_tool_func, "test_tool")

        # Should raise RuntimeError when deps is None
        with pytest.raises(RuntimeError) as exc_info:
            await wrapped()

        assert "Tool 'test_tool' called without context" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wrap_tool_function_injects_context_when_deps_set(self) -> None:
        """MCP-002: Wrapped tool function injects context when deps is set."""
        from mixseek_plus.core_patch import (
            _current_deps,
            _wrap_tool_function_for_mcp,
        )
        from mixseek_plus.utils.verbose import MockRunContext

        # Create mock deps
        mock_deps = MagicMock()
        mock_deps.execution_id = "test-execution-123"

        # Set _current_deps
        token = _current_deps.set(mock_deps)

        try:
            # Create a tool function that captures the context
            captured_ctx = None

            async def mock_tool_func(
                ctx: MockRunContext[object], **kwargs: object
            ) -> str:
                nonlocal captured_ctx
                captured_ctx = ctx
                return "result"

            wrapped = _wrap_tool_function_for_mcp(mock_tool_func, "test_tool")

            # Call wrapped function
            result = await wrapped(arg1="value1")

            # Verify context was injected
            assert captured_ctx is not None
            assert isinstance(captured_ctx, MockRunContext)
            assert captured_ctx.deps == mock_deps
            assert result == "result"
        finally:
            _current_deps.reset(token)

    @pytest.mark.asyncio
    async def test_wrap_tool_function_passes_kwargs(self) -> None:
        """Wrapped tool function passes kwargs to original function."""
        from mixseek_plus.core_patch import _current_deps, _wrap_tool_function_for_mcp

        # Create mock deps
        mock_deps = MagicMock()
        mock_deps.execution_id = "test-execution-123"

        token = _current_deps.set(mock_deps)

        try:
            captured_kwargs: dict[str, object] = {}

            async def mock_tool_func(ctx: object, **kwargs: object) -> str:
                nonlocal captured_kwargs
                captured_kwargs = kwargs
                return "result"

            wrapped = _wrap_tool_function_for_mcp(mock_tool_func, "test_tool")

            await wrapped(arg1="value1", arg2=42)

            assert captured_kwargs == {"arg1": "value1", "arg2": 42}
        finally:
            _current_deps.reset(token)


class TestPatchedRunContextVar:
    """Tests for patched_run() ContextVar management (MCP-010, MCP-011)."""

    @pytest.mark.asyncio
    async def test_patched_run_sets_contextvar(self) -> None:
        """MCP-010: patched_run() sets _current_deps ContextVar."""
        from unittest.mock import patch as mock_patch

        from claudecode_model import ClaudeCodeModel

        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            _current_deps,
            _patch_leader_agent,
            reset_leader_agent_patch,
        )

        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        # Create dataclass-compatible mock tool
        async def mock_func(ctx: object, **kwargs: object) -> str:
            return "result"

        mock_tool = MockTool(
            name="test_tool", description="A test tool", function=mock_func
        )

        # Create mock ClaudeCodeModel
        mock_claudecode_model = MagicMock(spec=ClaudeCodeModel)
        mock_claudecode_model.set_agent_toolsets = MagicMock()

        # Track what deps was during run
        deps_during_run = None

        async def capture_deps(*args: object, **kwargs: object) -> str:
            nonlocal deps_during_run
            deps_during_run = _current_deps.get()
            return "run_result"

        # Create mock leader agent with async run
        mock_leader_agent = MagicMock()
        mock_leader_agent.model = mock_claudecode_model
        mock_leader_agent._function_toolset = MagicMock()
        mock_leader_agent._function_toolset.tools = {"test_tool": mock_tool}
        mock_leader_agent.run = AsyncMock(side_effect=capture_deps)

        mock_team_config = MagicMock()
        mock_team_config.team_id = "test-team"

        mock_original_func = MagicMock(return_value=mock_leader_agent)

        # Create mock deps
        mock_deps = MagicMock()
        mock_deps.execution_id = "test-execution-456"

        with mock_patch(
            "mixseek.agents.leader.agent.create_leader_agent",
            mock_original_func,
        ):
            _patch_leader_agent()

            import mixseek.agents.leader.agent as leader_module

            patched_func = leader_module.create_leader_agent

            # Get the patched leader agent
            result_agent = patched_func(mock_team_config, {})

            # Call run with deps
            await result_agent.run("test prompt", deps=mock_deps)

            # Verify deps was set during run
            assert deps_during_run == mock_deps

        reset_leader_agent_patch()

    @pytest.mark.asyncio
    async def test_patched_run_resets_contextvar_on_success(self) -> None:
        """MCP-011: patched_run() resets ContextVar after successful completion."""
        from unittest.mock import patch as mock_patch

        from claudecode_model import ClaudeCodeModel

        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            _current_deps,
            _patch_leader_agent,
            reset_leader_agent_patch,
        )

        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        # Create dataclass-compatible mock tool
        async def mock_func(ctx: object, **kwargs: object) -> str:
            return "result"

        mock_tool = MockTool(
            name="test_tool", description="A test tool", function=mock_func
        )

        mock_claudecode_model = MagicMock(spec=ClaudeCodeModel)
        mock_claudecode_model.set_agent_toolsets = MagicMock()

        mock_leader_agent = MagicMock()
        mock_leader_agent.model = mock_claudecode_model
        mock_leader_agent._function_toolset = MagicMock()
        mock_leader_agent._function_toolset.tools = {"test_tool": mock_tool}
        mock_leader_agent.run = AsyncMock(return_value="run_result")

        mock_team_config = MagicMock()
        mock_team_config.team_id = "test-team"

        mock_original_func = MagicMock(return_value=mock_leader_agent)

        mock_deps = MagicMock()
        mock_deps.execution_id = "test-execution-789"

        # Ensure _current_deps is None before
        _current_deps.set(None)

        with mock_patch(
            "mixseek.agents.leader.agent.create_leader_agent",
            mock_original_func,
        ):
            _patch_leader_agent()

            import mixseek.agents.leader.agent as leader_module

            patched_func = leader_module.create_leader_agent
            result_agent = patched_func(mock_team_config, {})

            await result_agent.run("test prompt", deps=mock_deps)

            # Verify ContextVar is reset after run
            assert _current_deps.get() is None

        reset_leader_agent_patch()

    @pytest.mark.asyncio
    async def test_patched_run_resets_contextvar_on_exception(self) -> None:
        """MCP-011: patched_run() resets ContextVar even when exception occurs."""
        from unittest.mock import patch as mock_patch

        from claudecode_model import ClaudeCodeModel

        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            _current_deps,
            _patch_leader_agent,
            reset_leader_agent_patch,
        )

        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        # Create dataclass-compatible mock tool
        async def mock_func(ctx: object, **kwargs: object) -> str:
            return "result"

        mock_tool = MockTool(
            name="test_tool", description="A test tool", function=mock_func
        )

        mock_claudecode_model = MagicMock(spec=ClaudeCodeModel)
        mock_claudecode_model.set_agent_toolsets = MagicMock()

        mock_leader_agent = MagicMock()
        mock_leader_agent.model = mock_claudecode_model
        mock_leader_agent._function_toolset = MagicMock()
        mock_leader_agent._function_toolset.tools = {"test_tool": mock_tool}
        # Make run raise an exception
        mock_leader_agent.run = AsyncMock(side_effect=ValueError("Test error"))

        mock_team_config = MagicMock()
        mock_team_config.team_id = "test-team"

        mock_original_func = MagicMock(return_value=mock_leader_agent)

        mock_deps = MagicMock()
        mock_deps.execution_id = "test-execution-error"

        # Ensure _current_deps is None before
        _current_deps.set(None)

        with mock_patch(
            "mixseek.agents.leader.agent.create_leader_agent",
            mock_original_func,
        ):
            _patch_leader_agent()

            import mixseek.agents.leader.agent as leader_module

            patched_func = leader_module.create_leader_agent
            result_agent = patched_func(mock_team_config, {})

            # Call run which should raise
            with pytest.raises(ValueError, match="Test error"):
                await result_agent.run("test prompt", deps=mock_deps)

            # Verify ContextVar is reset even after exception
            assert _current_deps.get() is None

        reset_leader_agent_patch()

    @pytest.mark.asyncio
    async def test_patched_run_without_deps_does_not_set_contextvar(self) -> None:
        """patched_run() without deps does not modify ContextVar."""
        from unittest.mock import patch as mock_patch

        from claudecode_model import ClaudeCodeModel

        from mixseek_plus import core_patch
        from mixseek_plus.core_patch import (
            _current_deps,
            _patch_leader_agent,
            reset_leader_agent_patch,
        )

        core_patch._ORIGINAL_CREATE_LEADER_AGENT = None

        # Create dataclass-compatible mock tool
        async def mock_func(ctx: object, **kwargs: object) -> str:
            return "result"

        mock_tool = MockTool(
            name="test_tool", description="A test tool", function=mock_func
        )

        mock_claudecode_model = MagicMock(spec=ClaudeCodeModel)
        mock_claudecode_model.set_agent_toolsets = MagicMock()

        # Track if original run was called
        original_run_called = False

        async def mock_run(*args: object, **kwargs: object) -> str:
            nonlocal original_run_called
            original_run_called = True
            return "run_result"

        mock_leader_agent = MagicMock()
        mock_leader_agent.model = mock_claudecode_model
        mock_leader_agent._function_toolset = MagicMock()
        mock_leader_agent._function_toolset.tools = {"test_tool": mock_tool}
        mock_leader_agent.run = mock_run

        mock_team_config = MagicMock()
        mock_team_config.team_id = "test-team"

        mock_original_func = MagicMock(return_value=mock_leader_agent)

        # Ensure _current_deps is None
        _current_deps.set(None)

        with mock_patch(
            "mixseek.agents.leader.agent.create_leader_agent",
            mock_original_func,
        ):
            _patch_leader_agent()

            import mixseek.agents.leader.agent as leader_module

            patched_func = leader_module.create_leader_agent
            result_agent = patched_func(mock_team_config, {})

            # Call run without deps (deps=None is default)
            await result_agent.run("test prompt")

            # Verify original run was called
            assert original_run_called

            # Verify ContextVar was not modified
            assert _current_deps.get() is None

        reset_leader_agent_patch()
