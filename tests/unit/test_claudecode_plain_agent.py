"""ClaudeCodePlainAgentの単体テスト.

CC-030, CC-031, CC-032, CC-034の検証
"""

from mixseek.models.member_agent import MemberAgentConfig


class TestClaudeCodePlainAgent:
    """ClaudeCodePlainAgentクラスのテスト."""

    def test_claudecode_plain_agent_exists(self) -> None:
        """ClaudeCodePlainAgentクラスが存在することを確認 (CC-030)."""
        from mixseek_plus.agents.claudecode_agent import ClaudeCodePlainAgent

        assert ClaudeCodePlainAgent is not None

    def test_claudecode_plain_agent_inherits_from_base(self) -> None:
        """ClaudeCodePlainAgentがBaseClaudeCodeAgentを継承していることを確認 (CC-031)."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent
        from mixseek_plus.agents.claudecode_agent import ClaudeCodePlainAgent

        assert issubclass(ClaudeCodePlainAgent, BaseClaudeCodeAgent)

    def test_claudecode_plain_agent_can_be_instantiated(self) -> None:
        """ClaudeCodePlainAgentがインスタンス化できることを確認 (CC-030)."""
        from mixseek_plus.agents.claudecode_agent import ClaudeCodePlainAgent

        config = MemberAgentConfig(
            name="test-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
        )

        agent = ClaudeCodePlainAgent(config)

        assert agent is not None
        assert agent.agent_name == "test-agent"

    def test_claudecode_plain_agent_with_temperature(self) -> None:
        """ClaudeCodePlainAgentがtemperature設定を受け付けることを確認."""
        from mixseek_plus.agents.claudecode_agent import ClaudeCodePlainAgent

        config = MemberAgentConfig(
            name="temp-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
            temperature=0.7,
        )

        agent = ClaudeCodePlainAgent(config)

        assert agent.config.temperature == 0.7

    def test_claudecode_plain_agent_with_max_tokens(self) -> None:
        """ClaudeCodePlainAgentがmax_tokens設定を受け付けることを確認."""
        from mixseek_plus.agents.claudecode_agent import ClaudeCodePlainAgent

        config = MemberAgentConfig(
            name="token-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
            max_tokens=512,
        )

        agent = ClaudeCodePlainAgent(config)

        assert agent.config.max_tokens == 512

    def test_claudecode_plain_agent_agent_type(self) -> None:
        """ClaudeCodePlainAgentのagent_typeプロパティを確認."""
        from mixseek_plus.agents.claudecode_agent import ClaudeCodePlainAgent

        config = MemberAgentConfig(
            name="type-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
        )

        agent = ClaudeCodePlainAgent(config)

        assert agent.agent_type == "custom"


class TestClaudeCodePlainAgentExport:
    """ClaudeCodePlainAgentのエクスポートテスト."""

    def test_claudecode_plain_agent_exported_from_agents(self) -> None:
        """ClaudeCodePlainAgentがagentsモジュールからエクスポートされていることを確認."""
        from mixseek_plus.agents import ClaudeCodePlainAgent

        assert ClaudeCodePlainAgent is not None

    def test_claudecode_plain_agent_exported_from_root(self) -> None:
        """ClaudeCodePlainAgentがルートモジュールからエクスポートされていることを確認 (CC-070)."""
        from mixseek_plus import ClaudeCodePlainAgent

        assert ClaudeCodePlainAgent is not None


class TestClaudeCodeToolSettings:
    """ClaudeCode tool_settings parsing tests (CC-040, CC-041, CC-042, CC-043).

    These tests verify that tool_settings.claudecode section is correctly parsed
    and passed to create_claudecode_model().
    """

    def test_extract_claudecode_tool_settings_allowed_tools(self) -> None:
        """CC-040: _extract_claudecode_tool_settings extracts allowed_tools."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        config = MemberAgentConfig(
            name="tool-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
            tool_settings={  # type: ignore[arg-type]
                "claudecode": {
                    "allowed_tools": ["Read", "Glob", "Grep"],
                }
            },
        )

        # Test the extraction method directly (it's a static method functionally)
        # Create a minimal mock to test the method
        result = BaseClaudeCodeAgent._extract_claudecode_tool_settings(
            None,  # type: ignore[arg-type]
            config,
        )
        assert result is not None
        assert result.get("allowed_tools") == ["Read", "Glob", "Grep"]

    def test_extract_claudecode_tool_settings_disallowed_tools(self) -> None:
        """CC-041: _extract_claudecode_tool_settings extracts disallowed_tools."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        config = MemberAgentConfig(
            name="tool-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
            tool_settings={  # type: ignore[arg-type]
                "claudecode": {
                    "disallowed_tools": ["Write", "Edit"],
                }
            },
        )

        result = BaseClaudeCodeAgent._extract_claudecode_tool_settings(
            None,  # type: ignore[arg-type]
            config,
        )
        assert result is not None
        assert result.get("disallowed_tools") == ["Write", "Edit"]

    def test_extract_claudecode_tool_settings_permission_mode(self) -> None:
        """CC-042: _extract_claudecode_tool_settings extracts permission_mode."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        config = MemberAgentConfig(
            name="tool-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
            tool_settings={  # type: ignore[arg-type]
                "claudecode": {
                    "permission_mode": "bypassPermissions",
                }
            },
        )

        result = BaseClaudeCodeAgent._extract_claudecode_tool_settings(
            None,  # type: ignore[arg-type]
            config,
        )
        assert result is not None
        assert result.get("permission_mode") == "bypassPermissions"

    def test_extract_claudecode_tool_settings_working_directory(self) -> None:
        """CC-043: _extract_claudecode_tool_settings extracts working_directory."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        config = MemberAgentConfig(
            name="tool-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
            tool_settings={  # type: ignore[arg-type]
                "claudecode": {
                    "working_directory": "/tmp/workdir",
                }
            },
        )

        result = BaseClaudeCodeAgent._extract_claudecode_tool_settings(
            None,  # type: ignore[arg-type]
            config,
        )
        assert result is not None
        assert result.get("working_directory") == "/tmp/workdir"

    def test_extract_claudecode_tool_settings_max_turns(self) -> None:
        """_extract_claudecode_tool_settings extracts max_turns."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        config = MemberAgentConfig(
            name="tool-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
            tool_settings={  # type: ignore[arg-type]
                "claudecode": {
                    "max_turns": 5,
                }
            },
        )

        result = BaseClaudeCodeAgent._extract_claudecode_tool_settings(
            None,  # type: ignore[arg-type]
            config,
        )
        assert result is not None
        assert result.get("max_turns") == 5

    def test_extract_claudecode_tool_settings_all_combined(self) -> None:
        """All tool_settings.claudecode options work together."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        config = MemberAgentConfig(
            name="tool-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
            tool_settings={  # type: ignore[arg-type]
                "claudecode": {
                    "allowed_tools": ["Read", "Glob"],
                    "disallowed_tools": ["Write"],
                    "permission_mode": "bypassPermissions",
                    "working_directory": "/tmp",
                    "max_turns": 10,
                }
            },
        )

        result = BaseClaudeCodeAgent._extract_claudecode_tool_settings(
            None,  # type: ignore[arg-type]
            config,
        )
        assert result is not None
        assert result.get("allowed_tools") == ["Read", "Glob"]
        assert result.get("disallowed_tools") == ["Write"]
        assert result.get("permission_mode") == "bypassPermissions"
        assert result.get("working_directory") == "/tmp"
        assert result.get("max_turns") == 10

    def test_extract_claudecode_tool_settings_none_when_no_section(self) -> None:
        """Returns None when tool_settings is None."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        config = MemberAgentConfig(
            name="tool-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
            tool_settings=None,
        )

        result = BaseClaudeCodeAgent._extract_claudecode_tool_settings(
            None,  # type: ignore[arg-type]
            config,
        )
        assert result is None

    def test_extract_claudecode_tool_settings_none_when_no_claudecode_key(
        self,
    ) -> None:
        """Returns None when tool_settings has no claudecode key."""
        from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent

        config = MemberAgentConfig(
            name="tool-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
            tool_settings={"other_provider": {"setting": "value"}},  # type: ignore[arg-type]
        )

        result = BaseClaudeCodeAgent._extract_claudecode_tool_settings(
            None,  # type: ignore[arg-type]
            config,
        )
        assert result is None

    def test_tool_settings_without_claudecode_section(self) -> None:
        """Agent should work without tool_settings.claudecode section."""
        from mixseek_plus.agents.claudecode_agent import ClaudeCodePlainAgent

        config = MemberAgentConfig(
            name="tool-agent",
            type="custom",
            model="claudecode:claude-sonnet-4-5",
            system_instruction="You are a helpful assistant.",
            tool_settings=None,
        )

        # Should not raise
        agent = ClaudeCodePlainAgent(config)
        assert agent is not None


class TestCreateClaudeCodeModelWithToolSettings:
    """Tests for create_claudecode_model with tool_settings."""

    def test_create_claudecode_model_passes_allowed_tools(self) -> None:
        """CC-040: create_claudecode_model passes allowed_tools to FixedTokenClaudeCodeModel."""
        from unittest.mock import MagicMock, patch

        from mixseek_plus.providers.claudecode import (
            ClaudeCodeToolSettings,
            create_claudecode_model,
        )

        tool_settings: ClaudeCodeToolSettings = {
            "allowed_tools": ["Read", "Glob"],
        }

        with patch(
            "mixseek_plus.providers.claudecode.FixedTokenClaudeCodeModel"
        ) as mock_model:
            mock_model.return_value = MagicMock()
            create_claudecode_model("claude-sonnet-4-5", tool_settings=tool_settings)

            mock_model.assert_called_once()
            call_kwargs = mock_model.call_args[1]
            assert call_kwargs.get("allowed_tools") == ["Read", "Glob"]

    def test_create_claudecode_model_passes_all_settings(self) -> None:
        """create_claudecode_model passes all tool settings to FixedTokenClaudeCodeModel."""
        from unittest.mock import MagicMock, patch

        from mixseek_plus.providers.claudecode import (
            ClaudeCodeToolSettings,
            create_claudecode_model,
        )

        tool_settings: ClaudeCodeToolSettings = {
            "allowed_tools": ["Read"],
            "disallowed_tools": ["Write"],
            "permission_mode": "bypassPermissions",
            "working_directory": "/tmp",
            "max_turns": 5,
        }

        with patch(
            "mixseek_plus.providers.claudecode.FixedTokenClaudeCodeModel"
        ) as mock_model:
            mock_model.return_value = MagicMock()
            create_claudecode_model("claude-sonnet-4-5", tool_settings=tool_settings)

            mock_model.assert_called_once()
            call_kwargs = mock_model.call_args[1]
            assert call_kwargs.get("allowed_tools") == ["Read"]
            assert call_kwargs.get("disallowed_tools") == ["Write"]
            assert call_kwargs.get("permission_mode") == "bypassPermissions"
            assert call_kwargs.get("working_directory") == "/tmp"
            assert call_kwargs.get("max_turns") == 5

    def test_create_claudecode_model_without_tool_settings(self) -> None:
        """create_claudecode_model works without tool_settings."""
        from unittest.mock import MagicMock, patch

        from mixseek_plus.providers.claudecode import create_claudecode_model

        with patch(
            "mixseek_plus.providers.claudecode.FixedTokenClaudeCodeModel"
        ) as mock_model:
            mock_model.return_value = MagicMock()
            create_claudecode_model("claude-sonnet-4-5")

            mock_model.assert_called_once_with(model_name="claude-sonnet-4-5")
