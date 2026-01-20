# Implementation Plan: ClaudeCodeModel固有のロギング・オブザーバビリティ

**Branch**: `033-claudecode-logging` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/033-claudecode-logging/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

ClaudeCodeModelはClaude Code CLIをラップしたpydantic-aiモデル実装であり、MCP経由のツール呼び出しがpydantic-aiのインストルメンテーションの外側にあるため、ロギングとオブザーバビリティに問題が発生している。本機能では既存の`MemberAgentLogger.log_tool_invocation()`を活用し、MCPツール呼び出しの可視化、Verboseモードによる詳細ログ、オプショナルなLogfire統合を実現する。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**:
- mixseek-core（MemberAgentLogger, BaseMemberAgent, MemberAgentConfig）
- pydantic-ai（メッセージ履歴、ToolCallPart、ToolReturnPart）
- claudecode-model（ClaudeCodeModel）
- logfire 4.15+（オプショナル依存）

**Storage**: File-based logging (`$WORKSPACE/logs/member-agent-YYYY-MM-DD.log`)
**Testing**: pytest with mocked pydantic-ai messages
**Target Platform**: Linux server / macOS
**Project Type**: Single project - CLIツールパッケージ
**Performance Goals**: verboseモード無効時のログ出力によるパフォーマンス影響5%未満
**Constraints**: 機密情報（APIキー、認証トークン等）はログに含めない
**Scale/Scope**: mixseek-plus パッケージ内の ClaudeCode 関連エージェント

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Article | Status | Notes |
|---------|--------|-------|
| Article 1: Test-First | ✅ PASS | TDDワークフローに従って実装。テスト作成→承認→Red確認→実装 |
| Article 2: Documentation Integrity | ✅ PASS | spec.md で仕様確定済み。plan.md で設計を文書化 |
| Article 3: CLI & Plugin Design | ⚠️ NEEDS CLARIFICATION | `--verbose`/`--logfire` オプション追加方法要調査 |
| Article 4: Simplicity | ✅ PASS | 既存の MemberAgentLogger を活用。新規ファイルは最小限（2-3ファイル） |
| Article 5: Code Quality | ✅ PASS | ruff, mypy, pytest による品質チェック必須 |
| Article 6: Data Accuracy | ✅ PASS | 環境変数/設定による制御。ハードコード禁止 |
| Article 7: DRY Principle | ✅ PASS | 既存の log_tool_invocation() を再利用 |
| Article 8: Refactoring | ✅ PASS | 既存クラスへの機能追加（V2クラス作成しない） |
| Article 9: Python Type Safety | ✅ PASS | 全関数に型注釈必須 |
| Article 10: Python Docstring | ✅ PASS | Google-style docstring 推奨 |
| Article 11: Naming Convention | ✅ PASS | git-conventions.md に準拠 |

### Post-Phase 1 Re-evaluation

| Article | Status | Notes |
|---------|--------|-------|
| Article 1: Test-First | ✅ PASS | 変更なし |
| Article 2: Documentation Integrity | ✅ PASS | research.md, data-model.md, quickstart.md 作成完了 |
| Article 3: CLI & Plugin Design | ✅ PASS | **解決済み**: mixseek-core に既に `--verbose`/`--logfire` オプション存在。追加実装不要 |
| Article 4: Simplicity | ✅ PASS | 変更なし |
| Article 5: Code Quality | ✅ PASS | 変更なし |
| Article 6: Data Accuracy | ✅ PASS | 変更なし |
| Article 7: DRY Principle | ✅ PASS | 変更なし |
| Article 8: Refactoring | ✅ PASS | 変更なし |
| Article 9: Python Type Safety | ✅ PASS | 変更なし |
| Article 10: Python Docstring | ✅ PASS | 変更なし |
| Article 11: Naming Convention | ✅ PASS | 変更なし |

**RESOLVED**: CLIオプション追加方法

調査の結果、mixseek-core の `exec` コマンドには既に `--verbose` と `--logfire` オプションが存在することが判明。
- `/mixseek/cli/commands/exec.py` に実装済み
- `/mixseek/cli/common_options.py` でオプション定義
- mixseek-plus は `core_app` を直接再利用しているため、これらのオプションは自動的に利用可能

**結論**: CLI wrapper 作成は不要。環境変数 `MIXSEEK_VERBOSE` / `MIXSEEK_LOGFIRE` による内部チェック機能のみ実装する。

## Project Structure

### Documentation (this feature)

```text
specs/033-claudecode-logging/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (N/A - internal logging feature)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/mixseek_plus/
├── cli.py                              # CLI entry point (to be modified)
├── core_patch.py                       # MCP wrapper (to be modified)
├── agents/
│   ├── base_claudecode_agent.py        # ClaudeCode base class (to be modified)
│   └── playwright_markdown_fetch_agent.py  # Playwright agent (to be modified)
├── utils/
│   └── claudecode_logging.py           # NEW: Tool call extractor
└── observability/
    ├── __init__.py                     # NEW: Module exports
    └── logfire_integration.py          # NEW: Logfire setup

tests/
├── unit/
│   ├── test_claudecode_logging.py      # NEW: Tool call extractor tests
│   └── test_logfire_integration.py     # NEW: Logfire integration tests
└── integration/
    └── (existing tests)
```

**Structure Decision**: Single project structure. 新規ファイルは `utils/` と `observability/` サブパッケージに配置。既存の `agents/` 配下のファイルを修正。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A - 憲法違反なし | - | - |

## Architecture Overview

```
┌───────────────────────────────────────────────────────────────┐
│ Layer 1: 短期対応 - 即時ログ出力                                │
│ ├── core_patch.py: _wrap_tool_function_for_mcp() 内でログ      │
│ └── playwright_markdown_fetch_agent.py: _wrap_tool_for_mcp()  │
│     - 実行時間測定 (time.perf_counter())                       │
│     - MIXSEEK_VERBOSE環境変数で制御                            │
│     - MemberAgentLogger.log_tool_invocation() 使用             │
└───────────────────────────────────────────────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────┐
│ Layer 2: 中期対応 - メッセージ履歴からの抽出                     │
│ ├── utils/claudecode_logging.py (新規)                        │
│ │   └── ClaudeCodeToolCallExtractor                           │
│ │       - extract_tool_calls(messages)                        │
│ │       - _summarize_args(), _match_tool_return()             │
│ └── base_claudecode_agent.py                                  │
│     └── _log_tool_calls_from_history()                        │
└───────────────────────────────────────────────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────┐
│ Layer 3: 中期対応 - Logfire統合 (オプショナル)                   │
│ └── observability/logfire_integration.py (新規)               │
│     └── setup_logfire_instrumentation()                       │
│         - pydantic-ai自動インストルメンテーション                 │
│         - MIXSEEK_LOGFIRE環境変数で制御                        │
└───────────────────────────────────────────────────────────────┘
```

## Implementation Phases (Summary)

### Phase 1: 短期対応（即効性）
- `core_patch.py` に `_is_verbose_mode()` 追加
- `_wrap_tool_function_for_mcp()` にログ出力追加（開始、成功、エラー）
- `playwright_markdown_fetch_agent.py` に同様のパターン適用

### Phase 2: 中期対応（メッセージ抽出）
- `utils/claudecode_logging.py` 新規作成
- `ClaudeCodeToolCallExtractor` クラス実装
- `base_claudecode_agent.py` に `_log_tool_calls_from_history()` 追加

### Phase 3: 中期対応（Logfire）
- `observability/` パッケージ新規作成
- `logfire_integration.py` でオプショナルLogfire統合
- オプション未指定時/パッケージ未インストール時は警告して継続

### Phase 4: CLI拡張（決定次第）
- `--verbose` / `--logfire` オプション追加
- 環境変数設定後に core exec 呼び出し

## Dependencies Graph

```
Task 1.1 (core_patch verbose) → Task 1.2 (playwright verbose)
                                         ↓
Task 2.1 (claudecode_logging.py) → Task 2.2 (base_claudecode_agent)
                                         ↓
                              Task 2.3 (unit tests)
                                         ↓
Task 3.1 (observability pkg) → Task 3.2 (logfire tests)
                                         ↓
                              Phase 4 (CLI / docs)
```

## Key Design Decisions

1. **既存パターンとの整合性**: `MemberAgentLogger.log_tool_invocation()` を使用し、他モデル（Groq, OpenAI等）と同一のJSON形式でログ出力

2. **セキュリティ**: `MemberAgentLogger._sanitize_parameters()` による自動マスキングを活用

3. **パフォーマンス**: `MIXSEEK_VERBOSE=false` の場合はログ出力をスキップ

4. **オプショナル依存**: logfire はオプショナル依存とし、インストールされていない場合は警告のみで継続
