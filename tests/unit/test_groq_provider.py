"""Groqプロバイダーの単体テスト.

GR-001, GR-002, GR-010, GR-020, GR-021, GR-022の検証
"""

import pytest
from pydantic_ai.models.groq import GroqModel

from mixseek_plus.errors import ModelCreationError
from mixseek_plus.providers.groq import create_groq_model, validate_groq_credentials


class TestValidateGroqCredentials:
    """validate_groq_credentials関数のテスト."""

    def test_valid_api_key(self, mock_groq_api_key: str) -> None:
        """有効なAPIキーでエラーが発生しないことを確認 (GR-010)."""
        # Should not raise any exception
        validate_groq_credentials()

    def test_missing_api_key_raises_error(self, clear_groq_api_key: None) -> None:
        """APIキー未設定時にModelCreationErrorが発生することを確認 (GR-011)."""
        with pytest.raises(ModelCreationError) as exc_info:
            validate_groq_credentials()

        assert "GROQ_API_KEY環境変数が設定されていません" in str(exc_info.value)
        assert exc_info.value.provider == "groq"

    def test_empty_api_key_raises_error(self, empty_groq_api_key: None) -> None:
        """空のAPIキーでModelCreationErrorが発生することを確認 (GR-011)."""
        with pytest.raises(ModelCreationError) as exc_info:
            validate_groq_credentials()

        assert "GROQ_API_KEY環境変数が設定されていません" in str(exc_info.value)
        assert exc_info.value.provider == "groq"

    def test_invalid_format_api_key_raises_error(
        self, invalid_format_groq_api_key: str
    ) -> None:
        """不正な形式のAPIキーでModelCreationErrorが発生することを確認 (GR-012)."""
        with pytest.raises(ModelCreationError) as exc_info:
            validate_groq_credentials()

        assert "GROQ_API_KEYの形式が不正です" in str(exc_info.value)
        assert "gsk_で始まる必要があります" in str(exc_info.value)
        assert exc_info.value.provider == "groq"


class TestCreateGroqModel:
    """create_groq_model関数のテスト."""

    def test_create_groq_model_returns_groq_model_instance(
        self, mock_groq_api_key: str
    ) -> None:
        """create_groq_modelがGroqModelインスタンスを返すことを確認 (GR-001, GR-002)."""
        model = create_groq_model("llama-3.3-70b-versatile")

        assert isinstance(model, GroqModel)

    def test_create_groq_model_with_standard_model_name(
        self, mock_groq_api_key: str
    ) -> None:
        """標準的なモデル名でGroqModelが作成できることを確認 (GR-020)."""
        model = create_groq_model("llama-3.1-8b-instant")

        assert isinstance(model, GroqModel)

    def test_create_groq_model_with_slash_in_model_name(
        self, mock_groq_api_key: str
    ) -> None:
        """スラッシュを含むモデル名でGroqModelが作成できることを確認 (GR-021)."""
        model = create_groq_model("meta-llama/llama-4-scout-17b-16e-instruct")

        assert isinstance(model, GroqModel)

    def test_create_groq_model_with_unknown_model_name(
        self, mock_groq_api_key: str
    ) -> None:
        """未知のモデル名でもGroqModelが作成できることを確認 (GR-022).

        Note: モデル名の検証はGroq API側で行われる
        """
        model = create_groq_model("unknown-model-name")

        assert isinstance(model, GroqModel)

    def test_create_groq_model_without_api_key_raises_error(
        self, clear_groq_api_key: None
    ) -> None:
        """APIキー未設定時にModelCreationErrorが発生することを確認."""
        with pytest.raises(ModelCreationError):
            create_groq_model("llama-3.3-70b-versatile")
