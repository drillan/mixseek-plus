"""CLI integration tests with ClaudeCode configuration.

Tests cover:
- CC-052: ClaudeCode models work via CLI without additional setup
- CC-073: CLI maintains full compatibility with mixseek-core
"""

import shutil
from pathlib import Path
from textwrap import dedent

import pytest
from claudecode_model import ClaudeCodeModel
from typer.testing import CliRunner


def is_claude_code_available() -> bool:
    """Claude Code CLIが利用可能かチェック."""
    return shutil.which("claude") is not None


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a CLI test runner."""
    return CliRunner()


@pytest.fixture
def claudecode_toml_config(tmp_path: Path) -> Path:
    """Create a minimal TOML config with ClaudeCode model for testing."""
    config_content = dedent("""
        [settings]
        workspace = "."

        [leader]
        model = "claudecode:claude-haiku-4-5"

        [[members]]
        name = "claudecode-assistant"
        type = "claudecode_plain"
        model = "claudecode:claude-haiku-4-5"
        system_instruction = "You are a helpful assistant. Reply concisely."
    """).strip()

    config_file = tmp_path / "claudecode-config.toml"
    config_file.write_text(config_content)
    return config_file


@pytest.mark.integration
class TestCLIClaudeCodeExecution:
    """Integration tests for CLI execution with ClaudeCode."""

    @pytest.fixture(autouse=True)
    def check_claude_code_cli(self) -> None:
        """Claude Code CLIがインストールされていない場合はテストをスキップする."""
        if not is_claude_code_available():
            pytest.skip("Claude Code CLI not installed")

    def test_cli_help_works(self, cli_runner: CliRunner) -> None:
        """CC-073: CLI help should work after import."""
        from mixseek_plus.cli import app

        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "exec" in result.output

    def test_cli_version_works(self, cli_runner: CliRunner) -> None:
        """CC-073: CLI version should work after import."""
        from mixseek_plus.cli import app

        result = cli_runner.invoke(app, ["--version"])
        assert result.exit_code == 0

    def test_cli_claudecode_model_is_available(self) -> None:
        """CC-052: After CLI import, claudecode: models should be available."""
        # Import CLI to trigger patching
        from mixseek_plus import cli  # noqa: F401
        from mixseek.core.auth import create_authenticated_model

        model = create_authenticated_model("claudecode:claude-haiku-4-5")
        assert isinstance(model, ClaudeCodeModel)

    def test_cli_claudecode_agent_is_registered(self) -> None:
        """CC-052: After CLI import, claudecode_plain agent type should be available."""
        # Import CLI to trigger agent registration
        from mixseek_plus import cli  # noqa: F401
        from mixseek.agents.member.factory import MemberAgentFactory

        supported_types = MemberAgentFactory.get_supported_types()
        assert "claudecode_plain" in supported_types
