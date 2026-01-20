# Research: ClaudeCodeModel固有のロギング・オブザーバビリティ

## 調査サマリー

### Decision: CLIオプション追加方法

**結論**: mixseek-core の `exec` コマンドには既に `--verbose` と `--logfire` オプションが存在する。追加実装は不要。

**Rationale**:
- mixseek-core v0.x.x の `/mixseek/cli/commands/exec.py` に既に実装済み
- `setup_logging_from_cli()` と `setup_logfire_from_cli()` で環境設定が行われる
- mixseek-plus は `core_app` を直接再利用しているため、これらのオプションは自動的に利用可能

**Alternatives considered**:
1. ~~CLI wrapper作成~~ - 不要。既存のcore機能で十分
2. ~~Monkey-patching exec_command~~ - 不要。既存のcore機能で十分
3. ~~Typer callback でグローバルオプション~~ - 不要。既存のcore機能で十分

---

## 調査詳細

### 1. mixseek-core CLIの既存実装

#### exec コマンドの現在のシグネチャ

`/mixseek/cli/commands/exec.py` (lines 144-157):

```python
def exec_command(
    user_prompt: str = typer.Argument(..., help="ユーザプロンプト"),
    config: Path = CONFIG_OPTION,
    timeout: int | None = TIMEOUT_OPTION,
    workspace: Path | None = WORKSPACE_OPTION,
    output_format: str = OUTPUT_FORMAT_OPTION,
    verbose: bool = VERBOSE_OPTION,      # ← 既存
    logfire: bool = LOGFIRE_OPTION,       # ← 既存
    logfire_metadata: bool = LOGFIRE_METADATA_OPTION,
    logfire_http: bool = LOGFIRE_HTTP_OPTION,
    log_level: str = LOG_LEVEL_OPTION,
    no_log_console: bool = NO_LOG_CONSOLE_OPTION,
    no_log_FILE: bool = NO_LOG_FILE_OPTION,
) -> None:
```

#### 共通オプション定義

`/mixseek/cli/common_options.py`:

```python
VERBOSE_OPTION = typer.Option(
    False,
    "--verbose",
    "-v",
    help="Verbose output",
)

LOGFIRE_OPTION = typer.Option(
    False,
    "--logfire",
    help="Enable Logfire observability (full mode)",
)
```

#### 環境設定の実行フロー

`exec.py` (lines 195-201):

```python
logfire_enabled = logfire or logfire_metadata or logfire_http
setup_logging_from_cli(
    log_level,
    no_log_console,
    no_log_file,
    logfire_enabled,
    workspace_path,
    verbose
)
setup_logfire_from_cli(logfire, logfire_metadata, logfire_http, workspace_path, verbose)
```

### 2. 仕様要件との整合性

| 仕様要件 | 現状 | 対応必要 |
|---------|------|---------|
| FR-002: `--verbose` オプション | ✅ 既存 | 内部で `MIXSEEK_VERBOSE` 相当の動作確認が必要 |
| FR-003: `--logfire` オプション | ✅ 既存 | 内部で `MIXSEEK_LOGFIRE` 相当の動作確認が必要 |
| FR-007: logfire未インストール時の警告 | ✅ core側で対応済み | 不要 |

### 3. 環境変数との連携

**調査結果**: mixseek-core の `setup_logging_from_cli()` は内部で `verbose` フラグを使用するが、`MIXSEEK_VERBOSE` 環境変数を明示的に設定はしない。

**対応方針**:
1. mixseek-plus内で `_is_verbose_mode()` を実装
2. この関数内で CLI フラグ（コンテキストから取得）または環境変数 `MIXSEEK_VERBOSE` をチェック
3. 後方互換性のため、環境変数でも制御可能にする

### 4. 実装が必要な部分

#### Layer 1: 短期対応（MCP ツールログ出力）

mixseek-core の CLI オプションは存在するが、**MCP ツール呼び出し時の具体的なログ出力ロジック**は mixseek-plus 側で実装が必要：

```
core_patch.py: _wrap_tool_function_for_mcp()
  ├── time.perf_counter() による実行時間計測
  ├── _is_verbose_mode() による条件チェック
  └── MemberAgentLogger.log_tool_invocation() によるログ出力
```

#### Layer 2: 中期対応（メッセージ履歴抽出）

pydantic-ai のメッセージ履歴から ToolCallPart/ToolReturnPart を抽出する実装が必要：

```
utils/claudecode_logging.py:
  └── ClaudeCodeToolCallExtractor.extract_tool_calls()
```

#### Layer 3: 中期対応（Logfire 統合）

Logfire インストルメンテーションのセットアップ：

```
observability/logfire_integration.py:
  └── setup_logfire_instrumentation()
```

### 5. verbose モード判定ロジック

**推奨実装**:

```python
def _is_verbose_mode() -> bool:
    """Check if verbose mode is enabled.

    Checks in order:
    1. MIXSEEK_VERBOSE environment variable
    2. (Future: CLI context if accessible)
    """
    import os
    return os.getenv("MIXSEEK_VERBOSE", "").lower() in ("1", "true")
```

**理由**:
- CLI フラグは `exec_command` 内でのみ直接アクセス可能
- `core_patch.py` の `_wrap_tool_function_for_mcp()` は CLI コンテキスト外で呼ばれる
- 環境変数による制御が最もシンプルかつ汎用的

### 6. MemberAgentLogger の活用

mixseek-core の `MemberAgentLogger` が提供するメソッド：

```python
class MemberAgentLogger:
    def log_tool_invocation(
        self,
        execution_id: str,
        tool_name: str,
        parameters: dict[str, object],  # 自動サニタイズ
        execution_time_ms: int,
        status: str,  # "success" | "error"
    ) -> None: ...
```

**出力形式** (JSON):

```json
{
  "event": "tool_invocation",
  "execution_id": "exec_abc123",
  "tool_name": "mcp__pydantic_tools__fetch_url",
  "parameters": {"url": "https://example.com"},
  "execution_time_ms": 450,
  "status": "success",
  "timestamp": "2026-01-20T12:34:57.100Z"
}
```

---

## 結論

### 必要な実装

1. **CLIオプション追加**: ❌ 不要（既存）
2. **環境変数チェック関数**: ✅ 必要（`_is_verbose_mode()`）
3. **MCP ツールログ出力**: ✅ 必要（`core_patch.py`, `playwright_markdown_fetch_agent.py`）
4. **メッセージ履歴抽出**: ✅ 必要（`utils/claudecode_logging.py`）
5. **Logfire 統合**: ✅ 必要（`observability/logfire_integration.py`）

### 影響を受けるファイル

| ファイル | 変更タイプ | 内容 |
|---------|----------|------|
| `core_patch.py` | 修正 | `_is_verbose_mode()` 追加、ログ出力追加 |
| `playwright_markdown_fetch_agent.py` | 修正 | 同上 |
| `base_claudecode_agent.py` | 修正 | `_log_tool_calls_from_history()` 追加 |
| `utils/claudecode_logging.py` | 新規 | ツール呼び出し抽出クラス |
| `observability/__init__.py` | 新規 | モジュールエクスポート |
| `observability/logfire_integration.py` | 新規 | Logfire セットアップ |
