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
