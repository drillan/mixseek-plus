"""Groqプロバイダー実装."""

import os

from pydantic_ai.models.groq import GroqModel

from mixseek_plus.errors import ModelCreationError


def validate_groq_credentials() -> None:
    """Groq APIキーの検証を行う.

    環境変数 GROQ_API_KEY を検証し、以下の条件を確認する:
    - 環境変数が設定されていること
    - 空文字でないこと
    - gsk_ で始まること

    Raises:
        ModelCreationError: APIキーが未設定、空、または形式が不正な場合
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or not api_key.strip():
        raise ModelCreationError(
            message="GROQ_API_KEY環境変数が設定されていません",
            provider="groq",
            suggestion="export GROQ_API_KEY=your_key_here",
        )

    if not api_key.strip().startswith("gsk_"):
        raise ModelCreationError(
            message="GROQ_API_KEYの形式が不正です（gsk_で始まる必要があります）",
            provider="groq",
            suggestion="https://console.groq.com/keys でAPIキーを取得してください",
        )


def create_groq_model(model_name: str) -> GroqModel:
    """Groqモデルインスタンスを作成する.

    Args:
        model_name: モデル名（例: "llama-3.3-70b-versatile"）

    Returns:
        GroqModelインスタンス

    Raises:
        ModelCreationError: APIキーが未設定または形式が不正な場合
    """
    validate_groq_credentials()
    return GroqModel(model_name)
