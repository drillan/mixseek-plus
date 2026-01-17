"""モデルファクトリー - LLMモデルインスタンスの作成."""

from mixseek.agents.member.plain import create_authenticated_model
from pydantic_ai.models import Model
from pydantic_ai.models.groq import GroqModel

from mixseek_plus.errors import ModelCreationError
from mixseek_plus.providers import (
    ALL_PROVIDER_PREFIXES,
    CORE_PROVIDER_PREFIXES,
    GROQ_PROVIDER_PREFIX,
)
from mixseek_plus.providers.groq import create_groq_model


def _validate_model_id_format(model_id: str) -> None:
    """モデルID形式を検証する.

    Args:
        model_id: 検証するモデルID

    Raises:
        ModelCreationError: コロンが含まれていない場合
    """
    if ":" not in model_id:
        raise ModelCreationError(
            message="モデルIDは 'provider:model-name' 形式で指定してください",
            suggestion="例: groq:llama-3.3-70b-versatile",
        )


def _get_provider_prefix(model_id: str) -> str:
    """モデルIDからプロバイダープレフィックスを抽出する.

    Args:
        model_id: モデルID

    Returns:
        プロバイダープレフィックス（コロンを含む）
    """
    provider = model_id.split(":")[0]
    return f"{provider}:"


def _validate_provider(provider_prefix: str) -> None:
    """プロバイダーがサポートされているか検証する.

    Args:
        provider_prefix: プロバイダープレフィックス（コロンを含む）

    Raises:
        ModelCreationError: サポートされていないプロバイダーの場合
    """
    if provider_prefix not in ALL_PROVIDER_PREFIXES:
        provider_name = provider_prefix.rstrip(":")
        supported_providers = ", ".join(
            p.rstrip(":") for p in sorted(ALL_PROVIDER_PREFIXES)
        )
        raise ModelCreationError(
            message=f"サポートされていないプロバイダー: {provider_name}",
            suggestion=f"サポートされているプロバイダー: {supported_providers}",
        )


def create_model(model_id: str) -> GroqModel | Model:
    """モデルIDからLLMモデルインスタンスを作成する.

    Args:
        model_id: プロバイダープレフィックス付きのモデルID
            Groqモデルの場合: "groq:{model-name}"
            例: "groq:llama-3.3-70b-versatile", "groq:qwen/qwen3-32b"

            mixseek-coreモデルの場合: "{provider}:{model-name}"
            例: "openai:gpt-4o", "anthropic:claude-sonnet-4-5-20250929"

    Returns:
        LLMモデルインスタンス。
        - Groqモデルの場合: pydantic_ai.models.groq.GroqModel
        - mixseek-coreモデルの場合: 各プロバイダーのModelサブクラス

    Raises:
        ModelCreationError: モデル作成に失敗した場合
    """
    # モデルID形式の検証
    _validate_model_id_format(model_id)

    # プロバイダーの抽出と検証
    provider_prefix = _get_provider_prefix(model_id)
    _validate_provider(provider_prefix)

    # Groqプロバイダーの場合
    if provider_prefix == GROQ_PROVIDER_PREFIX:
        model_name = model_id[len(GROQ_PROVIDER_PREFIX) :]
        return create_groq_model(model_name)

    # mixseek-coreプロバイダーの場合
    if provider_prefix in CORE_PROVIDER_PREFIXES:
        return create_authenticated_model(model_id)

    # ここには到達しないはずだが、安全のため
    raise ModelCreationError(
        message=f"プロバイダーの処理が実装されていません: {provider_prefix}",
    )
