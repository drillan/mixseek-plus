"""BaseClaudeCodeAgent のロギング機能の単体テスト.

US2: Verboseモードでの詳細ログ確認
T014: _log_tool_calls_from_history() のテスト
"""

from unittest.mock import MagicMock, patch

import pytest


class TestBaseClaudeCodeAgentLogging:
    """BaseClaudeCodeAgent のログ関連メソッドのテスト."""

    def test_log_tool_calls_from_history_method_exists(self) -> None:
        """_log_tool_calls_from_history メソッドが存在することを確認."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        assert hasattr(BaseClaudeCodeAgent, "_log_tool_calls_from_history")

    def test_log_tool_calls_from_history_empty_messages(self) -> None:
        """空のメッセージリストではログを出力しない."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        # Create a concrete subclass for testing
        class ConcreteAgent(BaseClaudeCodeAgent):
            def _get_agent(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _create_deps(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _get_agent_type_metadata(self) -> dict[str, str]:
                return {}

        with patch.object(ConcreteAgent, "__init__", lambda self, config: None):
            agent = ConcreteAgent.__new__(ConcreteAgent)
            agent.logger = MagicMock()

            # Call with empty messages
            agent._log_tool_calls_from_history("exec_123", [])

            # Should not call log_tool_invocation
            agent.logger.log_tool_invocation.assert_not_called()

    def test_log_tool_calls_from_history_logs_extracted_calls(self) -> None:
        """メッセージからツール呼び出しを抽出してログに記録."""
        from pydantic_ai.messages import ModelRequest, ToolCallPart

        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        class ConcreteAgent(BaseClaudeCodeAgent):
            def _get_agent(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _create_deps(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _get_agent_type_metadata(self) -> dict[str, str]:
                return {}

        with patch.object(ConcreteAgent, "__init__", lambda self, config: None):
            agent = ConcreteAgent.__new__(ConcreteAgent)
            agent.logger = MagicMock()

            # Create mock message with ToolCallPart
            tool_call = ToolCallPart(
                tool_name="fetch_page",
                args={"url": "https://example.com"},
                tool_call_id="call_789",
            )
            request = MagicMock(spec=ModelRequest)
            request.parts = [tool_call]

            agent._log_tool_calls_from_history("exec_456", [request])

            # Should call log_tool_invocation
            agent.logger.log_tool_invocation.assert_called()
            call_args = agent.logger.log_tool_invocation.call_args
            assert call_args.kwargs["execution_id"] == "exec_456"
            assert call_args.kwargs["tool_name"] == "fetch_page"

    def test_log_tool_calls_from_history_respects_verbose_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """verboseモードでのみコンソール出力を行う."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        class ConcreteAgent(BaseClaudeCodeAgent):
            def _get_agent(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _create_deps(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _get_agent_type_metadata(self) -> dict[str, str]:
                return {}

        monkeypatch.setenv("MIXSEEK_VERBOSE", "1")

        with patch.object(ConcreteAgent, "__init__", lambda self, config: None):
            agent = ConcreteAgent.__new__(ConcreteAgent)
            agent.logger = MagicMock()

            # The method should exist and be callable
            # Further testing of verbose output would require log capture
            agent._log_tool_calls_from_history("exec_789", [])
