"""ClaudeCodeプロバイダーの単体テスト.

CC-001, CC-011, CC-020, CC-060の検証
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from claudecode_model import ClaudeCodeModel
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.usage import RequestUsage

from mixseek_plus.providers.claudecode import (
    FixedTokenClaudeCodeModel,
    create_claudecode_model,
)


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
        """モデル名がFixedTokenClaudeCodeModelに正しく渡されることを確認."""
        with patch(
            "mixseek_plus.providers.claudecode.FixedTokenClaudeCodeModel"
        ) as mock_model_class:
            create_claudecode_model("claude-sonnet-4-5")

            mock_model_class.assert_called_once_with(model_name="claude-sonnet-4-5")

    def test_create_claudecode_model_returns_fixed_token_model(self) -> None:
        """create_claudecode_modelがFixedTokenClaudeCodeModelを返すことを確認."""
        model = create_claudecode_model("claude-sonnet-4-5")

        assert isinstance(model, FixedTokenClaudeCodeModel)


class TestFixedTokenClaudeCodeModel:
    """FixedTokenClaudeCodeModelのテスト（Issue #15）."""

    def test_inherits_from_claudecode_model(self) -> None:
        """ClaudeCodeModelを継承していることを確認."""
        assert issubclass(FixedTokenClaudeCodeModel, ClaudeCodeModel)

    @pytest.mark.asyncio
    async def test_fix_token_usage_with_cache_tokens(self) -> None:
        """キャッシュトークンがある場合のinput_tokens補正を確認.

        CLIからの入力:
            input_tokens=3 (uncached only)
            cache_creation_input_tokens=8932
            cache_read_input_tokens=16404

        期待される出力:
            input_tokens=25339 (3+8932+16404)
        """
        model = FixedTokenClaudeCodeModel(model_name="claude-sonnet-4-5")

        original_usage = RequestUsage(
            input_tokens=3,
            output_tokens=35,
            cache_write_tokens=8932,
            cache_read_tokens=16404,
        )
        original_response = ModelResponse(
            parts=[TextPart(content="test response")],
            usage=original_usage,
            model_name="claude-sonnet-4-5",
            timestamp=datetime.now(tz=timezone.utc),
        )

        with patch.object(
            ClaudeCodeModel, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = original_response

            result = await model.request([], None, None)  # type: ignore[arg-type]

        assert result.usage.input_tokens == 25339  # 3 + 8932 + 16404
        assert result.usage.output_tokens == 35
        assert result.usage.cache_write_tokens == 8932
        assert result.usage.cache_read_tokens == 16404

    @pytest.mark.asyncio
    async def test_fix_token_usage_without_cache(self) -> None:
        """キャッシュトークンがない場合はinput_tokensが変化しないことを確認."""
        model = FixedTokenClaudeCodeModel(model_name="claude-sonnet-4-5")

        original_usage = RequestUsage(
            input_tokens=100,
            output_tokens=50,
            cache_write_tokens=0,
            cache_read_tokens=0,
        )
        original_response = ModelResponse(
            parts=[TextPart(content="test response")],
            usage=original_usage,
            model_name="claude-sonnet-4-5",
            timestamp=datetime.now(tz=timezone.utc),
        )

        with patch.object(
            ClaudeCodeModel, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = original_response

            result = await model.request([], None, None)  # type: ignore[arg-type]

        assert result.usage.input_tokens == 100
        assert result.usage.output_tokens == 50

    @pytest.mark.asyncio
    async def test_fix_token_usage_preserves_other_fields(self) -> None:
        """usageの他のフィールドが保持されることを確認."""
        model = FixedTokenClaudeCodeModel(model_name="claude-sonnet-4-5")

        original_usage = RequestUsage(
            input_tokens=10,
            output_tokens=20,
            cache_write_tokens=30,
            cache_read_tokens=40,
            input_audio_tokens=5,
            cache_audio_read_tokens=3,
            output_audio_tokens=2,
            details={"some_detail": 1},
        )
        timestamp = datetime.now(tz=timezone.utc)
        original_response = ModelResponse(
            parts=[TextPart(content="test")],
            usage=original_usage,
            model_name="claude-sonnet-4-5",
            timestamp=timestamp,
        )

        with patch.object(
            ClaudeCodeModel, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = original_response

            result = await model.request([], None, None)  # type: ignore[arg-type]

        assert result.usage.input_tokens == 80  # 10 + 30 + 40
        assert result.usage.output_tokens == 20
        assert result.usage.cache_write_tokens == 30
        assert result.usage.cache_read_tokens == 40
        assert result.usage.input_audio_tokens == 5
        assert result.usage.cache_audio_read_tokens == 3
        assert result.usage.output_audio_tokens == 2
        assert result.usage.details == {"some_detail": 1}

    @pytest.mark.asyncio
    async def test_fix_token_usage_preserves_response_fields(self) -> None:
        """ModelResponseの他のフィールドが保持されることを確認."""
        model = FixedTokenClaudeCodeModel(model_name="claude-sonnet-4-5")

        original_usage = RequestUsage(input_tokens=10, output_tokens=20)
        timestamp = datetime.now(tz=timezone.utc)
        parts = [TextPart(content="test response")]
        original_response = ModelResponse(
            parts=parts,
            usage=original_usage,
            model_name="test-model",
            timestamp=timestamp,
        )

        with patch.object(
            ClaudeCodeModel, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = original_response

            result = await model.request([], None, None)  # type: ignore[arg-type]

        assert result.parts == parts
        assert result.model_name == "test-model"
        assert result.timestamp == timestamp

    @pytest.mark.asyncio
    async def test_genai_prices_calculation_non_negative(self) -> None:
        """genai_pricesの計算式で負の値にならないことを確認.

        genai_pricesの計算式:
            uncached_text_input_tokens = input_tokens - cache_write_tokens - cache_read_tokens

        補正後の計算:
            uncached = (uncached + cache_write + cache_read) - cache_write - cache_read
                     = uncached >= 0
        """
        model = FixedTokenClaudeCodeModel(model_name="claude-sonnet-4-5")

        original_usage = RequestUsage(
            input_tokens=3,
            output_tokens=35,
            cache_write_tokens=8932,
            cache_read_tokens=16404,
        )
        original_response = ModelResponse(
            parts=[TextPart(content="test")],
            usage=original_usage,
            model_name="claude-sonnet-4-5",
            timestamp=datetime.now(tz=timezone.utc),
        )

        with patch.object(
            ClaudeCodeModel, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = original_response

            result = await model.request([], None, None)  # type: ignore[arg-type]

        uncached = (
            result.usage.input_tokens
            - result.usage.cache_write_tokens
            - result.usage.cache_read_tokens
        )
        assert uncached == 3
        assert uncached >= 0
