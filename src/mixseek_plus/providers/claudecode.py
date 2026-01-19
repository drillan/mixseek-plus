"""ClaudeCodeプロバイダー実装."""

from typing import TypedDict

from claudecode_model import ClaudeCodeModel
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import Model, ModelRequestParameters
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import RequestUsage


class FixedTokenClaudeCodeModel(ClaudeCodeModel):
    """トークン計算を補正したClaudeCodeModel.

    Claude Code CLIのトークン使用量レポートはpydantic-aiの期待する形式と異なる:
    - CLI: input_tokensはキャッシュされていないトークンのみ
    - pydantic-ai: input_tokensは全入力トークン（キャッシュ含む）

    このクラスはinput_tokensを全トークンの合計に補正し、
    genai_pricesのコスト計算でエラーが発生しないようにする。
    """

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """リクエストを実行し、トークン使用量を補正.

        Args:
            messages: モデルに送信するメッセージリスト
            model_settings: モデル設定
            model_request_parameters: リクエストパラメータ

        Returns:
            トークン使用量が補正されたModelResponse
        """
        response = await super().request(
            messages, model_settings, model_request_parameters
        )
        return self._fix_token_usage(response)

    def _fix_token_usage(self, response: ModelResponse) -> ModelResponse:
        """input_tokensを全入力トークンの合計に補正.

        genai_pricesの計算式:
            uncached = input_tokens - cache_write - cache_read

        CLIの場合（Anthropic API → pydantic-ai フィールド対応）:
            - input_tokens = uncached のみ
            - cache_write_tokens (pydantic-ai) = cache_creation_input_tokens (Anthropic API)
            - cache_read_tokens (pydantic-ai) = cache_read_input_tokens (Anthropic API)

        補正後:
            - input_tokens = uncached + cache_write + cache_read

        Args:
            response: 元のModelResponse

        Returns:
            トークン使用量が補正されたModelResponse
        """
        usage = response.usage

        # 防御的にNoneチェックを追加（将来のpydantic-ai変更に備えて）
        cache_write = usage.cache_write_tokens or 0
        cache_read = usage.cache_read_tokens or 0
        total_input = usage.input_tokens + cache_write + cache_read

        fixed_usage = RequestUsage(
            input_tokens=total_input,
            output_tokens=usage.output_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            cache_read_tokens=usage.cache_read_tokens,
            input_audio_tokens=usage.input_audio_tokens,
            cache_audio_read_tokens=usage.cache_audio_read_tokens,
            output_audio_tokens=usage.output_audio_tokens,
            details=usage.details,
        )

        return ModelResponse(
            parts=response.parts,
            usage=fixed_usage,
            model_name=response.model_name,
            timestamp=response.timestamp,
        )


class ClaudeCodeToolSettings(TypedDict, total=False):
    """ClaudeCode-specific tool settings from TOML config.

    Attributes:
        preset: Name of a preset defined in configs/presets/claudecode.toml.
                When specified, the preset's settings are loaded and merged
                with any additional settings provided here (local settings
                take precedence).
        allowed_tools: List of tools that are allowed to be used.
        disallowed_tools: List of tools that are disallowed.
        permission_mode: Permission mode (e.g., "bypassPermissions").
        working_directory: Working directory path.
        max_turns: Maximum number of turns.
    """

    preset: str
    allowed_tools: list[str]
    disallowed_tools: list[str]
    permission_mode: str
    working_directory: str
    max_turns: int


def create_claudecode_model(
    model_name: str,
    *,
    tool_settings: ClaudeCodeToolSettings | None = None,
) -> Model:
    """ClaudeCodeモデルインスタンスを作成する.

    Args:
        model_name: モデル名（例: "claude-sonnet-4-5"）
        tool_settings: ClaudeCode固有のツール設定（オプション）

    Returns:
        FixedTokenClaudeCodeModelインスタンス

    Note:
        ClaudeCodeはClaude Code CLIのセッション認証を使用するため、
        環境変数によるAPIキー検証は行わない。
        CLIが見つからない場合はClaudeCodeModel側でエラーが発生する。

        FixedTokenClaudeCodeModelはトークン使用量の計算を補正し、
        genai_pricesのコスト計算でエラーが発生しないようにする。
    """
    if tool_settings is None:
        return FixedTokenClaudeCodeModel(model_name=model_name)

    return FixedTokenClaudeCodeModel(
        model_name=model_name,
        allowed_tools=tool_settings.get("allowed_tools"),
        disallowed_tools=tool_settings.get("disallowed_tools"),
        permission_mode=tool_settings.get("permission_mode"),
        working_directory=tool_settings.get("working_directory"),
        max_turns=tool_settings.get("max_turns"),
    )
