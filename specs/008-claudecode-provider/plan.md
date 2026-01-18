# Implementation Plan: ClaudeCodeプロバイダーのサポート追加

**Branch**: `008-claudecode-provider` | **Date**: 2026-01-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-claudecode-provider/spec.md`
**Related**: Issue #8 - ClaudeCodeプロバイダーのサポート追加
**Reference**: Groqプロバイダー実装 `specs/003-groq-provider/`

## Summary

mixseek-plusに対して**claudecode-model**パッケージを使用したClaudeCodeプロバイダーのサポートを追加する。
`claudecode:` プレフィックスのモデルIDを`create_model()`関数で受け付け、ClaudeCodeModelインスタンスを作成する。

**特徴**:
- Claude Code CLI経由でLLMを呼び出すため、**APIキー環境変数（ANTHROPIC_API_KEY等）の設定が不要**
- 組み込みツール（Bash、Read/Write/Edit、Glob/Grep、WebFetch/WebSearch）により、**単一のPlainAgentで複数機能を提供**

**対応戦略**（Groqプロバイダーと同様のパターン）:
- Member Agent: ClaudeCodePlainAgent（Custom Agent実装）
- Leader/Evaluator/Judgment: `patch_core()` 拡張
- Web Search/Web Fetch/Code Execution: **対応不要**（ClaudeCodePlainAgentの組み込み機能として提供）

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: claudecode-model, pydantic-ai, mixseek-core (create_authenticated_model, BaseMemberAgent, MemberAgentConfig)
**Storage**: N/A
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux/macOS/Windows（Claude Code CLIが動作する環境）
**Project Type**: Single project (Pythonパッケージ)
**Performance Goals**: N/A（LLM API呼び出しが主要な遅延要因）
**Constraints**: Claude Code CLI必須、セッション認証必須
**Scale/Scope**: mixseek-coreのオーケストレーション機能に統合

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| 1: Test-First Imperative | TDD必須 | ✅ PASS | テストファースト実行可能 |
| 2: Documentation Integrity | 仕様確認必須 | ✅ PASS | spec.md作成済み |
| 5: Code Quality Standards | ruff/mypy必須 | ✅ PASS | pyproject.tomlで設定済み |
| 6: Data Accuracy Mandate | 推測禁止 | ✅ PASS | CLI存在チェック・エラー明示 |
| 7: DRY Principle | 既存実装確認 | ✅ PASS | Groqパターン再利用 |
| 9: Python Type Safety | 型注釈必須 | ✅ PASS | 全関数に型注釈付与 |
| 11: Naming Convention | 命名規則遵守 | ✅ PASS | git-conventions.md参照 |

## Project Structure

### Documentation (this feature)

```text
specs/008-claudecode-provider/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/mixseek_plus/
├── __init__.py          # Public exports (+ ClaudeCodePlainAgent, register_claudecode_agents)
├── cli.py               # CLI wrapper (+ ClaudeCode patch)
├── core_patch.py        # patch_core() (+ ClaudeCode support)
├── errors.py            # Custom exceptions (既存)
├── model_factory.py     # create_model() (+ claudecode: routing)
├── agents/
│   ├── __init__.py      # Agent exports (+ ClaudeCode)
│   ├── base_claudecode_agent.py  # NEW: Base class for ClaudeCode agents
│   └── claudecode_agent.py       # NEW: ClaudeCodePlainAgent
└── providers/
    ├── __init__.py      # Provider constants (+ CLAUDECODE_PROVIDER_PREFIX)
    └── claudecode.py    # NEW: ClaudeCode model creation

tests/
├── conftest.py          # Pytest fixtures (+ ClaudeCode)
├── integration/
│   └── test_claudecode_api.py  # NEW: Integration tests (real CLI)
└── unit/
    ├── test_claudecode_provider.py  # NEW: Provider tests
    └── test_model_factory.py        # 既存（+ claudecode tests）
```

**Structure Decision**: Single project structure。Groqプロバイダー実装と同様のパターンで拡張。

## Complexity Tracking

該当なし（憲法違反なし）

## Implementation Mapping

### Groqプロバイダーとの対応関係

| コンポーネント | Groq実装 | ClaudeCode実装 |
|--------------|----------|----------------|
| プロバイダー定数 | `GROQ_PROVIDER_PREFIX` | `CLAUDECODE_PROVIDER_PREFIX` |
| モデル作成関数 | `create_groq_model()` | `create_claudecode_model()` |
| ベースエージェント | `BaseGroqAgent` | `BaseClaudeCodeAgent` |
| プレーンエージェント | `GroqPlainAgent` | `ClaudeCodePlainAgent` |
| Web検索エージェント | `GroqWebSearchAgent` | **不要**（組み込みツール） |
| 登録関数 | `register_groq_agents()` | `register_claudecode_agents()` |
| パッチエラー | `GroqNotPatchedError` | `ClaudeCodeNotPatchedError` |

### ClaudeCode固有の考慮事項

1. **認証方式の違い**
   - Groq: `GROQ_API_KEY` 環境変数
   - ClaudeCode: Claude Code CLIのセッション認証（APIキー不要）

2. **tool_settings対応**
   - `allowed_tools`: 利用可能ツールの制限
   - `disallowed_tools`: 禁止ツールの指定
   - `permission_mode`: パーミッションモード（bypassPermissions等）
   - `working_directory`: 作業ディレクトリ
   - `max_turns`: 最大ターン数

3. **エラーハンドリング**
   - `CLINotFoundError`: Claude Code CLI未インストール
   - `CLIExecutionError`: CLI実行エラー
   - `CLIResponseParseError`: レスポンス解析エラー

### Post-Phase 1 Check

| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| 1: Test-First Imperative | TDD必須 | ✅ PASS | tasks.mdでTDDワークフロー定義予定 |
| 2: Documentation Integrity | 仕様確認必須 | ✅ PASS | research.md, data-model.md作成済み |
| 4: Simplicity | 最小構造 | ✅ PASS | 単一プロジェクト、Groqパターン再利用 |
| 5: Code Quality Standards | ruff/mypy必須 | ✅ PASS | 設定済み |
| 6: Data Accuracy Mandate | 推測禁止 | ✅ PASS | CLI存在チェック、明示的エラー |
| 7: DRY Principle | 重複禁止 | ✅ PASS | BaseClaudeCodeAgent継承 |
| 8: Refactoring Policy | 既存修正優先 | ✅ PASS | 既存core_patch.py拡張 |
| 9: Python Type Safety | 型注釈必須 | ✅ PASS | data-model.mdで型定義 |
| 11: Naming Convention | 命名規則遵守 | ✅ PASS | ClaudeCode*命名 |

## Requirements Mapping

### 要件IDと実装ファイルの対応

| 要件ID | 説明 | 実装ファイル |
|--------|------|-------------|
| CC-001 | CLAUDECODE_PROVIDER_PREFIX定義 | `providers/__init__.py` |
| CC-010 | create_model対応 | `model_factory.py` |
| CC-011 | ClaudeCodeModel使用 | `providers/claudecode.py` |
| CC-012 | 他プロバイダー委譲 | `model_factory.py` |
| CC-020 | create_claudecode_model() | `providers/claudecode.py` |
| CC-021 | claudecode:ルーティング | `model_factory.py` |
| CC-030 | ClaudeCodePlainAgent | `agents/claudecode_agent.py` |
| CC-031 | BaseMemberAgent継承 | `agents/base_claudecode_agent.py` |
| CC-032 | Factory登録 | `agents/__init__.py` |
| CC-033 | TOML type対応 | `agents/__init__.py` |
| CC-034 | 組み込みツール活用 | `agents/claudecode_agent.py` |
| CC-040 | tool_settingsセクション | `agents/claudecode_agent.py` |
| CC-041 | allowed_tools | `agents/claudecode_agent.py` |
| CC-042 | permission_mode | `agents/claudecode_agent.py` |
| CC-043 | デフォルト値 | `agents/claudecode_agent.py` |
| CC-050 | patch_core拡張 | `core_patch.py` |
| CC-051 | Leader/Evaluator対応 | `core_patch.py` |
| CC-052 | 明示的パッチ呼び出し | `core_patch.py` |
| CC-060 | CLI不可エラー | `providers/claudecode.py` |
| CC-061 | エラーラップ | `agents/base_claudecode_agent.py` |
| CC-062 | 形式エラー | `model_factory.py` |
| CC-070 | エクスポート | `__init__.py` |
| CC-071 | register_claudecode_agents() | `agents/__init__.py`
