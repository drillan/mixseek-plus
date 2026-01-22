"""ClaudeCodeToolsetMixin のユニットテスト.

このモジュールは ClaudeCodeToolsetMixin の動作を検証するテストを提供します。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from mixseek_plus.utils.verbose import ToolLike


@dataclass
class MockTool:
    """テスト用のToolモック."""

    name: str
    description: str | None
    function: object


class TestClaudeCodeToolsetProtocol:
    """ClaudeCodeToolsetProtocol のテスト."""

    def test_protocol_exists(self) -> None:
        """Protocol クラスが存在することを確認."""
        from mixseek_plus.agents.mixins.claudecode_toolset import (
            ClaudeCodeToolsetProtocol,
        )

        assert ClaudeCodeToolsetProtocol is not None

    def test_protocol_has_required_properties(self) -> None:
        """Protocol が必要なプロパティを定義していることを確認."""
        from mixseek_plus.agents.mixins.claudecode_toolset import (
            ClaudeCodeToolsetProtocol,
        )

        # Protocol のメソッド/プロパティを確認
        assert hasattr(ClaudeCodeToolsetProtocol, "_model")
        assert hasattr(ClaudeCodeToolsetProtocol, "_agent")

    def test_protocol_has_wrap_method(self) -> None:
        """Protocol が _wrap_tool_for_mcp_impl メソッドを定義していることを確認."""
        from mixseek_plus.agents.mixins.claudecode_toolset import (
            ClaudeCodeToolsetProtocol,
        )

        assert hasattr(ClaudeCodeToolsetProtocol, "_wrap_tool_for_mcp_impl")


class TestClaudeCodeToolsetMixin:
    """ClaudeCodeToolsetMixin のテスト."""

    def test_mixin_exists(self) -> None:
        """Mixin クラスが存在することを確認."""
        from mixseek_plus.agents.mixins.claudecode_toolset import (
            ClaudeCodeToolsetMixin,
        )

        assert ClaudeCodeToolsetMixin is not None

    def test_mixin_has_abstract_method(self) -> None:
        """Mixin が抽象メソッドを持つことを確認."""
        from mixseek_plus.agents.mixins.claudecode_toolset import (
            ClaudeCodeToolsetMixin,
        )

        assert hasattr(ClaudeCodeToolsetMixin, "_wrap_tool_for_mcp_impl")

    def test_mixin_has_register_method(self) -> None:
        """Mixin が _register_toolsets_if_claudecode メソッドを持つことを確認."""
        from mixseek_plus.agents.mixins.claudecode_toolset import (
            ClaudeCodeToolsetMixin,
        )

        assert hasattr(ClaudeCodeToolsetMixin, "_register_toolsets_if_claudecode")


class TestRegisterToolsetsIfClaudecode:
    """_register_toolsets_if_claudecode メソッドのテスト."""

    def _create_concrete_mixin(self) -> type:
        """テスト用の具体的なMixin実装を作成."""
        from mixseek_plus.agents.mixins.claudecode_toolset import (
            ClaudeCodeToolsetMixin,
        )

        class ConcreteMixin(ClaudeCodeToolsetMixin):
            def __init__(self) -> None:
                self._model: object = None
                self._agent: object = None
                self.wrapped_tools: list[ToolLike] = []

            def _wrap_tool_for_mcp_impl(self, tool: ToolLike) -> ToolLike:
                self.wrapped_tools.append(tool)
                return tool

        return ConcreteMixin

    def test_skips_when_model_is_none(self) -> None:
        """_model が None の場合にスキップすることを確認."""
        ConcreteMixin = self._create_concrete_mixin()
        instance = ConcreteMixin()
        instance._model = None
        instance._agent = MagicMock()

        # Should not raise
        instance._register_toolsets_if_claudecode()

    def test_skips_when_agent_is_none(self) -> None:
        """_agent が None の場合にスキップすることを確認."""
        ConcreteMixin = self._create_concrete_mixin()
        instance = ConcreteMixin()
        instance._model = MagicMock()
        instance._agent = None

        # Should not raise
        instance._register_toolsets_if_claudecode()

    def test_skips_when_model_is_not_claudecode(self) -> None:
        """モデルが ClaudeCodeModel でない場合にスキップすることを確認."""
        ConcreteMixin = self._create_concrete_mixin()
        instance = ConcreteMixin()
        instance._model = MagicMock()  # Not ClaudeCodeModel
        instance._agent = MagicMock()

        # Should not raise
        instance._register_toolsets_if_claudecode()

    def test_skips_when_toolset_is_none(self) -> None:
        """_function_toolset が None の場合にスキップすることを確認."""
        ConcreteMixin = self._create_concrete_mixin()
        instance = ConcreteMixin()

        # Mock ClaudeCodeModel
        with patch(
            "mixseek_plus.agents.mixins.claudecode_toolset.ClaudeCodeModel",
            create=True,
        ) as MockClaudeCodeModel:
            mock_model = MagicMock()
            MockClaudeCodeModel.return_value = mock_model
            instance._model = mock_model

            mock_agent = MagicMock()
            mock_agent._function_toolset = None
            instance._agent = mock_agent

            # Should not raise
            instance._register_toolsets_if_claudecode()

    def test_skips_when_tools_empty(self) -> None:
        """ツールが空の場合にスキップすることを確認."""
        ConcreteMixin = self._create_concrete_mixin()
        instance = ConcreteMixin()

        with patch(
            "mixseek_plus.agents.mixins.claudecode_toolset.ClaudeCodeModel",
            create=True,
        ) as MockClaudeCodeModel:
            mock_model = MagicMock()
            MockClaudeCodeModel.return_value = mock_model
            instance._model = mock_model

            mock_toolset = MagicMock()
            mock_toolset.tools = {}
            mock_agent = MagicMock()
            mock_agent._function_toolset = mock_toolset
            instance._agent = mock_agent

            # Should not raise
            instance._register_toolsets_if_claudecode()

    def test_handles_import_error_gracefully(self) -> None:
        """claudecode_model が未インストールの場合にエラーを抑制することを確認."""
        ConcreteMixin = self._create_concrete_mixin()
        instance = ConcreteMixin()
        instance._model = MagicMock()
        instance._agent = MagicMock()

        # Mock import to raise ImportError
        with patch.dict(
            "sys.modules",
            {"claudecode_model": None, "claudecode_model.mcp_integration": None},
        ):
            with patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'claudecode_model'"),
            ):
                # Should not raise
                instance._register_toolsets_if_claudecode()

    @pytest.mark.asyncio
    async def test_registers_tools_with_claudecode_model(self) -> None:
        """ClaudeCodeModel にツールが正しく登録されることを確認."""
        from claudecode_model import ClaudeCodeModel

        ConcreteMixin = self._create_concrete_mixin()
        instance = ConcreteMixin()

        # Create mock ClaudeCodeModel
        mock_model = MagicMock(spec=ClaudeCodeModel)
        mock_model._allowed_tools = None
        instance._model = mock_model

        # Create mock agent with tools
        mock_tool = MockTool(
            name="test_tool", description="Test", function=lambda: None
        )
        mock_toolset = MagicMock()
        mock_toolset.tools = {"test_tool": mock_tool}
        mock_agent = MagicMock()
        mock_agent._function_toolset = mock_toolset
        instance._agent = mock_agent

        # Register toolsets
        instance._register_toolsets_if_claudecode()

        # Verify set_agent_toolsets was called
        mock_model.set_agent_toolsets.assert_called_once()

        # Verify allowed_tools was updated
        assert mock_model._allowed_tools is not None
        assert "mcp__pydantic_tools__test_tool" in mock_model._allowed_tools

    @pytest.mark.asyncio
    async def test_extends_existing_allowed_tools(self) -> None:
        """既存の allowed_tools に追加することを確認."""
        from claudecode_model import ClaudeCodeModel

        ConcreteMixin = self._create_concrete_mixin()
        instance = ConcreteMixin()

        # Create mock ClaudeCodeModel with existing allowed_tools
        mock_model = MagicMock(spec=ClaudeCodeModel)
        mock_model._allowed_tools = ["existing_tool"]
        instance._model = mock_model

        # Create mock agent with tools
        mock_tool = MockTool(name="new_tool", description="Test", function=lambda: None)
        mock_toolset = MagicMock()
        mock_toolset.tools = {"new_tool": mock_tool}
        mock_agent = MagicMock()
        mock_agent._function_toolset = mock_toolset
        instance._agent = mock_agent

        # Register toolsets
        instance._register_toolsets_if_claudecode()

        # Verify allowed_tools includes both existing and new
        assert "existing_tool" in mock_model._allowed_tools
        assert "mcp__pydantic_tools__new_tool" in mock_model._allowed_tools

    def test_propagates_wrap_tool_exception(self) -> None:
        """_wrap_tool_for_mcp_impl の例外が伝播することを確認."""
        from mixseek_plus.agents.mixins.claudecode_toolset import (
            ClaudeCodeToolsetMixin,
        )

        class FailingMixin(ClaudeCodeToolsetMixin):
            def __init__(self) -> None:
                self._model: object = None
                self._agent: object = None

            def _wrap_tool_for_mcp_impl(self, tool: ToolLike) -> ToolLike:
                raise ValueError("Wrap failed")

        with patch(
            "mixseek_plus.agents.mixins.claudecode_toolset.ClaudeCodeModel",
            create=True,
        ):
            from claudecode_model import ClaudeCodeModel

            instance = FailingMixin()
            mock_model = MagicMock(spec=ClaudeCodeModel)
            mock_model._allowed_tools = None
            instance._model = mock_model

            mock_tool = MockTool(name="test", description="Test", function=lambda: None)
            mock_toolset = MagicMock()
            mock_toolset.tools = {"test": mock_tool}
            mock_agent = MagicMock()
            mock_agent._function_toolset = mock_toolset
            instance._agent = mock_agent

            with pytest.raises(ValueError, match="Wrap failed"):
                instance._register_toolsets_if_claudecode()


class TestMixinExport:
    """Mixin のエクスポートテスト."""

    def test_exported_from_mixins_package(self) -> None:
        """mixins パッケージからエクスポートされていることを確認."""
        from mixseek_plus.agents.mixins import (
            ClaudeCodeToolsetMixin,
            ClaudeCodeToolsetProtocol,
        )

        assert ClaudeCodeToolsetMixin is not None
        assert ClaudeCodeToolsetProtocol is not None
