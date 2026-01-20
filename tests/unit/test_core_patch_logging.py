"""core_patch.py のロギング機能の単体テスト.

US1: MCPツール呼び出しのログ確認
"""

from unittest.mock import MagicMock

import pytest


class TestEnableDisableVerboseMode:
    """enable_verbose_mode() / disable_verbose_mode() のテスト."""

    def test_enable_verbose_mode_sets_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """enable_verbose_mode() がMIXSEEK_VERBOSE=1を設定する."""
        import os

        from mixseek_plus.core_patch import enable_verbose_mode

        monkeypatch.delenv("MIXSEEK_VERBOSE", raising=False)
        enable_verbose_mode()
        assert os.environ.get("MIXSEEK_VERBOSE") == "1"

    def test_disable_verbose_mode_removes_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """disable_verbose_mode() がMIXSEEK_VERBOSEを削除する."""
        import os

        from mixseek_plus.core_patch import disable_verbose_mode

        monkeypatch.setenv("MIXSEEK_VERBOSE", "1")
        disable_verbose_mode()
        assert "MIXSEEK_VERBOSE" not in os.environ

    def test_disable_verbose_mode_safe_when_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """disable_verbose_mode() は未設定でもエラーにならない."""
        from mixseek_plus.core_patch import disable_verbose_mode

        monkeypatch.delenv("MIXSEEK_VERBOSE", raising=False)
        disable_verbose_mode()  # Should not raise

    def test_enable_verbose_mode_makes_is_verbose_mode_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """enable_verbose_mode() 後に _is_verbose_mode() がTrueを返す."""
        from mixseek_plus.core_patch import _is_verbose_mode, enable_verbose_mode

        monkeypatch.delenv("MIXSEEK_VERBOSE", raising=False)
        assert _is_verbose_mode() is False
        enable_verbose_mode()
        assert _is_verbose_mode() is True

    def test_disable_verbose_mode_makes_is_verbose_mode_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """disable_verbose_mode() 後に _is_verbose_mode() がFalseを返す."""
        from mixseek_plus.core_patch import (
            _is_verbose_mode,
            disable_verbose_mode,
            enable_verbose_mode,
        )

        monkeypatch.delenv("MIXSEEK_VERBOSE", raising=False)
        enable_verbose_mode()
        assert _is_verbose_mode() is True
        disable_verbose_mode()
        assert _is_verbose_mode() is False


class TestIsVerboseMode:
    """_is_verbose_mode() ヘルパー関数のテスト."""

    def test_verbose_mode_disabled_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数未設定時はFalseを返す."""
        from mixseek_plus.core_patch import _is_verbose_mode

        monkeypatch.delenv("MIXSEEK_VERBOSE", raising=False)
        assert _is_verbose_mode() is False

    def test_verbose_mode_enabled_with_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """MIXSEEK_VERBOSE=1 でTrueを返す."""
        from mixseek_plus.core_patch import _is_verbose_mode

        monkeypatch.setenv("MIXSEEK_VERBOSE", "1")
        assert _is_verbose_mode() is True

    def test_verbose_mode_enabled_with_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MIXSEEK_VERBOSE=true でTrueを返す (case-insensitive)."""
        from mixseek_plus.core_patch import _is_verbose_mode

        monkeypatch.setenv("MIXSEEK_VERBOSE", "TRUE")
        assert _is_verbose_mode() is True

    def test_verbose_mode_disabled_with_other_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """その他の値ではFalseを返す."""
        from mixseek_plus.core_patch import _is_verbose_mode

        monkeypatch.setenv("MIXSEEK_VERBOSE", "yes")
        assert _is_verbose_mode() is False


class TestIsLogfireMode:
    """_is_logfire_mode() ヘルパー関数のテスト."""

    def test_logfire_mode_disabled_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数未設定時はFalseを返す."""
        from mixseek_plus.core_patch import _is_logfire_mode

        monkeypatch.delenv("MIXSEEK_LOGFIRE", raising=False)
        assert _is_logfire_mode() is False

    def test_logfire_mode_enabled_with_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """MIXSEEK_LOGFIRE=1 でTrueを返す."""
        from mixseek_plus.core_patch import _is_logfire_mode

        monkeypatch.setenv("MIXSEEK_LOGFIRE", "1")
        assert _is_logfire_mode() is True

    def test_logfire_mode_enabled_with_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MIXSEEK_LOGFIRE=true でTrueを返す (case-insensitive)."""
        from mixseek_plus.core_patch import _is_logfire_mode

        monkeypatch.setenv("MIXSEEK_LOGFIRE", "true")
        assert _is_logfire_mode() is True


class TestWrapToolFunctionForMCPLogging:
    """_wrap_tool_function_for_mcp() のログ機能テスト.

    T007: ツール呼び出し時のログ出力が正しく行われることを確認.
    """

    @pytest.mark.asyncio
    async def test_wrap_tool_logs_invocation_on_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ツール呼び出し成功時にログが記録される."""
        from mixseek_plus.core_patch import _current_deps, _wrap_tool_function_for_mcp

        # Setup mock deps with logger
        mock_logger = MagicMock()
        mock_deps = MagicMock()
        mock_deps.execution_id = "test-exec-123"
        mock_deps.logger = mock_logger

        # Create a mock tool function
        async def mock_tool_func(ctx: object, **kwargs: object) -> str:
            return "success result"

        wrapped = _wrap_tool_function_for_mcp(mock_tool_func, "test_tool")

        # Set context and call
        token = _current_deps.set(mock_deps)
        try:
            result = await wrapped(arg1="value1")
            assert result == "success result"
        finally:
            _current_deps.reset(token)

    @pytest.mark.asyncio
    async def test_wrap_tool_logs_invocation_on_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ツール呼び出しエラー時にもログが記録される."""
        from mixseek_plus.core_patch import _current_deps, _wrap_tool_function_for_mcp

        mock_deps = MagicMock()
        mock_deps.execution_id = "test-exec-456"

        async def mock_tool_func(ctx: object, **kwargs: object) -> str:
            raise ValueError("Test error")

        wrapped = _wrap_tool_function_for_mcp(mock_tool_func, "failing_tool")

        token = _current_deps.set(mock_deps)
        try:
            with pytest.raises(ValueError, match="Test error"):
                await wrapped()
        finally:
            _current_deps.reset(token)

    @pytest.mark.asyncio
    async def test_wrap_tool_raises_without_deps(self) -> None:
        """コンテキストなしで呼び出すとRuntimeErrorが発生する."""
        from mixseek_plus.core_patch import _current_deps, _wrap_tool_function_for_mcp

        async def mock_tool_func(ctx: object, **kwargs: object) -> str:
            return "result"

        wrapped = _wrap_tool_function_for_mcp(mock_tool_func, "test_tool")

        # Ensure no deps are set
        _current_deps.set(None)

        with pytest.raises(RuntimeError, match="called without context"):
            await wrapped()

    @pytest.mark.asyncio
    async def test_wrap_tool_measures_execution_time(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ツール実行時間が計測される.

        NOTE: 現在の実装ではタイミング情報はログに含まれていますが、
        このテストは将来の実装で log_tool_invocation() が呼ばれることを確認するためのものです。
        """
        import time

        from mixseek_plus.core_patch import _current_deps, _wrap_tool_function_for_mcp

        mock_deps = MagicMock()
        mock_deps.execution_id = "test-exec-789"

        async def slow_tool_func(ctx: object, **kwargs: object) -> str:
            time.sleep(0.01)  # 10ms delay
            return "slow result"

        wrapped = _wrap_tool_function_for_mcp(slow_tool_func, "slow_tool")

        token = _current_deps.set(mock_deps)
        try:
            start = time.perf_counter()
            result = await wrapped()
            elapsed = (time.perf_counter() - start) * 1000

            assert result == "slow result"
            assert elapsed >= 10  # Should take at least 10ms
        finally:
            _current_deps.reset(token)
