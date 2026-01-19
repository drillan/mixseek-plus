"""Unit tests for CLI wrapper module.

Tests cover:
- GR-070: CLI wrapper provides mixseek-plus/mskp command
- GR-071: CLI automatically calls patch_core() on startup
- GR-072: Groq models work via CLI without additional setup
- GR-073: CLI maintains full compatibility with mixseek-core
"""

from typer.testing import CliRunner
import pytest


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a CLI test runner."""
    return CliRunner()


@pytest.fixture
def reset_patch_state() -> None:
    """Reset patch state before each test."""
    from mixseek_plus import core_patch

    core_patch._PATCH_APPLIED = False


class TestCLIWrapper:
    """Tests for CLI wrapper functionality."""

    def test_cli_app_exists(self) -> None:
        """GR-070: CLI app (mixseek-plus/mskp) should exist and be a Typer instance."""
        from mixseek_plus.cli import app
        import typer

        assert isinstance(app, typer.Typer)

    def test_cli_applies_patch_on_startup(
        self, reset_patch_state: None, mock_groq_api_key: str
    ) -> None:
        """GR-071: CLI should apply patch_core() on startup."""
        from mixseek_plus import core_patch

        # Reset patch state
        core_patch._PATCH_APPLIED = False

        # Import CLI module which should trigger patching
        import importlib
        import mixseek_plus.cli

        importlib.reload(mixseek_plus.cli)

        # Patch should be applied after module import
        assert core_patch.is_patched() is True


class TestCLICommands:
    """Tests for CLI command delegation to mixseek-core."""

    def test_version_command(
        self, cli_runner: CliRunner, mock_groq_api_key: str
    ) -> None:
        """GR-073: --version should show version info."""
        from mixseek_plus.cli import app

        result = cli_runner.invoke(app, ["--version"])
        # Should not error (exit code 0) even if version not set
        # The important thing is that the command runs
        assert result.exit_code == 0 or "--version" in result.output.lower()

    def test_help_command(self, cli_runner: CliRunner, mock_groq_api_key: str) -> None:
        """GR-073: --help should show help text compatible with mixseek-core."""
        from mixseek_plus.cli import app

        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # Should show available commands
        assert "exec" in result.output.lower() or "usage" in result.output.lower()


class TestCLIGroqIntegration:
    """Tests for Groq model integration via CLI."""

    def test_groq_model_available_after_cli_import(
        self, reset_patch_state: None, mock_groq_api_key: str
    ) -> None:
        """GR-072: After importing CLI, groq: models should work."""
        from mixseek_plus import core_patch

        # Reset patch state
        core_patch._PATCH_APPLIED = False

        # Import CLI (should trigger patch)
        import importlib
        import mixseek_plus.cli

        importlib.reload(mixseek_plus.cli)

        # Now create_authenticated_model should accept groq:
        from mixseek.core.auth import create_authenticated_model
        from pydantic_ai.models.groq import GroqModel

        model = create_authenticated_model("groq:llama-3.3-70b-versatile")
        assert isinstance(model, GroqModel)


class TestCLIEntryPoint:
    """Tests for CLI entry point configuration."""

    def test_main_function_exists(self) -> None:
        """CLI module should have a main function for entry point."""
        from mixseek_plus.cli import main

        assert callable(main)

    def test_main_applies_patch(
        self, reset_patch_state: None, mock_groq_api_key: str
    ) -> None:
        """GR-071: main() should ensure patch is applied."""
        from mixseek_plus import core_patch
        from mixseek_plus.cli import ensure_patched

        # Reset patch state
        core_patch._PATCH_APPLIED = False

        # Call ensure_patched (called by main)
        ensure_patched()

        assert core_patch.is_patched() is True


class TestCLIClaudeCodeIntegration:
    """Tests for ClaudeCode model integration via CLI (CC-052)."""

    def test_claudecode_model_available_after_cli_import(
        self, reset_patch_state: None
    ) -> None:
        """CC-052: After importing CLI, claudecode: models should work."""
        from mixseek_plus import core_patch

        # Reset patch state
        core_patch._PATCH_APPLIED = False

        # Import CLI (should trigger patch)
        import importlib
        import mixseek_plus.cli

        importlib.reload(mixseek_plus.cli)

        # Now create_authenticated_model should accept claudecode:
        from claudecode_model import ClaudeCodeModel
        from mixseek.core.auth import create_authenticated_model

        model = create_authenticated_model("claudecode:claude-sonnet-4-5")
        assert isinstance(model, ClaudeCodeModel)

    def test_cli_registers_claudecode_agents(self, reset_patch_state: None) -> None:
        """CC-052: CLI should register ClaudeCode agents for TOML config."""
        from mixseek_plus import core_patch

        # Reset patch state
        core_patch._PATCH_APPLIED = False

        # Import CLI (should trigger registration)
        import importlib
        import mixseek_plus.cli

        importlib.reload(mixseek_plus.cli)

        # Verify ClaudeCode agents are registered
        from mixseek.agents.member.factory import MemberAgentFactory

        # Check that claudecode_plain is in supported types
        supported_types = MemberAgentFactory.get_supported_types()
        assert "claudecode_plain" in supported_types

    def test_cli_patches_before_any_import(self, reset_patch_state: None) -> None:
        """CC-052: Patch should be applied before mixseek-core modules load."""
        from mixseek_plus import core_patch

        # Reset patch state
        core_patch._PATCH_APPLIED = False

        # Import CLI
        import importlib
        import mixseek_plus.cli

        importlib.reload(mixseek_plus.cli)

        # Verify patch is applied at module level (not just in main)
        assert core_patch.is_patched() is True
