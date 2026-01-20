# Issue #33: 実装計画

## 選定アプローチ: プラグマティックバランス

**原則**:
- 既存パターンとの整合性を維持
- 短期対応で即効性を確保
- 中期対応で構造化・拡張性を確保
- 過剰な抽象化を避ける

## アーキテクチャ概要

```
┌───────────────────────────────────────────────────────────────┐
│ Layer 1: 短期 - 即時ログ出力                                   │
│ ├── core_patch.py: _wrap_tool_function_for_mcp() 内でログ      │
│ └── playwright_markdown_fetch_agent.py: _wrap_tool_for_mcp()  │
│     - 実行時間測定 (time.perf_counter())                       │
│     - MIXSEEK_VERBOSE環境変数で制御                            │
│     - 基本情報: tool_name, args_summary, status, time_ms      │
└───────────────────────────────────────────────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────┐
│ Layer 2: 中期 - メッセージ履歴からの抽出                       │
│ ├── utils/claudecode_logging.py (新規)                        │
│ │   └── ClaudeCodeToolCallExtractor                           │
│ │       - extract_tool_calls(messages)                        │
│ │       - _summarize_args(), _match_tool_return()             │
│ └── base_claudecode_agent.py                                  │
│     └── _log_tool_calls(), _is_verbose_mode()                 │
└───────────────────────────────────────────────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────┐
│ Layer 3: 中期 - Logfire統合 (オプショナル)                     │
│ └── observability/logfire_integration.py (新規)               │
│     └── setup_logfire_instrumentation()                       │
│         - pydantic-ai自動インストルメンテーション               │
│         - MIXSEEK_LOGFIRE環境変数で制御                        │
└───────────────────────────────────────────────────────────────┘
```

## ファイル別変更内容

### 変更ファイル

#### 1. `src/mixseek_plus/core_patch.py`

**変更内容**:
- `_wrap_tool_function_for_mcp()`にログ出力追加
- `_summarize_tool_args()`新規関数追加
- 実行時間測定 (`time.perf_counter()`)
- `MIXSEEK_VERBOSE`環境変数チェック

**変更箇所**: `_wrap_tool_function_for_mcp()` 関数 (line 637-695)

```python
async def wrapped(**kwargs: object) -> str:
    start_time = time.perf_counter()
    tool_name = ...

    # ログ: 開始
    if _is_verbose_mode():
        logger.info(
            "[MCP Tool Start] %s: %s",
            tool_name,
            _summarize_tool_args(kwargs),
        )

    try:
        result = await original_func(mock_ctx, **kwargs)

        # ログ: 成功
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        if _is_verbose_mode():
            logger.info(
                "[MCP Tool Done] %s: success in %dms",
                tool_name,
                elapsed_ms,
            )

        return result
    except Exception as e:
        # ログ: エラー
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(
            "[MCP Tool Error] %s: %s in %dms",
            tool_name,
            str(e),
            elapsed_ms,
        )
        raise
```

#### 2. `src/mixseek_plus/agents/playwright_markdown_fetch_agent.py`

**変更内容**:
- `_wrap_tool_for_mcp()`にログ出力追加
- `core_patch.py`と同様のパターン

**変更箇所**: `_wrap_tool_for_mcp()` メソッド (line 182-238)

#### 3. `src/mixseek_plus/agents/base_claudecode_agent.py`

**変更内容**:
- `_log_tool_calls()`メソッド追加
- `_is_verbose_mode()`メソッド追加
- `execute()`メソッドで`_log_tool_calls()`呼び出し

**変更箇所**: `BaseClaudeCodeAgent`クラス

```python
def _log_tool_calls(
    self, execution_id: str, messages: list[ModelMessage]
) -> None:
    """ClaudeCodeModelのツール呼び出しをログ出力."""
    from mixseek_plus.utils.claudecode_logging import ClaudeCodeToolCallExtractor

    tool_calls = ClaudeCodeToolCallExtractor.extract_tool_calls(messages)

    for call in tool_calls:
        self.logger.log_tool_invocation(
            execution_id=execution_id,
            tool_name=call["tool_name"],
            parameters={"summary": call["args_summary"]},
            execution_time_ms=0,  # メッセージ履歴からは取得不可
            status=call.get("status", "unknown"),
        )

def _is_verbose_mode(self) -> bool:
    """verboseモードが有効かチェック."""
    import os
    return os.getenv("MIXSEEK_VERBOSE", "").lower() in ("1", "true")
```

### 新規作成ファイル

#### 4. `src/mixseek_plus/utils/claudecode_logging.py`

**責務**: メッセージ履歴からツール呼び出しを抽出

```python
"""ClaudeCodeModel固有のロギングユーティリティ."""

from __future__ import annotations

import logging
from typing import Any

from pydantic_ai.messages import (
    ModelMessage,
    ToolCallPart,
    ToolReturnPart,
)

logger = logging.getLogger(__name__)


class ClaudeCodeToolCallExtractor:
    """ClaudeCodeModelのメッセージ履歴からツール呼び出しを抽出."""

    @staticmethod
    def extract_tool_calls(
        messages: list[ModelMessage],
    ) -> list[dict[str, Any]]:
        """メッセージ履歴からツール呼び出し情報を抽出.

        Args:
            messages: pydantic-ai の all_messages() からの出力

        Returns:
            ツール呼び出し情報のリスト:
            - tool_name: str
            - args_summary: str (引数の概要)
            - status: 'success' | 'error'
            - result_summary: str | None
        """
        tool_calls: list[dict[str, Any]] = []

        for msg in messages:
            if hasattr(msg, "parts"):
                for part in msg.parts:
                    if isinstance(part, ToolCallPart):
                        tool_info = {
                            "tool_name": part.tool_name,
                            "args_summary": _summarize_args(part.args),
                            "tool_call_id": part.tool_call_id,
                        }
                        tool_calls.append(tool_info)

            if hasattr(msg, "parts"):
                for part in msg.parts:
                    if isinstance(part, ToolReturnPart):
                        _match_tool_return(tool_calls, part)

        return tool_calls


def _summarize_args(args: dict[str, Any]) -> str:
    """ツール引数を要約."""
    summary_parts = []
    for key, value in args.items():
        if isinstance(value, str) and len(value) > 100:
            summary_parts.append(f"{key}={value[:100]}...")
        else:
            summary_parts.append(f"{key}={value}")
    return ", ".join(summary_parts)


def _match_tool_return(
    tool_calls: list[dict[str, Any]], return_part: ToolReturnPart
) -> None:
    """ToolReturnPartを対応するツール呼び出しにマッチング."""
    for call in tool_calls:
        if call.get("tool_call_id") == return_part.tool_call_id:
            call["status"] = "success"
            call["result_summary"] = _summarize_result(return_part.content)
            return


def _summarize_result(content: str) -> str:
    """ツール結果を要約."""
    if len(content) > 200:
        return content[:200] + "..."
    return content
```

#### 5. `src/mixseek_plus/observability/__init__.py`

```python
"""Observability module for mixseek-plus."""

from mixseek_plus.observability.logfire_integration import (
    setup_logfire_instrumentation,
    is_logfire_enabled,
)

__all__ = [
    "setup_logfire_instrumentation",
    "is_logfire_enabled",
]
```

#### 6. `src/mixseek_plus/observability/logfire_integration.py`

**責務**: オプショナルLogfire統合

```python
"""Logfire統合モジュール (オプショナル)."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic_ai import Agent

logger = logging.getLogger(__name__)


def is_logfire_enabled() -> bool:
    """Logfireが有効かチェック."""
    return os.getenv("MIXSEEK_LOGFIRE", "").lower() in ("1", "true")


def setup_logfire_instrumentation(
    agent: Agent | None = None,
) -> None:
    """Logfireインストルメンテーションをセットアップ.

    Args:
        agent: pydantic-ai Agent (指定された場合、エージェント固有の設定)

    Note:
        - logfireパッケージがインストールされている場合のみ有効
        - MIXSEEK_LOGFIRE環境変数が設定されている必要あり
    """
    if not is_logfire_enabled():
        logger.debug("Logfire is disabled (MIXSEEK_LOGFIRE not set)")
        return

    try:
        import logfire
    except ImportError:
        logger.warning(
            "logfireパッケージがインストールされていません。"
            "pip install 'mixseek-plus[logfire]' でインストールしてください。"
        )
        return

    try:
        logfire.configure()
    except Exception as e:
        logger.warning("Logfireの初期化に失敗しました: %s", e)
        return

    logfire.instrument_pydantic_ai()

    logger.info("Logfireインストルメンテーションを有効化しました")
```

### テストファイル

#### 7. `tests/unit/test_claudecode_logging.py`

```python
"""ClaudeCodeToolCallExtractorのテスト."""

import pytest

from mixseek_plus.utils.claudecode_logging import (
    ClaudeCodeToolCallExtractor,
    _summarize_args,
    _summarize_result,
)


class TestClaudeCodeToolCallExtractor:
    """ClaudeCodeToolCallExtractorのテストクラス."""

    def test_extract_single_tool_call(self):
        """単一ツール呼び出しの抽出."""
        # TODO: pydantic-aiのメッセージオブジェクトをモック
        pass

    def test_extract_multiple_tool_calls(self):
        """複数ツール呼び出しの抽出."""
        pass

    def test_match_tool_return_to_call(self):
        """ToolReturnPartとToolCallPartのマッチング."""
        pass


class TestSummarizeArgs:
    """_summarize_argsのテストクラス."""

    def test_short_args(self):
        """短い引数はそのまま."""
        result = _summarize_args({"url": "https://example.com"})
        assert result == "url=https://example.com"

    def test_long_args_truncated(self):
        """長い引数は切り詰め."""
        long_value = "x" * 200
        result = _summarize_args({"content": long_value})
        assert len(result) < 200
        assert "..." in result


class TestSummarizeResult:
    """_summarize_resultのテストクラス."""

    def test_short_result(self):
        """短い結果はそのまま."""
        result = _summarize_result("OK")
        assert result == "OK"

    def test_long_result_truncated(self):
        """長い結果は切り詰め."""
        long_result = "x" * 300
        result = _summarize_result(long_result)
        assert len(result) <= 203  # 200 + "..."
        assert "..." in result
```

#### 8. `tests/unit/test_logfire_integration.py`

```python
"""Logfire統合のテスト."""

import os
from unittest.mock import patch

import pytest

from mixseek_plus.observability.logfire_integration import (
    is_logfire_enabled,
    setup_logfire_instrumentation,
)


class TestIsLogfireEnabled:
    """is_logfire_enabledのテストクラス."""

    def test_disabled_by_default(self):
        """デフォルトで無効."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_logfire_enabled() is False

    def test_enabled_with_env_var(self):
        """環境変数で有効化."""
        with patch.dict(os.environ, {"MIXSEEK_LOGFIRE": "1"}):
            assert is_logfire_enabled() is True

    def test_enabled_with_true(self):
        """環境変数trueで有効化."""
        with patch.dict(os.environ, {"MIXSEEK_LOGFIRE": "true"}):
            assert is_logfire_enabled() is True


class TestSetupLogfireInstrumentation:
    """setup_logfire_instrumentationのテストクラス."""

    def test_skipped_when_disabled(self):
        """無効時はスキップ."""
        with patch.dict(os.environ, {}, clear=True):
            # エラーなく完了することを確認
            setup_logfire_instrumentation()

    @pytest.mark.skipif(
        "logfire" not in __import__("sys").modules,
        reason="logfire not installed",
    )
    def test_configures_logfire_when_enabled(self):
        """有効時はLogfireを設定."""
        # TODO: logfireのモックを使用したテスト
        pass
```

## 実装順序

### Phase 1: 短期対応（即効性）

1. **Task 1.1**: `core_patch.py`にログ追加
   - `_is_verbose_mode()`関数追加
   - `_summarize_tool_args()`関数追加
   - `_wrap_tool_function_for_mcp()`にログ追加

2. **Task 1.2**: `playwright_markdown_fetch_agent.py`にログ追加
   - 同様のパターンを適用

### Phase 2: 中期対応（メッセージ抽出）

3. **Task 2.1**: `utils/claudecode_logging.py`作成
   - `ClaudeCodeToolCallExtractor`クラス実装
   - ヘルパー関数実装

4. **Task 2.2**: `base_claudecode_agent.py`拡張
   - `_log_tool_calls()`メソッド追加
   - `execute()`メソッド修正

5. **Task 2.3**: テスト作成
   - `test_claudecode_logging.py`

### Phase 3: 中期対応（Logfire）

6. **Task 3.1**: `observability/`パッケージ作成
   - `__init__.py`
   - `logfire_integration.py`

7. **Task 3.2**: テスト作成
   - `test_logfire_integration.py`

## 注意事項

### 既存コードとの整合性

- mixseek-coreの`MemberAgentLogger`を活用
- 既存の`log_tool_invocation()`メソッドを使用
- ログフォーマットは既存パターンに従う

### パフォーマンス考慮

- `MIXSEEK_VERBOSE=false`の場合、ログ出力はスキップ
- 引数/結果のサマライズで大量データを避ける

### セキュリティ

- 機密情報（APIキー、トークン）はログに含めない
- `_summarize_args()`でマスキングを検討

## 関連

- Issue #31: PlaywrightMarkdownFetchAgent実装
- Issue #23: MCPツール統合
- claudecode-model パッケージ
