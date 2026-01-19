"""Preset resolution for ClaudeCode tool settings.

This module provides functionality to load named presets from TOML files
and merge them with local settings. Presets allow teams to define
reusable ClaudeCode tool configurations.

Example preset file (configs/presets/claudecode.toml):
    [delegate_only]
    permission_mode = "bypassPermissions"
    disallowed_tools = ["Bash", "Write", "Edit", "Read", "Glob", "Grep"]

    [full_access]
    permission_mode = "bypassPermissions"

Example usage in team config (Leader):
    [leader.tool_settings.claudecode]
    preset = "delegate_only"

Example usage in team config (Member):
    [members.tool_settings.claudecode]
    preset = "delegate_only"
    max_turns = 50  # Preset with local overrides
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mixseek_plus.providers.claudecode import ClaudeCodeToolSettings

# Type alias for raw TOML preset data (nested dicts, strings, ints, lists)
# Using object instead of Any to satisfy CLAUDE.md type safety requirements
PresetData = dict[str, object]

logger = logging.getLogger(__name__)

# Default preset file path relative to workspace
PRESET_FILE_PATH = "configs/presets/claudecode.toml"


class PresetError(Exception):
    """Base exception for preset-related errors."""


class PresetFileNotFoundError(PresetError):
    """Raised when the preset TOML file is not found.

    This error indicates that the configs/presets/claudecode.toml file
    does not exist in the specified workspace.

    Attributes:
        file_path: The path that was searched for the preset file.
        workspace: The workspace directory where the preset was expected.
    """

    def __init__(self, file_path: Path, workspace: Path) -> None:
        """Initialize PresetFileNotFoundError.

        Args:
            file_path: The full path to the missing preset file.
            workspace: The workspace directory.
        """
        self.file_path = file_path
        self.workspace = workspace
        message = (
            f"Preset file not found: {file_path}\n"
            f"Expected location: {workspace / PRESET_FILE_PATH}\n"
            f"Please create the preset file or remove the 'preset' key from tool_settings."
        )
        super().__init__(message)


class PresetSyntaxError(PresetError):
    """Raised when the preset TOML file contains invalid syntax.

    This error indicates that the configs/presets/claudecode.toml file
    contains invalid TOML syntax that cannot be parsed.

    Attributes:
        file_path: The path to the preset file with invalid syntax.
        original_error: The original tomllib.TOMLDecodeError.
    """

    def __init__(self, file_path: Path, original_error: Exception) -> None:
        """Initialize PresetSyntaxError.

        Args:
            file_path: The path to the preset file with invalid syntax.
            original_error: The original tomllib.TOMLDecodeError.
        """
        self.file_path = file_path
        self.original_error = original_error
        message = (
            f"Invalid TOML syntax in preset file: {file_path}\n"
            f"Error: {original_error}\n"
            f"Please check the TOML syntax in the preset file."
        )
        super().__init__(message)


class PresetNotFoundError(PresetError):
    """Raised when a preset name is not defined in the preset file.

    This error indicates that the specified preset name does not exist
    in the configs/presets/claudecode.toml file.

    Attributes:
        preset_name: The name of the preset that was not found.
        available_presets: List of preset names that are defined in the file.
        file_path: The path to the preset file.
    """

    def __init__(
        self,
        preset_name: str,
        available_presets: list[str],
        file_path: Path,
    ) -> None:
        """Initialize PresetNotFoundError.

        Args:
            preset_name: The name of the preset that was not found.
            available_presets: List of available preset names.
            file_path: The path to the preset file.
        """
        self.preset_name = preset_name
        self.available_presets = available_presets
        self.file_path = file_path

        if available_presets:
            available = ", ".join(sorted(available_presets))
            message = (
                f"Preset '{preset_name}' not found in {file_path}\n"
                f"Available presets: {available}"
            )
        else:
            message = (
                f"Preset '{preset_name}' not found in {file_path}\n"
                f"No presets are defined in the file."
            )
        super().__init__(message)


def _load_preset_file(workspace: Path) -> PresetData:
    """Load and parse the preset TOML file from the workspace.

    Args:
        workspace: The workspace directory containing configs/presets/claudecode.toml.

    Returns:
        Dictionary containing all preset definitions.

    Raises:
        PresetFileNotFoundError: If the preset file does not exist.
        PresetSyntaxError: If the preset file contains invalid TOML syntax.
    """
    import tomllib

    preset_file = workspace / PRESET_FILE_PATH

    if not preset_file.exists():
        raise PresetFileNotFoundError(preset_file, workspace)

    try:
        with preset_file.open("rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise PresetSyntaxError(preset_file, e) from e


def resolve_claudecode_preset(
    preset_name: str,
    workspace: Path,
) -> ClaudeCodeToolSettings:
    """Resolve a preset name to its ClaudeCode tool settings.

    Looks up the preset name in configs/presets/claudecode.toml within
    the specified workspace and returns the corresponding settings.

    Args:
        preset_name: The name of the preset to resolve.
        workspace: The workspace directory containing the preset file.

    Returns:
        ClaudeCodeToolSettings dictionary from the preset definition.

    Raises:
        PresetFileNotFoundError: If the preset file does not exist.
        PresetNotFoundError: If the preset name is not defined in the file.

    Example:
        >>> settings = resolve_claudecode_preset("delegate_only", Path("/workspace"))
        >>> settings
        {'permission_mode': 'bypassPermissions', 'disallowed_tools': [...]}
    """
    preset_data = _load_preset_file(workspace)

    if preset_name not in preset_data:
        available = [k for k in preset_data.keys() if isinstance(preset_data[k], dict)]
        raise PresetNotFoundError(
            preset_name,
            available,
            workspace / PRESET_FILE_PATH,
        )

    preset_settings = preset_data[preset_name]
    if not isinstance(preset_settings, dict):
        raise PresetNotFoundError(
            preset_name,
            [k for k in preset_data.keys() if isinstance(preset_data[k], dict)],
            workspace / PRESET_FILE_PATH,
        )

    logger.debug(
        "Resolved preset '%s' from %s: %s",
        preset_name,
        workspace / PRESET_FILE_PATH,
        preset_settings,
    )

    return preset_settings  # type: ignore[return-value]


def resolve_and_merge_preset(
    settings: ClaudeCodeToolSettings,
    workspace: Path,
) -> ClaudeCodeToolSettings:
    """Resolve preset and merge with local settings.

    If the settings contain a 'preset' key, this function:
    1. Loads the preset configuration from the preset file
    2. Merges it with any additional local settings (local settings take precedence)
    3. Removes the 'preset' key from the final result

    If no 'preset' key is present, the original settings are returned unchanged.

    Args:
        settings: ClaudeCode tool settings that may contain a 'preset' key.
        workspace: The workspace directory containing the preset file.

    Returns:
        Merged ClaudeCodeToolSettings with preset resolved and 'preset' key removed.

    Raises:
        PresetFileNotFoundError: If preset is specified but file doesn't exist.
        PresetNotFoundError: If preset name is not defined in the file.

    Example:
        >>> settings = {"preset": "delegate_only", "max_turns": 50}
        >>> merged = resolve_and_merge_preset(settings, Path("/workspace"))
        >>> merged  # Preset settings merged with max_turns=50, no 'preset' key
        {'permission_mode': 'bypassPermissions', 'disallowed_tools': [...], 'max_turns': 50}
    """
    preset_name = settings.get("preset")

    if preset_name is None:
        # No preset specified, return original settings
        return settings

    # Load preset settings
    preset_settings = resolve_claudecode_preset(preset_name, workspace)

    # Merge: preset as base, local settings override
    merged: PresetData = dict(preset_settings)

    for key, value in settings.items():
        if key != "preset":
            merged[key] = value

    logger.debug(
        "Merged preset '%s' with local settings: %s",
        preset_name,
        merged,
    )

    return merged  # type: ignore[return-value]
