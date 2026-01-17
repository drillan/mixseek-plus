# Implementation Plan: Groqプロバイダーのサポート追加

**Branch**: `003-groq-provider` | **Date**: 2026-01-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-groq-provider/spec.md`
**Related**: Issue #5 - エージェント別モデルプロバイダー制約の文書化

## Summary

mixseek-coreに対してGroqプロバイダーのサポートを追加する。
pydantic-aiの`GroqModel`を使用してモデルインスタンスを作成し、
mixseek-coreの既存プロバイダーと統一的なインターフェース（`create_model()`関数）で利用可能にする。

**対応戦略**（Issue #5の制約に基づく）:
- Member Agent (Plain/WebSearch相当): Custom Agent実装
- Leader/Evaluator: Monkey-patch（暫定対応）
- Web Fetch/Code Execution: 対応不可（mixseek-core側の制約）

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: pydantic-ai (GroqModel), mixseek-core (create_authenticated_model, BaseMemberAgent, MemberAgentConfig)
**Storage**: N/A
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux/macOS/Windows
**Project Type**: Single project (Pythonパッケージ)
**Performance Goals**: N/A（LLM API呼び出しが主要な遅延要因）
**Constraints**: Groq APIのレート制限、mixseek-coreのプロバイダー検証制約

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| 1: Test-First Imperative | TDD必須 | ✅ PASS | テストファースト実行可能 |
| 2: Documentation Integrity | 仕様確認必須 | ✅ PASS | spec.md作成済み |
| 5: Code Quality Standards | ruff/mypy必須 | ✅ PASS | pyproject.tomlで設定済み |
| 6: Data Accuracy Mandate | APIキー環境変数取得 | ✅ PASS | ハードコード禁止を遵守 |
| 7: DRY Principle | 既存実装確認 | ✅ PASS | mixseek-core, pydantic-ai利用 |
| 9: Python Type Safety | 型注釈必須 | ✅ PASS | 全関数に型注釈付与 |
| 11: Naming Convention | 命名規則遵守 | ✅ PASS | git-conventions.md参照 |

## Project Structure

### Documentation (this feature)

```text
specs/003-groq-provider/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/mixseek_plus/
├── __init__.py          # Public exports (create_model, patch_core, agents)
├── cli.py               # CLI wrapper (NEW - overrides mixseek command)
├── core_patch.py        # patch_core() implementation
├── errors.py            # Custom exceptions (ModelCreationError)
├── model_factory.py     # create_model() implementation
├── py.typed             # PEP 561 marker
├── agents/
│   ├── __init__.py      # Agent exports
│   ├── groq_agent.py    # GroqPlainAgent
│   └── groq_web_search_agent.py  # GroqWebSearchAgent
└── providers/
    ├── __init__.py      # Provider constants
    └── groq.py          # Groq model creation

tests/
├── conftest.py          # Pytest fixtures
├── integration/
│   └── test_groq_api.py # Integration tests (real API)
└── unit/
    ├── test_groq_provider.py  # Provider tests
    └── test_model_factory.py  # Factory tests
```

**Structure Decision**: Single project structure。既存の実装（GR-001〜GR-012完了）を拡張し、残りの要件（GR-050〜GR-063）を追加実装する。

## Complexity Tracking

該当なし（憲法違反なし）

## Implementation Status (Current)

### 実装済み（spec.mdの要件との対応）

| 要件ID | 状態 | 説明 | 実装ファイル |
|--------|------|------|--------------|
| GR-001 | ✅ Done | create_model関数提供 | model_factory.py |
| GR-002 | ✅ Done | Groqモデル作成 | providers/groq.py |
| GR-003 | ✅ Done | mixseek-core委譲 | model_factory.py |
| GR-010 | ✅ Done | GROQ_API_KEY取得 | providers/groq.py |
| GR-011 | ✅ Done | 未設定エラーメッセージ | providers/groq.py |
| GR-012 | ✅ Done | 形式不正エラーメッセージ | providers/groq.py |
| GR-020 | ✅ Done | モデルサポート | 検証なし（API側で検証） |
| GR-021 | ✅ Done | 任意モデル名許可 | providers/groq.py |
| GR-022 | ✅ Done | スラッシュ含むモデル名対応 | providers/groq.py |
| GR-030 | ✅ Done | 形式エラーメッセージ | model_factory.py |
| GR-031 | ✅ Done | プロバイダー一覧エラー | model_factory.py |
| GR-032 | ✅ Done | API呼び出しエラー | 詳細なエラーラップ実装済み（401/429/503） |
| GR-040 | ✅ Done | create_modelエクスポート | __init__.py |

### 実装完了（Phase 7で全て完了）

| 要件ID | 状態 | 説明 |
|--------|------|------|
| GR-050 | ✅ Done | GroqPlainMemberAgent |
| GR-051 | ✅ Done | GroqWebSearchMemberAgent |
| GR-052 | ✅ Done | BaseMemberAgent継承 |
| GR-053 | ✅ Done | Factory登録（groq_plain, groq_web_search） |
| GR-054 | ✅ Done | TOML設定対応 |
| GR-060 | ✅ Done | patch_core()関数 |
| GR-061 | ✅ Done | Leader/Evaluatorでのgroq:対応 |
| GR-062 | ✅ Done | 明示的パッチ呼び出し |
| GR-063 | ✅ Done | パッチ未適用時エラー（GroqNotPatchedError） |
| GR-041 | ✅ Done | patch_coreエクスポート |
| GR-042 | ✅ Done | エージェントクラスエクスポート |
| GR-070〜GR-073 | ✅ Done | CLI統合 |
