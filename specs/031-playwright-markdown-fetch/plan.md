# Implementation Plan: Playwright + MarkItDown統合Webフェッチャー

**Branch**: `031-playwright-markdown-fetch` | **Date**: 2026-01-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/031-playwright-markdown-fetch/spec.md`
**Related**: Issue #31 - Playwright + MarkItDownを統合したWebフェッチャーエージェントの実装
**Reference**: Groqプロバイダー実装 `specs/003-groq-provider/`, ClaudeCodeプロバイダー実装 `specs/008-claudecode-provider/`

## Summary

mixseek-plusに対して**Playwright + MarkItDown**を使用したWebフェッチャーエージェントを追加する。
`playwright_markdown_fetch` タイプのMember Agentを提供し、動的コンテンツを含むWebページを取得してMarkdown形式に変換する。

**特徴**:
- Playwrightでheadedモード対応（ボット対策回避）
- MarkItDownでHTML→Markdown変換（LLM処理に最適化）
- 任意のモデルプロバイダー対応（`model`フィールドで指定）
- `fetch_page`ツールによるURL取得

**対応戦略**（Groqプロバイダーと同様のパターン）:
- Member Agent: PlaywrightMarkdownFetchAgent（Custom Agent実装）
- ツール: `fetch_page`（URL→Markdown変換）
- ライフサイクル: エージェント単位でブラウザ保持

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Playwright, MarkItDown, pydantic-ai, mixseek-core (BaseMemberAgent, MemberAgentConfig, MemberAgentFactory)
**Storage**: N/A
**Testing**: pytest, pytest-asyncio, pytest-playwright（オプション）
**Target Platform**: Linux/macOS/Windows（Playwrightが動作する環境、headedモードはGUI必須）
**Project Type**: Single project (Pythonパッケージ)
**Performance Goals**: N/A（Playwright/ネットワーク遅延が主要な遅延要因）
**Constraints**: Playwright + Chromiumインストール必須（オプション依存）、headedモードはディスプレイ必須
**Scale/Scope**: mixseek-coreのオーケストレーション機能に統合

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| 1: Test-First Imperative | TDD必須 | ✅ PASS | テストファースト実行可能 |
| 2: Documentation Integrity | 仕様確認必須 | ✅ PASS | spec.md作成済み、Clarification完了 |
| 5: Code Quality Standards | ruff/mypy必須 | ✅ PASS | pyproject.tomlで設定済み |
| 6: Data Accuracy Mandate | 推測禁止 | ✅ PASS | 設定値は定数化、エラー明示 |
| 7: DRY Principle | 既存実装確認 | ✅ PASS | Groqパターン再利用 |
| 9: Python Type Safety | 型注釈必須 | ✅ PASS | 全関数に型注釈付与 |
| 11: Naming Convention | 命名規則遵守 | ✅ PASS | git-conventions.md参照 |

## Project Structure

### Documentation (this feature)

```text
specs/031-playwright-markdown-fetch/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/mixseek_plus/
├── __init__.py          # Public exports (+ PlaywrightMarkdownFetchAgent, register_playwright_agents)
├── cli.py               # CLI wrapper (既存)
├── core_patch.py        # patch_core() (既存)
├── errors.py            # Custom exceptions (+ PlaywrightNotInstalledError)
├── model_factory.py     # create_model() (既存)
├── agents/
│   ├── __init__.py      # Agent exports (+ Playwright)
│   ├── base_playwright_agent.py   # NEW: Base class for Playwright agents
│   └── playwright_markdown_fetch_agent.py  # NEW: PlaywrightMarkdownFetchAgent
└── providers/
    └── __init__.py      # Provider constants (既存)

tests/
├── conftest.py          # Pytest fixtures (+ Playwright)
├── integration/
│   └── test_playwright_fetch_api.py  # NEW: Integration tests (real browser)
└── unit/
    ├── test_playwright_agent.py     # NEW: Agent tests
    └── test_playwright_config.py    # NEW: Config tests
```

**Structure Decision**: Single project structure。Groqプロバイダー実装と同様のパターンで拡張。

## Complexity Tracking

該当なし（憲法違反なし）

## Implementation Mapping

### Groqプロバイダーとの対応関係

| コンポーネント | Groq実装 | Playwright実装 |
|--------------|----------|----------------|
| ベースエージェント | `BaseGroqAgent` | `BasePlaywrightAgent` |
| プレーンエージェント | `GroqPlainAgent` | `PlaywrightMarkdownFetchAgent` |
| 登録関数 | `register_groq_agents()` | `register_playwright_agents()` |
| エラークラス | - | `PlaywrightNotInstalledError`, `FetchError` |
| 設定クラス | `MemberAgentConfig` | `PlaywrightConfig`（拡張） |

### Playwright固有の考慮事項

1. **ライフサイクル管理**
   - ブラウザ: エージェント単位で保持（遅延初期化）
   - BrowserContext: リクエスト毎に作成・破棄
   - Page: リクエスト毎に作成・破棄

2. **PlaywrightConfig設定項目**
   - `headless`: ヘッドレスモード（デフォルト: true）
   - `timeout_ms`: タイムアウト（デフォルト: 30000）
   - `wait_for_load_state`: 待機条件（load/domcontentloaded/networkidle）
   - `retry_count`: リトライ回数（デフォルト: 0）
   - `retry_delay_ms`: リトライ遅延（デフォルト: 1000）
   - `block_resources`: ブロックするリソースタイプ

3. **エラーハンドリング**
   - `PlaywrightNotInstalledError`: Playwright未インストール
   - `FetchError`: ページ取得エラー（タイムアウト、接続エラー等）
   - `ConversionError`: Markdown変換エラー

### Post-Phase 1 Check

| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| 1: Test-First Imperative | TDD必須 | ✅ PASS | tasks.mdでTDDワークフロー定義予定 |
| 2: Documentation Integrity | 仕様確認必須 | ✅ PASS | research.md, data-model.md作成済み |
| 4: Simplicity | 最小構造 | ✅ PASS | 単一プロジェクト、Groqパターン再利用 |
| 5: Code Quality Standards | ruff/mypy必須 | ✅ PASS | 設定済み |
| 6: Data Accuracy Mandate | 推測禁止 | ✅ PASS | 設定値定数化、明示的エラー |
| 7: DRY Principle | 重複禁止 | ✅ PASS | BasePlaywrightAgent継承 |
| 8: Refactoring Policy | 既存修正優先 | ✅ PASS | 既存errors.py拡張 |
| 9: Python Type Safety | 型注釈必須 | ✅ PASS | data-model.mdで型定義 |
| 11: Naming Convention | 命名規則遵守 | ✅ PASS | Playwright*命名 |

## Requirements Mapping

### 要件IDと実装ファイルの対応

| 要件ID | 説明 | 実装ファイル |
|--------|------|-------------|
| FR-001 | playwright_markdown_fetchタイプ提供 | `agents/__init__.py` |
| FR-002 | TOML設定でPlaywright固有設定 | `agents/playwright_markdown_fetch_agent.py` |
| FR-003 | HTTPリトライ（指数バックオフ） | `agents/base_playwright_agent.py` |
| FR-004 | リソースブロック機能 | `agents/base_playwright_agent.py` |
| FR-005 | MarkItDownでMarkdown変換 | `agents/base_playwright_agent.py` |
| FR-006 | 任意のモデルプロバイダー対応 | `agents/playwright_markdown_fetch_agent.py` |
| FR-007 | Playwrightオプション依存関係 | `pyproject.toml` |
| FR-008 | fetch_pageツール提供 | `agents/playwright_markdown_fetch_agent.py` |
| FR-009 | MemberAgentFactory登録 | `agents/__init__.py` |
| FR-010 | ブラウザライフサイクル管理 | `agents/base_playwright_agent.py` |

## Dependencies

### 新規依存関係（オプション）

```toml
[project.optional-dependencies]
playwright = [
    "playwright>=1.57.0",
    "markitdown>=0.1.4",
]
```

### インストール手順

```bash
pip install mixseek-plus[playwright]
playwright install chromium
```
