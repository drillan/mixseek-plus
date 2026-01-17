"""Tavilyプロバイダー実装."""

import os

from mixseek_plus.errors import ModelCreationError


def validate_tavily_credentials() -> None:
    """Tavily APIキーの検証を行う.

    環境変数 TAVILY_API_KEY を検証し、以下の条件を確認する:
    - 環境変数が設定されていること
    - 空文字でないこと
    - tvly- で始まること

    Raises:
        ModelCreationError: APIキーが未設定、空、または形式が不正な場合
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key or not api_key.strip():
        raise ModelCreationError(
            message="TAVILY_API_KEY環境変数が設定されていません",
            provider="tavily",
            suggestion="export TAVILY_API_KEY=your_key_here",
        )

    if not api_key.strip().startswith("tvly-"):
        raise ModelCreationError(
            message="TAVILY_API_KEYの形式が不正です（tvly-で始まる必要があります）",
            provider="tavily",
            suggestion="https://tavily.com でAPIキーを取得してください",
        )
