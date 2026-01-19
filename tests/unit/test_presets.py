"""Unit tests for preset resolution functionality.

Tests cover:
- PRE-001: PresetNotFoundError exception
- PRE-002: PresetFileNotFoundError exception
- PRE-003: resolve_claudecode_preset() function
- PRE-004: resolve_and_merge_preset() function
- PRE-005: Preset and local settings merge strategy
"""

from pathlib import Path

import pytest

from mixseek_plus.presets import (
    PRESET_FILE_PATH,
    PresetFileNotFoundError,
    PresetNotFoundError,
    resolve_and_merge_preset,
    resolve_claudecode_preset,
)


class TestPresetErrors:
    """Tests for preset error classes (PRE-001, PRE-002)."""

    def test_preset_not_found_error_message_with_available_presets(self) -> None:
        """PRE-001: PresetNotFoundError includes available presets in message."""
        error = PresetNotFoundError(
            preset_name="unknown",
            available_presets=["delegate_only", "full_access", "read_only"],
            file_path=Path("/workspace/configs/presets/claudecode.toml"),
        )

        assert "unknown" in str(error)
        assert "delegate_only" in str(error)
        assert "full_access" in str(error)
        assert "read_only" in str(error)
        assert error.preset_name == "unknown"
        assert error.available_presets == ["delegate_only", "full_access", "read_only"]

    def test_preset_not_found_error_message_without_available_presets(self) -> None:
        """PRE-001: PresetNotFoundError handles empty available presets."""
        error = PresetNotFoundError(
            preset_name="unknown",
            available_presets=[],
            file_path=Path("/workspace/configs/presets/claudecode.toml"),
        )

        assert "unknown" in str(error)
        assert "No presets are defined" in str(error)

    def test_preset_file_not_found_error_message(self) -> None:
        """PRE-002: PresetFileNotFoundError includes file path and workspace."""
        workspace = Path("/workspace")
        file_path = workspace / PRESET_FILE_PATH

        error = PresetFileNotFoundError(file_path=file_path, workspace=workspace)

        assert str(file_path) in str(error)
        assert str(workspace) in str(error)
        assert error.file_path == file_path
        assert error.workspace == workspace


class TestResolveClaudecodePreset:
    """Tests for resolve_claudecode_preset() function (PRE-003)."""

    def test_resolve_preset_returns_settings(self, tmp_path: Path) -> None:
        """PRE-003: resolve_claudecode_preset returns preset settings."""
        # Create preset file
        preset_dir = tmp_path / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
[delegate_only]
permission_mode = "bypassPermissions"
disallowed_tools = ["Bash", "Write", "Edit", "Read"]
""")

        settings = resolve_claudecode_preset("delegate_only", tmp_path)

        assert settings["permission_mode"] == "bypassPermissions"
        assert settings["disallowed_tools"] == ["Bash", "Write", "Edit", "Read"]

    def test_resolve_preset_raises_when_file_not_found(self, tmp_path: Path) -> None:
        """PRE-003: resolve_claudecode_preset raises PresetFileNotFoundError."""
        with pytest.raises(PresetFileNotFoundError) as exc_info:
            resolve_claudecode_preset("delegate_only", tmp_path)

        assert exc_info.value.workspace == tmp_path

    def test_resolve_preset_raises_when_preset_not_found(self, tmp_path: Path) -> None:
        """PRE-003: resolve_claudecode_preset raises PresetNotFoundError."""
        # Create preset file without the requested preset
        preset_dir = tmp_path / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
[full_access]
permission_mode = "bypassPermissions"
""")

        with pytest.raises(PresetNotFoundError) as exc_info:
            resolve_claudecode_preset("delegate_only", tmp_path)

        assert exc_info.value.preset_name == "delegate_only"
        assert "full_access" in exc_info.value.available_presets

    def test_resolve_preset_with_all_settings(self, tmp_path: Path) -> None:
        """PRE-003: resolve_claudecode_preset handles all ClaudeCode settings."""
        preset_dir = tmp_path / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
[comprehensive]
permission_mode = "bypassPermissions"
allowed_tools = ["Read", "Glob"]
disallowed_tools = ["Write", "Edit"]
working_directory = "/workspace/project"
max_turns = 100
""")

        settings = resolve_claudecode_preset("comprehensive", tmp_path)

        assert settings["permission_mode"] == "bypassPermissions"
        assert settings["allowed_tools"] == ["Read", "Glob"]
        assert settings["disallowed_tools"] == ["Write", "Edit"]
        assert settings["working_directory"] == "/workspace/project"
        assert settings["max_turns"] == 100

    def test_resolve_preset_ignores_non_dict_entries(self, tmp_path: Path) -> None:
        """PRE-003: resolve_claudecode_preset ignores non-dict TOML entries."""
        preset_dir = tmp_path / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
# This is a comment
version = "1.0"  # This is a scalar, not a preset

[valid_preset]
permission_mode = "bypassPermissions"
""")

        settings = resolve_claudecode_preset("valid_preset", tmp_path)
        assert settings["permission_mode"] == "bypassPermissions"

        # Non-dict entry should raise PresetNotFoundError
        with pytest.raises(PresetNotFoundError) as exc_info:
            resolve_claudecode_preset("version", tmp_path)

        # Only valid_preset should be in available presets
        assert "valid_preset" in exc_info.value.available_presets


class TestResolveAndMergePreset:
    """Tests for resolve_and_merge_preset() function (PRE-004, PRE-005)."""

    def test_merge_returns_original_when_no_preset(self, tmp_path: Path) -> None:
        """PRE-004: resolve_and_merge_preset returns original when no preset key."""
        settings = {
            "permission_mode": "bypassPermissions",
            "max_turns": 50,
        }

        result = resolve_and_merge_preset(settings, tmp_path)  # type: ignore[arg-type]

        assert result == settings

    def test_merge_loads_and_merges_preset(self, tmp_path: Path) -> None:
        """PRE-004: resolve_and_merge_preset loads and merges preset settings."""
        # Create preset file
        preset_dir = tmp_path / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
[delegate_only]
permission_mode = "bypassPermissions"
disallowed_tools = ["Bash", "Write", "Edit"]
""")

        settings = {"preset": "delegate_only", "max_turns": 50}

        result = resolve_and_merge_preset(settings, tmp_path)  # type: ignore[arg-type]

        # Should have preset settings merged with local settings
        assert result["permission_mode"] == "bypassPermissions"
        assert result["disallowed_tools"] == ["Bash", "Write", "Edit"]
        assert result["max_turns"] == 50
        # Preset key should be removed
        assert "preset" not in result

    def test_merge_local_settings_override_preset(self, tmp_path: Path) -> None:
        """PRE-005: Local settings take precedence over preset."""
        preset_dir = tmp_path / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
[base_preset]
permission_mode = "bypassPermissions"
max_turns = 10
disallowed_tools = ["Bash"]
""")

        settings = {
            "preset": "base_preset",
            "max_turns": 100,  # Override preset value
            "allowed_tools": ["Read", "Write"],  # Additional setting
        }

        result = resolve_and_merge_preset(settings, tmp_path)  # type: ignore[arg-type]

        # Preset value should be kept
        assert result["permission_mode"] == "bypassPermissions"
        assert result["disallowed_tools"] == ["Bash"]
        # Local override should take precedence
        assert result["max_turns"] == 100
        # Additional local setting should be included
        assert result["allowed_tools"] == ["Read", "Write"]
        # Preset key should be removed
        assert "preset" not in result

    def test_merge_raises_when_preset_file_not_found(self, tmp_path: Path) -> None:
        """PRE-004: resolve_and_merge_preset raises PresetFileNotFoundError."""
        settings = {"preset": "delegate_only"}

        with pytest.raises(PresetFileNotFoundError):
            resolve_and_merge_preset(settings, tmp_path)  # type: ignore[arg-type]

    def test_merge_raises_when_preset_not_found(self, tmp_path: Path) -> None:
        """PRE-004: resolve_and_merge_preset raises PresetNotFoundError."""
        preset_dir = tmp_path / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
[other_preset]
permission_mode = "bypassPermissions"
""")

        settings = {"preset": "nonexistent"}

        with pytest.raises(PresetNotFoundError) as exc_info:
            resolve_and_merge_preset(settings, tmp_path)  # type: ignore[arg-type]

        assert exc_info.value.preset_name == "nonexistent"

    def test_merge_with_empty_local_settings(self, tmp_path: Path) -> None:
        """PRE-004: resolve_and_merge_preset with only preset key."""
        preset_dir = tmp_path / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
[minimal]
permission_mode = "bypassPermissions"
""")

        settings = {"preset": "minimal"}

        result = resolve_and_merge_preset(settings, tmp_path)  # type: ignore[arg-type]

        assert result == {"permission_mode": "bypassPermissions"}
        assert "preset" not in result


class TestMultiplePresets:
    """Tests for multiple presets in one file."""

    def test_multiple_presets_in_file(self, tmp_path: Path) -> None:
        """Multiple presets can be defined and resolved."""
        preset_dir = tmp_path / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
[delegate_only]
permission_mode = "bypassPermissions"
disallowed_tools = ["Bash", "Write", "Edit", "Read", "Glob", "Grep", "WebFetch", "WebSearch", "NotebookEdit", "Task"]

[full_access]
permission_mode = "bypassPermissions"

[read_only]
permission_mode = "bypassPermissions"
disallowed_tools = ["Write", "Edit", "NotebookEdit"]
""")

        # Resolve each preset
        delegate = resolve_claudecode_preset("delegate_only", tmp_path)
        full = resolve_claudecode_preset("full_access", tmp_path)
        readonly = resolve_claudecode_preset("read_only", tmp_path)

        assert len(delegate["disallowed_tools"]) == 10
        assert "disallowed_tools" not in full
        assert readonly["disallowed_tools"] == ["Write", "Edit", "NotebookEdit"]

    def test_preset_not_found_lists_all_available(self, tmp_path: Path) -> None:
        """PresetNotFoundError lists all available presets."""
        preset_dir = tmp_path / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
[preset_a]
permission_mode = "mode_a"

[preset_b]
permission_mode = "mode_b"

[preset_c]
permission_mode = "mode_c"
""")

        with pytest.raises(PresetNotFoundError) as exc_info:
            resolve_claudecode_preset("nonexistent", tmp_path)

        available = exc_info.value.available_presets
        assert "preset_a" in available
        assert "preset_b" in available
        assert "preset_c" in available
