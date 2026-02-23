"""ClaudeCodeToolsetMixin - ClaudeCodeモデル用ツール登録の共通パターン.

このモジュールは、ClaudeCodeモデルを使用するエージェントで共通のツール登録ロジックを
提供するMixinクラスを定義します。
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Protocol

from pydantic_ai.models import Model

if TYPE_CHECKING:
    from pydantic_ai import Agent

    from mixseek_plus.utils.verbose import ToolLike

logger = logging.getLogger(__name__)


class ClaudeCodeToolsetProtocol(Protocol):
    """ClaudeCodeToolsetMixinが必要とするプロトコル.

    このプロトコルを実装するクラスは、ClaudeCodeモデルと
    pydantic-aiエージェントを持つ必要があります。
    """

    @property
    def _model(self) -> Model: ...

    @property
    def _agent(self) -> Agent[object, str] | None: ...

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

        Raises:
            Exception: ツール登録処理中に予期しないエラーが発生した場合
                (ImportErrorはclaudecode_modelが未インストールの場合のみ抑制)
        """
        # Step 1: Import claudecode_model (may raise ImportError if not installed)
        try:
            from claudecode_model import ClaudeCodeModel
            from claudecode_model.mcp_integration import MCP_SERVER_NAME
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
            return

        # Step 2: Get model and agent from base class (these should not raise)
        model = getattr(self, "_model", None)
        agent = getattr(self, "_agent", None)

        # Early return with debug logging for various skip conditions
        if model is None:
            logger.debug("_model is None, skipping ClaudeCode toolset registration.")
            return

        if not isinstance(model, ClaudeCodeModel):
            logger.debug(
                "Model is not ClaudeCodeModel (type: %s), skipping toolset registration.",
                type(model).__name__,
            )
            return

        if agent is None:
            logger.debug("_agent is None, skipping ClaudeCode toolset registration.")
            return

        # Step 3: Register toolsets (may raise various exceptions)
        toolset = getattr(agent, "_function_toolset", None)
        if toolset is None:
            logger.debug(
                "_function_toolset not found on agent, skipping toolset registration."
            )
            return

        tools = list(toolset.tools.values())
        if not tools:
            logger.debug("No tools found in toolset, skipping toolset registration.")
            return

        # ツールをラップ（各サブクラスの実装を使用）
        # この処理は例外を発生させる可能性があるため、呼び出し元に伝播させる
        wrapped_tools = [self._wrap_tool_for_mcp_impl(tool) for tool in tools]
        model.set_agent_toolsets(wrapped_tools)  # type: ignore[arg-type]

        # MCPツール名をallowed_toolsに追加
        # MCP tools are named: mcp__<server_name>__<tool_name>
        mcp_tool_names = [f"mcp__{MCP_SERVER_NAME}__{tool.name}" for tool in tools]

        # モデルのallowed_toolsを更新
        # allowed_tools=None は「全ツール利用可能（制限なし）」を意味する。
        # MCP ツールは --mcp-config 経由で登録されるため、
        # allowed_tools に明示追加しなくても利用可能。
        # None を上書きすると Bash/Read 等の標準ツールがブロックされる (Issue #58)。
        if model._allowed_tools is not None:
            # 既存のホワイトリストを MCP ツール名で拡張
            model._allowed_tools = list(set(model._allowed_tools) | set(mcp_tool_names))

        logger.debug(
            "Registered %d tools with ClaudeCodeModel: %s",
            len(tools),
            [tool.name for tool in tools],
        )
