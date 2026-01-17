"""モデル作成に関するカスタム例外定義."""


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
