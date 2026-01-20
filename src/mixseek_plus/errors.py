"""モデル作成に関するカスタム例外定義."""

from __future__ import annotations

from typing import Literal

# Type alias for Tavily error types
TavilyErrorType = Literal[
    "AUTH_ERROR",
    "VALIDATION_ERROR",
    "RATE_LIMIT_ERROR",
    "SERVER_ERROR",
    "SERVICE_UNAVAILABLE",
    "TIMEOUT_ERROR",
    "RETRY_EXHAUSTED",
    "API_ERROR",
]

# Error types that are safe to retry
RETRYABLE_ERROR_TYPES: frozenset[TavilyErrorType] = frozenset(
    {
        "RATE_LIMIT_ERROR",
        "SERVER_ERROR",
        "SERVICE_UNAVAILABLE",
        "TIMEOUT_ERROR",
    }
)


class PlaywrightNotInstalledError(ImportError):
    """Playwrightがインストールされていない場合のエラー.

    Example:
        raise PlaywrightNotInstalledError()
        # Output:
        # playwright is not installed. Install it with:
        #   pip install mixseek-plus[playwright]
        #   playwright install chromium
    """

    def __init__(self, message: str | None = None) -> None:
        """PlaywrightNotInstalledErrorを初期化する.

        Args:
            message: カスタムエラーメッセージ（省略可）
        """
        if message is None:
            message = (
                "playwright is not installed. Install it with:\n"
                "  pip install mixseek-plus[playwright]\n"
                "  playwright install chromium"
            )
        super().__init__(message)


class FetchError(Exception):
    """ページ取得に失敗した場合のエラー.

    Attributes:
        url: 取得を試みたURL
        cause: 原因となった例外
        attempts: 試行回数
    """

    def __init__(
        self,
        message: str,
        url: str,
        cause: Exception | None = None,
        attempts: int = 1,
    ) -> None:
        """FetchErrorを初期化する.

        Args:
            message: エラーメッセージ
            url: 取得を試みたURL
            cause: 原因となった例外
            attempts: 試行回数
        """
        self.url = url
        self.cause = cause
        self.attempts = attempts
        super().__init__(message)


class ConversionError(Exception):
    """HTML→Markdown変換に失敗した場合のエラー.

    Attributes:
        url: 変換元のURL
        cause: 原因となった例外
    """

    def __init__(
        self,
        message: str,
        url: str,
        cause: Exception | None = None,
    ) -> None:
        """ConversionErrorを初期化する.

        Args:
            message: エラーメッセージ
            url: 変換元のURL
            cause: 原因となった例外
        """
        self.url = url
        self.cause = cause
        super().__init__(message)


class ModelCreationError(Exception):
    """モデル作成時のエラーを表す例外.

    Attributes:
        message: エラーメッセージ
        provider: エラーが発生したプロバイダー（判明している場合）
        suggestion: ユーザーへの解決策の提案
    """

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        suggestion: str = "",
    ) -> None:
        """ModelCreationErrorを初期化する.

        Args:
            message: エラーメッセージ
            provider: エラーが発生したプロバイダー（判明している場合）
            suggestion: ユーザーへの解決策の提案
        """
        self.provider = provider
        self.suggestion = suggestion
        full_message = f"[{provider}] {message}" if provider else message
        if suggestion:
            full_message += f"\n提案: {suggestion}"
        super().__init__(full_message)


class ClaudeCodeNotPatchedError(Exception):
    """ClaudeCodeモデルがパッチ未適用で使用された場合のエラー.

    Leader/EvaluatorでClaudeCodeモデルを使用するには、
    事前にmixseek_plus.patch_core()を呼び出す必要がある。
    """

    def __init__(self, message: str | None = None) -> None:
        """ClaudeCodeNotPatchedErrorを初期化する.

        Args:
            message: カスタムエラーメッセージ（省略可）
        """
        if message is None:
            message = (
                "ClaudeCode models are not yet enabled for Leader/Evaluator. "
                "Please call mixseek_plus.patch_core() before using claudecode: models. "
                "Example:\n"
                "    import mixseek_plus\n"
                "    mixseek_plus.patch_core()\n"
                "    # Now you can use claudecode: models with Leader/Evaluator"
            )
        super().__init__(message)


class TavilyAPIError(Exception):
    """Tavily API呼び出しエラー.

    Attributes:
        message: エラーメッセージ
        status_code: HTTPステータスコード（該当する場合）
        error_type: エラータイプ（TavilyErrorType Literal型で制限）
        is_retryable: リトライ可能かどうか（error_typeから自動導出）
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_type: TavilyErrorType = "API_ERROR",
    ) -> None:
        """TavilyAPIErrorを初期化する.

        Args:
            message: エラーメッセージ
            status_code: HTTPステータスコード（該当する場合）
            error_type: エラータイプ（TavilyErrorType）
        """
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type

    @property
    def message(self) -> str:
        """エラーメッセージを取得."""
        return str(self.args[0]) if self.args else ""

    @property
    def is_retryable(self) -> bool:
        """error_typeからリトライ可能かどうかを自動導出."""
        return self.error_type in RETRYABLE_ERROR_TYPES
