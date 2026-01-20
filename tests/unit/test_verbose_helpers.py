"""Unit tests for verbose helper functions.

Tests for log_verbose_tool_start() and log_verbose_tool_done()
which provide unified verbose logging across all agent types.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import patch


if TYPE_CHECKING:
    from pytest import LogCaptureFixture


class TestLogVerboseToolStart:
    """Tests for log_verbose_tool_start()."""

    def test_logs_when_verbose_mode_enabled(self, caplog: LogCaptureFixture) -> None:
        """Should log tool start when verbose mode is enabled."""
        from mixseek_plus.utils.verbose import log_verbose_tool_start

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=True),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            log_verbose_tool_start("fetch_page", {"url": "https://example.com"})

        assert "[Tool Start]" in caplog.text
        assert "fetch_page" in caplog.text
        assert "url=" in caplog.text

    def test_does_not_log_when_verbose_mode_disabled(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Should not log when verbose mode is disabled."""
        from mixseek_plus.utils.verbose import log_verbose_tool_start

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=False),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            log_verbose_tool_start("fetch_page", {"url": "https://example.com"})

        assert caplog.text == ""

    def test_truncates_long_parameter_values(self, caplog: LogCaptureFixture) -> None:
        """Should truncate parameter values that exceed max length."""
        from mixseek_plus.utils.verbose import log_verbose_tool_start

        long_value = "x" * 500

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=True),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            log_verbose_tool_start("test_tool", {"content": long_value})

        # Value should be truncated
        assert "..." in caplog.text
        # Should not contain full value
        assert long_value not in caplog.text

    def test_handles_empty_params(self, caplog: LogCaptureFixture) -> None:
        """Should handle empty parameters dictionary."""
        from mixseek_plus.utils.verbose import log_verbose_tool_start

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=True),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            log_verbose_tool_start("test_tool", {})

        assert "[Tool Start]" in caplog.text
        assert "test_tool" in caplog.text


class TestLogVerboseToolDone:
    """Tests for log_verbose_tool_done()."""

    def test_logs_success_status(self, caplog: LogCaptureFixture) -> None:
        """Should log completion with success status."""
        from mixseek_plus.utils.verbose import log_verbose_tool_done

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=True),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            log_verbose_tool_done("fetch_page", "success", 1234, "Page content...")

        assert "[Tool Done]" in caplog.text
        assert "fetch_page" in caplog.text
        assert "success" in caplog.text
        assert "1234ms" in caplog.text

    def test_logs_error_status(self, caplog: LogCaptureFixture) -> None:
        """Should log completion with error status."""
        from mixseek_plus.utils.verbose import log_verbose_tool_done

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=True),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            log_verbose_tool_done("fetch_page", "error", 500)

        assert "[Tool Done]" in caplog.text
        assert "error" in caplog.text
        assert "500ms" in caplog.text

    def test_does_not_log_when_verbose_mode_disabled(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Should not log when verbose mode is disabled."""
        from mixseek_plus.utils.verbose import log_verbose_tool_done

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=False),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            log_verbose_tool_done("fetch_page", "success", 1234)

        assert caplog.text == ""

    def test_logs_result_preview_when_provided(self, caplog: LogCaptureFixture) -> None:
        """Should log result preview when provided."""
        from mixseek_plus.utils.verbose import log_verbose_tool_done

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=True),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            log_verbose_tool_done(
                "fetch_page", "success", 1234, result_preview="# Page Title\n\nContent"
            )

        assert "[Tool Result Preview]" in caplog.text
        assert "Page Title" in caplog.text

    def test_truncates_long_result_preview(self, caplog: LogCaptureFixture) -> None:
        """Should truncate result preview that exceeds max length."""
        from mixseek_plus.utils.verbose import log_verbose_tool_done

        # Use 600 chars to exceed RESULT_PREVIEW_MAX_LENGTH (500)
        long_result = "x" * 600

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=True),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            log_verbose_tool_done(
                "fetch_page", "success", 1234, result_preview=long_result
            )

        # Should contain preview but not full result
        assert "[Tool Result Preview]" in caplog.text
        assert long_result not in caplog.text
        assert "..." in caplog.text

    def test_replaces_newlines_in_result_preview(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Should replace newlines with escaped \\n in result preview."""
        from mixseek_plus.utils.verbose import log_verbose_tool_done

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=True),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            log_verbose_tool_done(
                "fetch_page", "success", 1234, result_preview="Line1\nLine2\nLine3"
            )

        # Newlines should be escaped for single-line output
        assert "\\n" in caplog.text


class TestFormatParamsForVerbose:
    """Tests for _format_params_for_verbose() helper."""

    def test_formats_simple_params(self) -> None:
        """Should format simple parameters correctly."""
        # Import from verbose module directly (not exported in __all__)
        from mixseek_plus.utils.verbose import _format_params_for_verbose

        result = _format_params_for_verbose(
            {"url": "https://example.com", "timeout": 5000}
        )

        assert "url=https://example.com" in result
        assert "timeout=5000" in result

    def test_truncates_long_values(self) -> None:
        """Should truncate long parameter values."""
        from mixseek_plus.utils.verbose import _format_params_for_verbose

        long_value = "x" * 200
        result = _format_params_for_verbose({"content": long_value})

        assert "..." in result
        assert len(result) < len(long_value)

    def test_handles_empty_params(self) -> None:
        """Should handle empty parameters dictionary."""
        from mixseek_plus.utils.verbose import _format_params_for_verbose

        result = _format_params_for_verbose({})

        assert result == ""

    def test_handles_various_types(self) -> None:
        """Should handle various parameter types."""
        from mixseek_plus.utils.verbose import _format_params_for_verbose

        result = _format_params_for_verbose(
            {
                "string": "value",
                "number": 42,
                "boolean": True,
                "none": None,
            }
        )

        assert "string=value" in result
        assert "number=42" in result
        assert "boolean=True" in result
        assert "none=None" in result


class TestEnsureVerboseLoggingConfigured:
    """Tests for ensure_verbose_logging_configured()."""

    def test_is_idempotent(self) -> None:
        """Should be safe to call multiple times."""
        from mixseek_plus.utils.verbose import ensure_verbose_logging_configured

        # Call multiple times - should not raise
        ensure_verbose_logging_configured()
        ensure_verbose_logging_configured()
        ensure_verbose_logging_configured()

    def test_configures_member_agents_logger_when_verbose_enabled(self) -> None:
        """Should configure mixseek.member_agents logger when verbose mode is enabled."""
        import logging

        import mixseek_plus.utils.verbose as verbose_module
        from mixseek_plus.utils.verbose import ensure_verbose_logging_configured

        # Reset the global flag and logger level for clean test state
        original_flag = verbose_module._VERBOSE_LOGGING_CONFIGURED
        verbose_module._VERBOSE_LOGGING_CONFIGURED = False
        member_logger = logging.getLogger("mixseek.member_agents")
        original_level = member_logger.level
        member_logger.setLevel(logging.NOTSET)

        try:
            with patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=True):
                ensure_verbose_logging_configured()

            # Logger should be configured at DEBUG level when verbose mode is enabled
            assert member_logger.level == logging.DEBUG
        finally:
            # Restore original state
            verbose_module._VERBOSE_LOGGING_CONFIGURED = original_flag
            member_logger.setLevel(original_level)

    def test_does_not_configure_when_verbose_disabled(self) -> None:
        """Should not configure logger when verbose mode is disabled."""
        import logging

        import mixseek_plus.utils.verbose as verbose_module
        from mixseek_plus.utils.verbose import ensure_verbose_logging_configured

        # Reset the global flag and logger level for clean test state
        original_flag = verbose_module._VERBOSE_LOGGING_CONFIGURED
        verbose_module._VERBOSE_LOGGING_CONFIGURED = False
        member_logger = logging.getLogger("mixseek.member_agents")
        original_level = member_logger.level
        member_logger.setLevel(logging.WARNING)

        try:
            with patch(
                "mixseek_plus.utils.verbose.is_verbose_mode", return_value=False
            ):
                ensure_verbose_logging_configured()

            # Logger level should not be changed when verbose mode is disabled
            assert member_logger.level == logging.WARNING
        finally:
            # Restore original state
            verbose_module._VERBOSE_LOGGING_CONFIGURED = original_flag
            member_logger.setLevel(original_level)


class TestLogToolCallsIfVerbose:
    """Tests for PydanticAgentExecutorMixin._log_tool_calls_if_verbose()."""

    def test_handles_empty_messages(self) -> None:
        """Should handle empty messages list without error."""
        from unittest.mock import MagicMock

        from mixseek_plus.agents.mixins.execution import PydanticAgentExecutorMixin

        # Create a mock object that satisfies AgentProtocol
        mock_agent = MagicMock()
        mock_agent.logger = MagicMock()

        # Call the method with empty messages - should not raise
        PydanticAgentExecutorMixin._log_tool_calls_if_verbose(
            mock_agent, "exec-123", []
        )

        # Logger should not be called for empty messages
        mock_agent.logger.log_tool_invocation.assert_not_called()

    def test_extracts_and_logs_tool_calls(self, caplog: LogCaptureFixture) -> None:
        """Should extract tool calls and log them."""
        from unittest.mock import MagicMock, patch

        from pydantic_ai.messages import ToolCallPart

        from mixseek_plus.agents.mixins.execution import PydanticAgentExecutorMixin

        # Create a mock ModelRequest with a ToolCallPart
        tool_call = ToolCallPart(
            tool_name="test_tool",
            args={"param": "value"},
            tool_call_id="call_123",
        )
        mock_request = MagicMock()
        mock_request.parts = [tool_call]

        # Create a mock agent
        mock_agent = MagicMock()
        mock_agent.logger = MagicMock()

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=True),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            PydanticAgentExecutorMixin._log_tool_calls_if_verbose(
                mock_agent, "exec-456", [mock_request]
            )

        # Should log via verbose helpers
        assert "[Tool Start]" in caplog.text or "[Tool Done]" in caplog.text
        # Should also log via MemberAgentLogger
        mock_agent.logger.log_tool_invocation.assert_called_once()

    def test_respects_verbose_mode_disabled(self, caplog: LogCaptureFixture) -> None:
        """Should not log to console when verbose mode is disabled."""
        from unittest.mock import MagicMock, patch

        from pydantic_ai.messages import ToolCallPart

        from mixseek_plus.agents.mixins.execution import PydanticAgentExecutorMixin

        tool_call = ToolCallPart(
            tool_name="test_tool",
            args={"param": "value"},
            tool_call_id="call_789",
        )
        mock_request = MagicMock()
        mock_request.parts = [tool_call]

        mock_agent = MagicMock()
        mock_agent.logger = MagicMock()

        with (
            patch("mixseek_plus.utils.verbose.is_verbose_mode", return_value=False),
            caplog.at_level(logging.INFO, logger="mixseek.member_agents"),
        ):
            PydanticAgentExecutorMixin._log_tool_calls_if_verbose(
                mock_agent, "exec-789", [mock_request]
            )

        # Console verbose logs should not appear
        assert "[Tool Start]" not in caplog.text
        assert "[Tool Done]" not in caplog.text
        # But file logging should still occur
        mock_agent.logger.log_tool_invocation.assert_called_once()
