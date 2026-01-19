"""BaseClaudeCodeAgentベースクラスの単体テスト.

CC-031, CC-061の検証
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

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


class TestBaseClaudeCodeAgentWorkspace:
    """Tests for workspace and preset resolution in BaseClaudeCodeAgent."""

    def test_get_workspace_returns_path_when_env_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_get_workspace returns Path when MIXSEEK_WORKSPACE is set."""
        from mixseek_plus.agents.base_claudecode_agent import (
            WORKSPACE_ENV_VAR,
            BaseClaudeCodeAgent,
        )

        monkeypatch.setenv(WORKSPACE_ENV_VAR, str(tmp_path))

        # Create a concrete subclass for testing
        class ConcreteAgent(BaseClaudeCodeAgent):
            def _get_agent(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _create_deps(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _get_agent_type_metadata(self) -> dict[str, str]:
                return {}

        # Mock the init to avoid model creation
        with patch.object(ConcreteAgent, "__init__", lambda self, config: None):
            agent = ConcreteAgent.__new__(ConcreteAgent)
            result = agent._get_workspace()
            assert result == tmp_path

    def test_get_workspace_returns_none_when_env_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_get_workspace returns None when MIXSEEK_WORKSPACE is not set."""
        from mixseek_plus.agents.base_claudecode_agent import (
            WORKSPACE_ENV_VAR,
            BaseClaudeCodeAgent,
        )

        monkeypatch.delenv(WORKSPACE_ENV_VAR, raising=False)

        class ConcreteAgent(BaseClaudeCodeAgent):
            def _get_agent(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _create_deps(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _get_agent_type_metadata(self) -> dict[str, str]:
                return {}

        with patch.object(ConcreteAgent, "__init__", lambda self, config: None):
            agent = ConcreteAgent.__new__(ConcreteAgent)
            result = agent._get_workspace()
            assert result is None

    def test_get_workspace_returns_none_when_dir_not_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_get_workspace returns None when directory doesn't exist."""
        from mixseek_plus.agents.base_claudecode_agent import (
            WORKSPACE_ENV_VAR,
            BaseClaudeCodeAgent,
        )

        non_existent = tmp_path / "non_existent"
        monkeypatch.setenv(WORKSPACE_ENV_VAR, str(non_existent))

        class ConcreteAgent(BaseClaudeCodeAgent):
            def _get_agent(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _create_deps(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _get_agent_type_metadata(self) -> dict[str, str]:
                return {}

        with patch.object(ConcreteAgent, "__init__", lambda self, config: None):
            agent = ConcreteAgent.__new__(ConcreteAgent)
            result = agent._get_workspace()
            assert result is None

    def test_resolve_preset_if_needed_returns_original_when_no_preset(self) -> None:
        """_resolve_preset_if_needed returns original settings when no preset."""
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
            settings = {"permission_mode": "bypassPermissions", "max_turns": 50}
            result = agent._resolve_preset_if_needed(settings)  # type: ignore[arg-type]
            assert result == settings

    def test_resolve_preset_if_needed_resolves_preset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_resolve_preset_if_needed resolves preset when workspace available."""
        from mixseek_plus.agents.base_claudecode_agent import (
            WORKSPACE_ENV_VAR,
            BaseClaudeCodeAgent,
        )

        # Create preset file
        preset_dir = tmp_path / "configs" / "presets"
        preset_dir.mkdir(parents=True)
        preset_file = preset_dir / "claudecode.toml"
        preset_file.write_text("""
[delegate_only]
permission_mode = "bypassPermissions"
disallowed_tools = ["Bash", "Write", "Edit"]
""")

        monkeypatch.setenv(WORKSPACE_ENV_VAR, str(tmp_path))

        class ConcreteAgent(BaseClaudeCodeAgent):
            def _get_agent(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _create_deps(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _get_agent_type_metadata(self) -> dict[str, str]:
                return {}

        with patch.object(ConcreteAgent, "__init__", lambda self, config: None):
            agent = ConcreteAgent.__new__(ConcreteAgent)
            # Mock config with name property
            mock_config = MagicMock()
            mock_config.name = "test-agent"
            agent.config = mock_config

            settings = {"preset": "delegate_only", "max_turns": 100}
            result = agent._resolve_preset_if_needed(settings)  # type: ignore[arg-type]

            # Preset values
            assert result.get("permission_mode") == "bypassPermissions"
            assert result.get("disallowed_tools") == ["Bash", "Write", "Edit"]
            # Local override
            assert result.get("max_turns") == 100
            # Preset key removed
            assert "preset" not in result

    def test_resolve_preset_if_needed_skips_when_no_workspace(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_resolve_preset_if_needed skips preset when workspace not available."""
        from mixseek_plus.agents.base_claudecode_agent import (
            WORKSPACE_ENV_VAR,
            BaseClaudeCodeAgent,
        )

        monkeypatch.delenv(WORKSPACE_ENV_VAR, raising=False)

        class ConcreteAgent(BaseClaudeCodeAgent):
            def _get_agent(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _create_deps(self):  # type: ignore[no-untyped-def]
                return MagicMock()

            def _get_agent_type_metadata(self) -> dict[str, str]:
                return {}

        with patch.object(ConcreteAgent, "__init__", lambda self, config: None):
            agent = ConcreteAgent.__new__(ConcreteAgent)
            # Mock config with name property
            mock_config = MagicMock()
            mock_config.name = "test-agent"
            agent.config = mock_config

            settings = {"preset": "delegate_only", "max_turns": 100}
            result = agent._resolve_preset_if_needed(settings)  # type: ignore[arg-type]

            # Only local settings (preset ignored)
            assert result.get("max_turns") == 100
            # Preset key removed
            assert "preset" not in result
            # Preset settings not applied
            assert "permission_mode" not in result
