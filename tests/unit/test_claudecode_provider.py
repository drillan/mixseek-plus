"""ClaudeCodeプロバイダーの単体テスト.

CC-001, CC-011, CC-020, CC-060の検証
"""

from unittest.mock import patch

from claudecode_model import ClaudeCodeModel

from mixseek_plus.providers.claudecode import create_claudecode_model


class TestCreateClaudeCodeModel:
    """create_claudecode_model関数のテスト."""

    def test_create_claudecode_model_returns_claudecode_model_instance(
        self,
    ) -> None:
        """create_claudecode_modelがClaudeCodeModelインスタンスを返すことを確認 (CC-011)."""
        model = create_claudecode_model("claude-sonnet-4-5")

        assert isinstance(model, ClaudeCodeModel)

    def test_create_claudecode_model_with_standard_model_name(self) -> None:
        """標準的なモデル名でClaudeCodeModelが作成できることを確認 (CC-020)."""
        model = create_claudecode_model("claude-haiku-4-5")

        assert isinstance(model, ClaudeCodeModel)

    def test_create_claudecode_model_with_full_version(self) -> None:
        """フルバージョン指定のモデル名でClaudeCodeModelが作成できることを確認."""
        model = create_claudecode_model("claude-sonnet-4-5-20250929")

        assert isinstance(model, ClaudeCodeModel)

    def test_create_claudecode_model_with_opus(self) -> None:
        """Opusモデルが作成できることを確認."""
        model = create_claudecode_model("claude-opus-4-5")

        assert isinstance(model, ClaudeCodeModel)

    def test_create_claudecode_model_with_unknown_model_name(self) -> None:
        """未知のモデル名でもClaudeCodeModelが作成できることを確認.

        Note: モデル名の検証はClaude Code CLI側で行われる
        """
        model = create_claudecode_model("unknown-model-name")

        assert isinstance(model, ClaudeCodeModel)

    def test_create_claudecode_model_passes_model_name(self) -> None:
        """モデル名がClaudeCodeModelに正しく渡されることを確認."""
        with patch(
            "mixseek_plus.providers.claudecode.ClaudeCodeModel"
        ) as mock_model_class:
            create_claudecode_model("claude-sonnet-4-5")

            mock_model_class.assert_called_once_with(model_name="claude-sonnet-4-5")
