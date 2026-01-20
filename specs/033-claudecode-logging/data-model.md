# Data Model: ClaudeCodeModel固有のロギング・オブザーバビリティ

## エンティティ概要

本機能では新規のデータモデル（永続化エンティティ）は作成しない。代わりに、既存の `MemberAgentLogger.log_tool_invocation()` のログフォーマットに準拠したデータ構造を使用する。

---

## 1. ToolCallLog（ログ出力形式）

MCPツール呼び出しのログ情報。`MemberAgentLogger.log_tool_invocation()` の出力形式に準拠。

### スキーマ

```python
# TypedDictとして表現（実際にはJSONログ出力）
class ToolCallLog(TypedDict):
    """MCPツール呼び出しログのスキーマ."""

    event: Literal["tool_invocation"]  # 固定値
    execution_id: str                   # エージェント実行ID
    tool_name: str                      # ツール名（例: "mcp__pydantic_tools__fetch_url"）
    parameters: dict[str, object]       # 引数（自動サニタイズ済み）
    execution_time_ms: int              # 実行時間（ミリ秒）
    status: Literal["success", "error"] # 実行結果
    timestamp: str                      # ISO8601形式（例: "2026-01-20T12:34:57.100Z"）
```

### 出力例

```json
{
  "event": "tool_invocation",
  "execution_id": "exec_abc123",
  "tool_name": "mcp__pydantic_tools__fetch_url",
  "parameters": {"url": "https://example.com", "prompt": "Extract title..."},
  "execution_time_ms": 1250,
  "status": "success",
  "timestamp": "2026-01-20T12:34:57.100Z"
}
```

### バリデーションルール

| フィールド | ルール |
|-----------|--------|
| `event` | 常に `"tool_invocation"` |
| `execution_id` | 非空文字列、`log_execution_start()` から取得 |
| `tool_name` | 非空文字列、MCP形式 `mcp__<server>__<tool>` |
| `parameters` | 自動サニタイズ（APIキー等をマスク） |
| `execution_time_ms` | 0以上の整数 |
| `status` | `"success"` または `"error"` |
| `timestamp` | ISO8601形式 |

---

## 2. ExtractedToolCall（内部データ構造）

`ClaudeCodeToolCallExtractor` がメッセージ履歴から抽出する中間データ構造。

### スキーマ

```python
class ExtractedToolCall(TypedDict):
    """メッセージ履歴から抽出したツール呼び出し情報."""

    tool_name: str                       # ツール名
    args_summary: str                    # 引数の概要（切り詰め済み、最大100文字）
    tool_call_id: str | None             # pydantic-aiのtool_call_id
    status: Literal["success", "error", "unknown"]  # マッチング結果
    result_summary: str | None           # 結果の概要（切り詰め済み、最大200文字）
```

### 抽出プロセス

```
pydantic-ai messages (ModelMessage[])
    │
    ├── ToolCallPart → ExtractedToolCall (status="unknown")
    │
    └── ToolReturnPart → マッチング by tool_call_id
                          │
                          └── status="success" or "error"
```

### バリデーションルール

| フィールド | ルール |
|-----------|--------|
| `tool_name` | 非空文字列 |
| `args_summary` | 最大100文字、超過時は `...` で切り詰め |
| `tool_call_id` | pydantic-aiから取得、マッチングに使用 |
| `status` | 初期値 `"unknown"`、`ToolReturnPart` マッチング後に更新 |
| `result_summary` | 最大200文字、超過時は `...` で切り詰め |

---

## 3. LogConfiguration（設定状態）

ログ設定の状態。環境変数から読み取り。

### スキーマ

```python
class LogConfiguration(TypedDict):
    """ログ設定の状態."""

    verbose_enabled: bool    # MIXSEEK_VERBOSE=1 または CLI --verbose
    logfire_enabled: bool    # MIXSEEK_LOGFIRE=1 または CLI --logfire
    log_dir: Path            # ログ出力先ディレクトリ（$WORKSPACE/logs/）
    log_file_pattern: str    # ログファイル名パターン（member-agent-YYYY-MM-DD.log）
```

### 設定優先順位

1. CLI オプション（`--verbose`, `--logfire`）→ 最優先
2. 環境変数（`MIXSEEK_VERBOSE`, `MIXSEEK_LOGFIRE`）→ フォールバック
3. デフォルト値（`false`, `false`）→ 最終フォールバック

---

## 4. 関連エンティティ（既存・参照のみ）

### MemberAgentLogger（mixseek-core）

```python
class MemberAgentLogger:
    """メンバーエージェントのロガー（mixseek-core提供）."""

    def log_execution_start(
        self,
        agent_name: str,
        agent_type: str,
        task: str,
        model_id: str,
        context: dict[str, object] | None = None,
    ) -> str:
        """実行開始をログに記録し、execution_idを返す."""
        ...

    def log_tool_invocation(
        self,
        execution_id: str,
        tool_name: str,
        parameters: dict[str, object],
        execution_time_ms: int,
        status: str,
    ) -> None:
        """ツール呼び出しをログに記録."""
        ...

    def log_execution_complete(
        self,
        execution_id: str,
        result: MemberAgentResult,
        usage_info: dict[str, object] | None = None,
    ) -> None:
        """実行完了をログに記録."""
        ...

    def log_error(
        self,
        execution_id: str,
        error: Exception,
        context: dict[str, object] | None = None,
    ) -> None:
        """エラーをログに記録."""
        ...

    @staticmethod
    def _sanitize_parameters(params: dict[str, object]) -> dict[str, object]:
        """機密情報をマスク."""
        ...
```

### TeamDependencies（core_patch.py）

```python
@dataclass
class TeamDependencies:
    """チーム実行時の依存性（MCP コンテキスト注入用）."""

    execution_id: str           # 現在の実行ID
    workspace_path: Path        # ワークスペースパス
    # ... 他のフィールド
```

---

## 状態遷移

### ツール呼び出しログのライフサイクル

```
[未記録]
    │
    ├── (Layer 1) _wrap_tool_function_for_mcp() 呼び出し
    │   │
    │   ├── 開始: time.perf_counter() 記録
    │   │
    │   ├── 実行: await original_func()
    │   │
    │   └── 終了: log_tool_invocation() 呼び出し
    │       │
    │       └── [記録済み] → ログファイルに出力
    │
    └── (Layer 2) _log_tool_calls_from_history() 呼び出し（execute完了後）
        │
        ├── メッセージ履歴を走査
        │
        ├── ToolCallPart/ToolReturnPart を抽出
        │
        └── log_tool_invocation() 呼び出し
            │
            └── [記録済み] → ログファイルに出力
```

---

## ログ出力先

### ファイル構造

```
$WORKSPACE/
└── logs/
    └── member-agent-YYYY-MM-DD.log  # JSONLines形式
```

### ログローテーション

- 日付ベースのファイル分割（既存の MemberAgentLogger の動作）
- 本機能でのローテーション実装は Out of Scope

---

## 機密情報マスキング

### 対象フィールド

`MemberAgentLogger._sanitize_parameters()` により以下のキーを含むパラメータは自動マスク：

- `api_key`
- `apikey`
- `token`
- `secret`
- `password`
- `credential`
- `auth`

### マスク形式

```json
{
  "url": "https://example.com",
  "api_key": "***REDACTED***"
}
```
