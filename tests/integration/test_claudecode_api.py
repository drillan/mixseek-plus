"""ClaudeCode API統合テスト.

実際のClaude Code CLIを使用してモデル作成と基本的なAPI呼び出しをテストする.
Claude Code CLIがインストールされている場合のみ実行される.
"""

import shutil

import pytest
from claudecode_model import ClaudeCodeModel
from pydantic_ai import Agent

from mixseek_plus import create_model


def is_claude_code_available() -> bool:
    """Claude Code CLIが利用可能かチェック."""
    return shutil.which("claude") is not None


@pytest.mark.integration
class TestClaudeCodeApiIntegration:
    """ClaudeCode API統合テスト."""

    @pytest.fixture(autouse=True)
    def check_claude_code_cli(self) -> None:
        """Claude Code CLIがインストールされていない場合はテストをスキップする."""
        if not is_claude_code_available():
            pytest.skip("Claude Code CLI not installed")

    def test_create_model_returns_claudecode_model(self) -> None:
        """create_modelがClaudeCodeModelインスタンスを返すことを確認."""
        model = create_model("claudecode:claude-sonnet-4-5")

        assert isinstance(model, ClaudeCodeModel)

    def test_create_model_with_different_models(self) -> None:
        """異なるモデル名でClaudeCodeModelを作成できることを確認."""
        models = [
            "claudecode:claude-sonnet-4-5",
            "claudecode:claude-haiku-4-5",
            "claudecode:claude-opus-4-5",
        ]

        for model_id in models:
            model = create_model(model_id)
            assert isinstance(model, ClaudeCodeModel)

    @pytest.mark.asyncio
    async def test_claudecode_model_can_generate_response(self) -> None:
        """ClaudeCodeモデルがCLIを通じてレスポンスを生成できることを確認.

        Note: This test actually invokes the Claude Code CLI and may take time.
        """
        model = create_model("claudecode:claude-haiku-4-5")
        agent = Agent(model)

        result = await agent.run("Reply with just 'hello' in lowercase.")

        assert result.output is not None
        assert "hello" in result.output.lower()
