"""モデルファクトリーの単体テスト.

GR-003 (mixseek-core委譲), GR-030, GR-031 の検証
"""

from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai.models.groq import GroqModel

from mixseek_plus import create_model
from mixseek_plus.errors import ModelCreationError


class TestCreateModelGroqProvider:
    """Groqプロバイダーでのcreate_model関数のテスト."""

    def test_create_model_with_groq_prefix(self, mock_groq_api_key: str) -> None:
        """groq: プレフィックスでGroqModelが作成されることを確認."""
        model = create_model("groq:llama-3.3-70b-versatile")

        assert isinstance(model, GroqModel)


class TestCreateModelCoreProviderDelegation:
    """mixseek-coreプロバイダー委譲のテスト (GR-003)."""

    def test_create_model_with_openai_prefix_delegates_to_core(
        self, mock_openai_api_key: str
    ) -> None:
        """openai: プレフィックスでmixseek-coreに委譲されることを確認."""
        # Mock mixseek-core's create_authenticated_model
        mock_model = MagicMock()
        with patch(
            "mixseek_plus.model_factory.create_authenticated_model",
            return_value=mock_model,
        ) as mock_create:
            model = create_model("openai:gpt-4o")

            mock_create.assert_called_once_with("openai:gpt-4o")
            assert model is mock_model

    def test_create_model_with_anthropic_prefix_delegates_to_core(self) -> None:
        """anthropic: プレフィックスでmixseek-coreに委譲されることを確認."""
        mock_model = MagicMock()
        with patch(
            "mixseek_plus.model_factory.create_authenticated_model",
            return_value=mock_model,
        ) as mock_create:
            model = create_model("anthropic:claude-sonnet-4-5-20250929")

            mock_create.assert_called_once_with("anthropic:claude-sonnet-4-5-20250929")
            assert model is mock_model

    def test_create_model_with_google_gla_prefix_delegates_to_core(self) -> None:
        """google-gla: プレフィックスでmixseek-coreに委譲されることを確認."""
        mock_model = MagicMock()
        with patch(
            "mixseek_plus.model_factory.create_authenticated_model",
            return_value=mock_model,
        ) as mock_create:
            model = create_model("google-gla:gemini-2.5-flash")

            mock_create.assert_called_once_with("google-gla:gemini-2.5-flash")
            assert model is mock_model

    def test_create_model_with_google_vertex_prefix_delegates_to_core(self) -> None:
        """google-vertex: プレフィックスでmixseek-coreに委譲されることを確認."""
        mock_model = MagicMock()
        with patch(
            "mixseek_plus.model_factory.create_authenticated_model",
            return_value=mock_model,
        ) as mock_create:
            model = create_model("google-vertex:gemini-2.5-flash")

            mock_create.assert_called_once_with("google-vertex:gemini-2.5-flash")
            assert model is mock_model

    def test_create_model_with_grok_prefix_delegates_to_core(self) -> None:
        """grok: プレフィックスでmixseek-coreに委譲されることを確認."""
        mock_model = MagicMock()
        with patch(
            "mixseek_plus.model_factory.create_authenticated_model",
            return_value=mock_model,
        ) as mock_create:
            model = create_model("grok:grok-3")

            mock_create.assert_called_once_with("grok:grok-3")
            assert model is mock_model

    def test_create_model_with_grok_responses_prefix_delegates_to_core(self) -> None:
        """grok-responses: プレフィックスでmixseek-coreに委譲されることを確認."""
        mock_model = MagicMock()
        with patch(
            "mixseek_plus.model_factory.create_authenticated_model",
            return_value=mock_model,
        ) as mock_create:
            model = create_model("grok-responses:grok-3")

            mock_create.assert_called_once_with("grok-responses:grok-3")
            assert model is mock_model


class TestCreateModelValidation:
    """モデルID形式検証のテスト (GR-030, GR-031)."""

    def test_create_model_without_colon_raises_error(self) -> None:
        """コロンなしのモデルIDでModelCreationErrorが発生することを確認 (GR-030)."""
        with pytest.raises(ModelCreationError) as exc_info:
            create_model("invalid-model-id")

        assert "モデルIDは 'provider:model-name' 形式で指定してください" in str(
            exc_info.value
        )

    def test_create_model_with_unknown_provider_raises_error(self) -> None:
        """未知のプロバイダーでModelCreationErrorが発生することを確認 (GR-031)."""
        with pytest.raises(ModelCreationError) as exc_info:
            create_model("unknown:some-model")

        assert "サポートされていないプロバイダー" in str(exc_info.value)
        assert "unknown" in str(exc_info.value)
