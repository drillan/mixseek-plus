"""CLI integration tests with Groq configuration.

Tests cover:
- GR-072: Groq models work via CLI without additional setup
- GR-073: CLI maintains full compatibility with mixseek-core
"""

import os
from pathlib import Path
from textwrap import dedent

import pytest
from typer.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a CLI test runner."""
    return CliRunner()


@pytest.fixture
def groq_toml_config(tmp_path: Path) -> Path:
    """Create a minimal TOML config with Groq model for testing."""
    config_content = dedent("""
        [settings]
        workspace = "."

        [leader]
        model = "groq:llama-3.1-8b-instant"

        [[members]]
        name = "groq-assistant"
        type = "groq_plain"
        model = "groq:llama-3.1-8b-instant"
        system_instruction = "You are a helpful assistant. Reply concisely."
    """).strip()

    config_file = tmp_path / "groq-config.toml"
    config_file.write_text(config_content)
    return config_file


@pytest.mark.integration
class TestCLIGroqExecution:
    """Integration tests for CLI execution with Groq."""

    @pytest.fixture(autouse=True)
    def check_groq_api_key(self) -> None:
        """GROQ_API_KEYが設定されていない場合はテストをスキップする."""
        if not os.getenv("GROQ_API_KEY"):
            pytest.skip("GROQ_API_KEY not set")

    def test_cli_help_works(self, cli_runner: CliRunner) -> None:
        """GR-073: CLI help should work after import."""
        from mixseek_plus.cli import app

        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "exec" in result.output

    def test_cli_version_works(self, cli_runner: CliRunner) -> None:
        """GR-073: CLI version should work after import."""
        from mixseek_plus.cli import app

        result = cli_runner.invoke(app, ["--version"])
        assert result.exit_code == 0

    def test_cli_groq_model_is_available(self) -> None:
        """GR-072: After CLI import, groq: models should be available."""
        # Import CLI to trigger patching
        from mixseek_plus import cli  # noqa: F401
        from mixseek.core.auth import create_authenticated_model
        from pydantic_ai.models.groq import GroqModel

        model = create_authenticated_model("groq:llama-3.1-8b-instant")
        assert isinstance(model, GroqModel)
