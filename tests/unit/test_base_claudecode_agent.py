"""BaseClaudeCodeAgentベースクラスの単体テスト.

CC-031, CC-061の検証
"""

import pytest

from mixseek.models.member_agent import MemberAgentConfig


class TestBaseClaudeCodeAgent:
    """BaseClaudeCodeAgentクラスのテスト."""

    def test_base_claudecode_agent_exists(self) -> None:
        """BaseClaudeCodeAgentクラスが存在することを確認 (CC-031)."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        assert BaseClaudeCodeAgent is not None

    def test_base_claudecode_agent_inherits_from_base_member_agent(self) -> None:
        """BaseClaudeCodeAgentがBaseMemberAgentを継承していることを確認 (CC-031)."""
        from mixseek.agents.member.base import BaseMemberAgent

        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        assert issubclass(BaseClaudeCodeAgent, BaseMemberAgent)

    def test_base_claudecode_agent_is_abstract(self) -> None:
        """BaseClaudeCodeAgentが抽象クラスであることを確認."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="Test instruction",
        )

        # 抽象メソッドがあるため、直接インスタンス化できない
        with pytest.raises(TypeError):
            BaseClaudeCodeAgent(config)  # type: ignore[abstract]
