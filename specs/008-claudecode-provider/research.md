# Research: ClaudeCodeプロバイダー

**Date**: 2026-01-17
**Status**: Complete

## Research Tasks

### 1. claudecode-model パッケージAPI

**決定**: claudecode-model v0.1.0 のAPIを使用

**調査結果**:
- パッケージは `pyproject.toml` に依存関係として追加済み
- `ClaudeCodeModel` クラスがpydantic-ai `Model` インターフェースを実装

**ClaudeCodeModel コンストラクタ**:
```python
def __init__(
    self,
    model_name: str = "claude-sonnet-4-5",
    *,
    working_directory: str | None = None,
    timeout: float = 120.0,
    allowed_tools: list[str] | None = None,
    disallowed_tools: list[str] | None = None,
    permission_mode: str | None = None,
    max_turns: int | None = None,
) -> None
```

**利用可能なエラー型**:
- `CLINotFoundError`: Claude Code CLIが見つからない
- `CLIExecutionError`: CLI実行エラー
- `CLIResponseParseError`: レスポンス解析エラー

**理由**: 検証スクリプト（`ai_working/validate-claudecode-model/`）で互換性確認済み

**検討した代替案**:
- 直接Claude Code CLI呼び出し → パッケージが提供するpydantic-ai統合を活用すべき

### 2. Groqプロバイダーパターンの再利用

**決定**: Groqプロバイダーと同様のアーキテクチャパターンを採用

**調査結果**:
既存のGroqプロバイダー実装を分析し、以下のパターンを特定:

| コンポーネント | 役割 |
|--------------|------|
| `providers/__init__.py` | プロバイダープレフィックス定数 |
| `providers/groq.py` | モデル作成関数 |
| `model_factory.py` | プロバイダーごとのルーティング |
| `agents/base_groq_agent.py` | エージェント共通ベースクラス |
| `agents/groq_agent.py` | プレーンエージェント実装 |
| `core_patch.py` | Leader/Evaluator対応パッチ |

**理由**:
- 一貫したコードベース維持
- DRY原則の遵守（Article 7）
- 検証済みパターンの再利用

**検討した代替案**:
- 新しいアーキテクチャパターン → 不必要な複雑性、既存パターンで十分

### 3. 認証方式の違い

**決定**: ClaudeCodeは環境変数によるAPIキー検証を行わない

**調査結果**:
- Groq: `GROQ_API_KEY` 環境変数が必須、`gsk_` プレフィックスを検証
- ClaudeCode: Claude Code CLIのセッション認証を使用、APIキー不要

**ClaudeCode認証の特徴**:
1. Claude Code CLIがインストール済みであること（`curl -fsSL https://claude.ai/install.sh | bash`）
2. Claudeサブスクリプション（Pro/Max/Teams/Enterprise）またはClaude Consoleアカウントがあること
3. 初回起動時（`claude`コマンド実行）に認証フローが完了していること
4. 環境変数の設定は不要

**エラーハンドリング**:
- CLI未インストール: `CLINotFoundError`をキャッチし、インストールコマンドを案内
- セッション無効: `CLIExecutionError`をキャッチし、`claude`コマンドでの再認証を案内

**理由**: ClaudeCodeModelの設計思想に準拠

**検討した代替案**:
- APIキー環境変数を要求 → ClaudeCodeの利点（APIキー不要）を損なう

### 4. tool_settings 設計

**決定**: TOML設定で `[members.tool_settings.claudecode]` セクションをサポート

**調査結果**:
プロトタイプ実装（`ai_working/validate-claudecode-model/04_member_agent_prototype.py`）で以下の設定を確認:

```toml
[members]
name = "claudecode-agent"
type = "claudecode_plain"
model = "claudecode:claude-sonnet-4-5"

[members.tool_settings.claudecode]
allowed_tools = ["Read", "Glob", "Grep", "Bash"]
disallowed_tools = ["Write", "Edit"]
permission_mode = "bypassPermissions"
working_directory = "/tmp"
max_turns = 5
```

**設定項目**（Claude Code CLI `--flags` に対応）:
| 設定 | 型 | 説明 | CLI相当 | デフォルト |
|------|-----|------|---------|----------|
| `allowed_tools` | `list[str]` | 許可ツールのホワイトリスト | `--allowedTools` | None（全ツール許可） |
| `disallowed_tools` | `list[str]` | 禁止ツールのブラックリスト | `--disallowedTools` | None |
| `permission_mode` | `str` | パーミッションモード | `--permission-mode` | None |
| `working_directory` | `str` | 作業ディレクトリ | N/A | None（カレント） |
| `max_turns` | `int` | 最大ターン数（printモード） | `--max-turns` | None |

**permission_mode値**:
- `"bypassPermissions"`: パーミッション確認をスキップ（`--dangerously-skip-permissions`相当）

**理由**:
- CC-040〜CC-043要件に対応
- ClaudeCodeModelのAPIに1:1でマッピング

**検討した代替案**:
- グローバル設定 → Agent単位の柔軟性を損なう

### 5. Web検索/コード実行エージェントの非必要性

**決定**: `claudecode_web_search`、`claudecode_code_execution` エージェントは実装しない

**調査結果**:
ClaudeCodeModelは以下の組み込みツールを提供:

| ツール | 機能 | Groq相当 |
|--------|------|----------|
| WebSearch | Web検索 | `groq_web_search` |
| WebFetch | Webページ取得 | N/A |
| Bash | コマンド実行 | N/A（mixseek-core制約） |
| Read/Write/Edit | ファイル操作 | N/A |
| Glob/Grep | ファイル検索 | N/A |

**理由**:
- spec.md Constraints セクションで明記
- ClaudeCodePlainAgentが全機能を包含
- 追加エージェント実装は冗長

**検討した代替案**:
- 個別エージェント実装 → 機能重複、保守コスト増

### 6. patch_core() 拡張設計

**決定**: 既存の `patch_core()` を拡張し、`claudecode:` プレフィックスをサポート

**調査結果**:
現在の `core_patch.py`:
1. `GROQ_PROVIDER_PREFIX` をチェック
2. 該当する場合は `create_groq_model()` を呼び出し
3. それ以外は元の `create_authenticated_model()` に委譲

拡張後:
1. `CLAUDECODE_PROVIDER_PREFIX` をチェック（追加）
2. 該当する場合は `create_claudecode_model()` を呼び出し（追加）
3. `GROQ_PROVIDER_PREFIX` をチェック
4. 該当する場合は `create_groq_model()` を呼び出し
5. それ以外は元の `create_authenticated_model()` に委譲

**理由**:
- 既存のGroq対応を破壊しない
- 単一の `patch_core()` 呼び出しで全プロバイダー有効化

**検討した代替案**:
- 別の `patch_claudecode()` 関数 → ユーザー体験の複雑化

## 追加調査: サポートモデル

**spec.md記載のサポートモデル**:
- Current: `claude-sonnet-4-5`, `claude-haiku-4-5`, `claude-opus-4-5`
- Legacy: `claude-opus-4-1`, `claude-sonnet-4-0`, `claude-opus-4-0`
- フルバージョン指定: `claude-sonnet-4-5-20250929` 等

**実装方針**:
- モデル名のバリデーションは行わない（Groqと同様）
- 不正なモデル名はClaudeCode側でエラーを返す
- エラーはラップして表示

## 結論

すべての不明点が解消され、Phase 1（設計）に進む準備が整った。

**主要な設計決定**:
1. Groqプロバイダーパターンを踏襲
2. 認証はClaude Code CLIのセッション認証に依存
3. tool_settingsでClaudeCode固有設定をサポート
4. 単一のClaudeCodePlainAgentで全機能を提供
5. patch_core()を拡張してLeader/Evaluator対応
