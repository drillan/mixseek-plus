"""ClaudeCodeプロバイダー実装."""

from typing import TypedDict

from claudecode_model import ClaudeCodeModel
from pydantic_ai.models import Model


class ClaudeCodeToolSettings(TypedDict, total=False):
    """ClaudeCode-specific tool settings from TOML config."""

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
        ClaudeCodeModelインスタンス

    Note:
        ClaudeCodeはClaude Code CLIのセッション認証を使用するため、
        環境変数によるAPIキー検証は行わない。
        CLIが見つからない場合はClaudeCodeModel側でエラーが発生する。
    """
    if tool_settings is None:
        return ClaudeCodeModel(model_name=model_name)

    return ClaudeCodeModel(
        model_name=model_name,
        allowed_tools=tool_settings.get("allowed_tools"),
        disallowed_tools=tool_settings.get("disallowed_tools"),
        permission_mode=tool_settings.get("permission_mode"),
        working_directory=tool_settings.get("working_directory"),
        max_turns=tool_settings.get("max_turns"),
    )
