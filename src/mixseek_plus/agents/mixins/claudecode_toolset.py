"""ClaudeCodeToolsetMixin - ClaudeCodeモデル用ツール登録の共通パターン.

このモジュールは、ClaudeCodeモデルを使用するエージェントで共通のツール登録ロジックを
提供するMixinクラスを定義します。
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from mixseek_plus.utils.verbose import ToolLike

logger = logging.getLogger(__name__)


class ClaudeCodeToolsetProtocol(Protocol):
    """ClaudeCodeToolsetMixinが必要とするプロトコル.

    このプロトコルを実装するクラスは、ClaudeCodeモデルと
    pydantic-aiエージェントを持つ必要があります。
    """

    @property
    def _model(self) -> object: ...

    @property
    def _agent(self) -> object | None: ...

    def _wrap_tool_for_mcp_impl(self, tool: ToolLike) -> ToolLike:
        """pydantic-aiツールをMCP用にラップする."""
        ...


class ClaudeCodeToolsetMixin:
    """ClaudeCodeモデル用ツール登録の共通パターンを提供するMixin.

    このMixinは、ClaudeCodeModelを使用するエージェントで必要な
    ツール登録ロジックを共通化します。

    使用方法:
        1. このMixinを継承
        2. `_wrap_tool_for_mcp_impl`メソッドをオーバーライド
        3. Agentセットアップ後に`_register_toolsets_if_claudecode()`を呼び出し

    Example:
        class MyAgent(ClaudeCodeToolsetMixin, BaseClaudeCodeAgent):
            def _wrap_tool_for_mcp_impl(self, tool: ToolLike) -> ToolLike:
                # カスタムラッピングロジック
                ...

    Note:
        _model, _agent 属性は継承元のベースクラスから提供される想定です。
    """

    @abstractmethod
    def _wrap_tool_for_mcp_impl(self, tool: ToolLike) -> ToolLike:
        """pydantic-aiツールをMCP用にラップする（サブクラスで実装）.

        Args:
            tool: pydantic-ai Toolオブジェクト

        Returns:
            ラップされたToolオブジェクト
        """
        ...

    def _register_toolsets_if_claudecode(self) -> None:
        """ClaudeCodeModelの場合にツールセットを登録.

        ClaudeCodeModelは、Agent作成後にset_agent_toolsets()を介して
        ツール関数を明示的に登録する必要があります。このメソッドは:
        - ツール関数をラップしてコンテキストを注入
        - MCPツール名をallowed_toolsに追加してClaudeが呼び出せるようにする

        MCPツールの命名規則: mcp__<server_name>__<tool_name>
        server_nameは`claudecode_model.mcp_integration.MCP_SERVER_NAME`から取得
        (pydantic-aiツールの場合は'pydantic_tools')。

        Note:
            このメソッドはMixinとして使用され、_modelと_agentは
            継承元のベースクラスから提供される想定です。
        """
        try:
            from claudecode_model import ClaudeCodeModel
            from claudecode_model.mcp_integration import MCP_SERVER_NAME

            # Mixin attributes from base class
            model = getattr(self, "_model", None)
            agent = getattr(self, "_agent", None)

            if isinstance(model, ClaudeCodeModel) and agent is not None:
                # Agentから内部のツールセットにアクセス
                toolset = getattr(agent, "_function_toolset", None)
                if toolset is not None:
                    tools = list(toolset.tools.values())
                    if tools:
                        # ツールをラップ（各サブクラスの実装を使用）
                        wrapped_tools = [
                            self._wrap_tool_for_mcp_impl(tool) for tool in tools
                        ]
                        model.set_agent_toolsets(wrapped_tools)  # type: ignore[arg-type]

                        # MCPツール名をallowed_toolsに追加
                        # MCP tools are named: mcp__<server_name>__<tool_name>
                        mcp_tool_names = [
                            f"mcp__{MCP_SERVER_NAME}__{tool.name}" for tool in tools
                        ]

                        # モデルのallowed_toolsを更新
                        if model._allowed_tools is None:
                            model._allowed_tools = mcp_tool_names
                        else:
                            # 既存のallowed_toolsを拡張
                            model._allowed_tools = list(
                                set(model._allowed_tools) | set(mcp_tool_names)
                            )
        except ImportError as e:
            # claudecode_modelパッケージ自体が見つからない場合のみ抑制
            # 信頼性の高いモジュール検出のためにImportError.name属性を使用
            missing_module = getattr(e, "name", None)
            if missing_module is None or not missing_module.startswith(
                "claudecode_model"
            ):
                # 予期しないインポートエラーは完全なトレースバックでログ出力
                logger.error(
                    "ClaudeCode model import failed unexpectedly: %s",
                    e,
                    exc_info=True,
                )
            else:
                # claudecode_modelがインストールされていない - 一部の環境では想定内
                logger.debug(
                    "claudecode_model パッケージが利用できないため、"
                    "ツールの ClaudeCodeModel への登録をスキップしました。"
                )
