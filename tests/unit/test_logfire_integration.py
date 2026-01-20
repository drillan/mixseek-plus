"""Logfire統合の単体テスト.

US3: Logfireによるオブザーバビリティ統合
T021-T022: setup_logfire_instrumentation() のテスト
"""

import logging
from unittest.mock import MagicMock, patch

import pytest


class TestSetupLogfireInstrumentation:
    """setup_logfire_instrumentation() のテスト."""

    def test_function_exists(self) -> None:
        """setup_logfire_instrumentation 関数が存在することを確認."""
        from mixseek_plus.observability.logfire_integration import (
            setup_logfire_instrumentation,
        )

        assert callable(setup_logfire_instrumentation)

    def test_does_nothing_when_logfire_disabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MIXSEEK_LOGFIRE が無効時は何もしない."""
        from mixseek_plus.observability.logfire_integration import (
            setup_logfire_instrumentation,
        )

        monkeypatch.delenv("MIXSEEK_LOGFIRE", raising=False)

        # Should return False or None indicating nothing was done
        result = setup_logfire_instrumentation()
        assert result is False

    def test_warns_when_logfire_not_installed(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """logfire パッケージ未インストール時に警告を出力."""
        from mixseek_plus.observability.logfire_integration import (
            setup_logfire_instrumentation,
        )

        monkeypatch.setenv("MIXSEEK_LOGFIRE", "1")

        # Mock the import to fail
        with patch.dict("sys.modules", {"logfire": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                with caplog.at_level(logging.WARNING):
                    result = setup_logfire_instrumentation()

                # Should return False and log warning
                assert result is False

    def test_enables_instrumentation_when_logfire_available(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """logfire パッケージがインストールされている場合にインストルメンテーションを有効化."""
        from mixseek_plus.observability.logfire_integration import (
            setup_logfire_instrumentation,
        )

        monkeypatch.setenv("MIXSEEK_LOGFIRE", "1")

        # Mock logfire module
        mock_logfire = MagicMock()
        mock_logfire.instrument_pydantic_ai = MagicMock()

        with patch.dict("sys.modules", {"logfire": mock_logfire}):
            result = setup_logfire_instrumentation()

            # Should return True and call instrument_pydantic_ai
            assert result is True
            mock_logfire.instrument_pydantic_ai.assert_called_once()


class TestLogfireIntegrationExports:
    """observability モジュールのエクスポートテスト."""

    def test_setup_logfire_instrumentation_exported(self) -> None:
        """setup_logfire_instrumentation が observability モジュールからエクスポートされていることを確認."""
        from mixseek_plus.observability import setup_logfire_instrumentation

        assert callable(setup_logfire_instrumentation)
