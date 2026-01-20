# Implementation Plan: Tavily汎用検索エージェント

**Branch**: `039-tavily-search-agent` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/039-tavily-search-agent/spec.md`

## Summary

Groq/ClaudeCode両対応のTavily検索エージェントを追加する。3層クリーンアーキテクチャ（Infrastructure → Domain → Application）を採用し、TavilyToolsRepositoryMixinでツール実装を共有化。Tavilyの全機能（search, extract, get_search_context）を提供し、将来のプロバイダー拡張にも対応。既存のgroq_web_searchは維持して後方互換性を確保。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: pydantic-ai, mixseek-core (BaseMemberAgent, MemberAgentConfig, MemberAgentFactory), tavily-python, claudecode-model
**Storage**: N/A
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux/macOS (CLI)
**Project Type**: Single
**Performance Goals**: 検索クエリ応答30秒以内（タイムアウト設定準拠）
**Constraints**: Tavily API呼び出しタイムアウト30秒、リトライ最大3回（指数バックオフ）
**Scale/Scope**: 2つの新規エージェントタイプ、1つのMixin、1つのAPIクライアント

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| Article 1: Test-First | TDD必須 | ✅ PASS | tasks.mdでテスト先行を実装順序に反映 |
| Article 2: Documentation Integrity | 仕様確認・整合性 | ✅ PASS | spec.md完成済み、Clarifications解決済み |
| Article 4: Simplicity | 最小3プロジェクト | ✅ PASS | 単一プロジェクト構造維持 |
| Article 5: Code Quality | 品質チェック必須 | ✅ PASS | ruff + mypy + pytest 実行予定 |
| Article 6: Data Accuracy | 推測禁止 | ✅ PASS | 環境変数TAVILY_API_KEY使用、ハードコード禁止 |
| Article 7: DRY Principle | 重複禁止 | ✅ PASS | TavilyToolsRepositoryMixinで共通化 |
| Article 9: Type Safety | 型注釈必須 | ✅ PASS | 全関数・メソッドに型注釈 |
| Article 11: Naming Convention | 命名規則準拠 | ✅ PASS | git-conventions.md準拠 |

**Violations**: なし

## Project Structure

### Documentation (this feature)

```text
specs/039-tavily-search-agent/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Technical research and decisions
├── data-model.md        # Entity definitions and types
├── quickstart.md        # Usage examples
├── contracts/           # API contracts
│   └── tavily-tools.md  # Tool interface definitions
└── tasks.md             # Implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/mixseek_plus/
├── agents/
│   ├── __init__.py                       # 更新: register_tavily_agents()追加
│   ├── base_groq_agent.py               # 既存（参照のみ）
│   ├── base_claudecode_agent.py         # 既存（参照のみ）
│   ├── groq_web_search_agent.py         # 既存（変更なし - 後方互換性）
│   ├── groq_tavily_search_agent.py      # ★ 新規
│   ├── claudecode_tavily_search_agent.py # ★ 新規
│   └── mixins/
│       ├── __init__.py                  # 更新: TavilyToolsRepositoryMixin追加
│       ├── execution.py                 # 既存（参照のみ）
│       └── tavily_tools.py              # ★ 新規
├── providers/
│   ├── tavily.py                        # 既存（参照のみ）
│   └── tavily_client.py                 # ★ 新規
├── errors.py                            # 更新: TavilyAPIError追加
└── types.py                             # 更新: Tavily関連TypedDict追加

tests/
├── unit/
│   ├── test_tavily_client.py            # ★ 新規
│   ├── test_tavily_tools_mixin.py       # ★ 新規
│   ├── test_groq_tavily_search_agent.py # ★ 新規
│   └── test_claudecode_tavily_search_agent.py # ★ 新規
└── integration/
    └── test_tavily_search_integration.py # ★ 新規
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。新規ファイルは既存のディレクトリ構造に配置。

## Implementation Phases

### Phase依存関係図

```
Phase 1: Infrastructure Layer
    └── TavilyAPIClient, TavilyAPIError, TavilySearchResult, TavilyExtractResult
              │
              ▼
Phase 2: Domain Layer
    └── TavilyToolsRepositoryMixin, TavilySearchDeps
              │
              ├─────────────────────────┐
              ▼                         ▼
Phase 3: Application (Groq)    Phase 4: Application (ClaudeCode)
    └── GroqTavilySearchAgent      └── ClaudeCodeTavilySearchAgent
              │                         │
              └─────────────────────────┘
                          │
                          ▼
              Phase 5: Integration & Documentation
                  └── エージェント登録, 統合テスト, README更新
```

**依存関係**:
- Phase 2 → Phase 1（TavilyAPIClientが必要）
- Phase 3 → Phase 2（TavilyToolsRepositoryMixinが必要）
- Phase 4 → Phase 2（TavilyToolsRepositoryMixinが必要）
- Phase 5 → Phase 3, 4（両エージェントが必要）

**並列実行可能**: Phase 3とPhase 4は並列実行可能

### Phase 1: Infrastructure Layer (TavilyAPIClient)

**目的**: Tavily公式APIとの通信を担当するラッパークラス

**新規ファイル**:
- `src/mixseek_plus/providers/tavily_client.py`
- `tests/unit/test_tavily_client.py`

**主要コンポーネント**:
- `TavilyAPIClient`: search, extract, get_search_contextメソッド
- HTTPエラー → TavilyAPIError変換
- リトライロジック（指数バックオフ）

### Phase 2: Domain Layer (TavilyToolsRepositoryMixin)

**目的**: エージェントにTavilyツールを登録するMixin

**新規ファイル**:
- `src/mixseek_plus/agents/mixins/tavily_tools.py`
- `tests/unit/test_tavily_tools_mixin.py`

**主要コンポーネント**:
- `TavilyToolsRepositoryMixin`: register_tavily_tools()メソッド
- 3つのツール実装: `tavily_search`, `tavily_extract`, `tavily_context`

### Phase 3: Application Layer - Groq

**目的**: Groqモデル + Tavilyツールのエージェント

**新規ファイル**:
- `src/mixseek_plus/agents/groq_tavily_search_agent.py`
- `tests/unit/test_groq_tavily_search_agent.py`

**主要コンポーネント**:
- `GroqTavilySearchAgent`: BaseGroqAgent + TavilyToolsRepositoryMixin
- `GroqTavilySearchDeps`: 依存性注入用dataclass

### Phase 4: Application Layer - ClaudeCode

**目的**: ClaudeCodeモデル + Tavilyツールのエージェント

**新規ファイル**:
- `src/mixseek_plus/agents/claudecode_tavily_search_agent.py`
- `tests/unit/test_claudecode_tavily_search_agent.py`

**主要コンポーネント**:
- `ClaudeCodeTavilySearchAgent`: BaseClaudeCodeAgent + TavilyToolsRepositoryMixin
- MCP統合（PlaywrightMarkdownFetchAgentパターン準拠）

### Phase 5: Integration & Documentation

**目的**: エージェント登録、統合テスト、ドキュメント更新

**更新ファイル**:
- `src/mixseek_plus/agents/__init__.py`: register_tavily_agents()
- `src/mixseek_plus/agents/mixins/__init__.py`: エクスポート追加
- `src/mixseek_plus/errors.py`: TavilyAPIError追加
- `src/mixseek_plus/types.py`: TypedDict追加

**新規ファイル**:
- `tests/integration/test_tavily_search_integration.py`

**ドキュメント更新**:
- README.md: Tavily検索エージェントの使用例追加

## Complexity Tracking

> **No violations to justify**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Risk Mitigation

| リスク | 影響 | 対策 |
|--------|------|------|
| Tavily APIレート制限 | 429エラー | 指数バックオフリトライ + エラーハンドリング |
| APIキー漏洩 | セキュリティ | 環境変数のみ使用、コード内ハードコード禁止 |
| 後方互換性破壊 | 既存ユーザー影響 | groq_web_searchは完全維持、別エージェントタイプ追加 |
| ClaudeCode MCP統合失敗 | 機能不全 | 既存PlaywrightMarkdownFetchAgentパターン踏襲 |

## Dependencies

### 外部ライブラリ

| ライブラリ | バージョン | 用途 |
|-----------|----------|------|
| tavily-python | >=0.7.4 | Tavily公式Pythonクライアント |
| pydantic-ai | >=1.44.0 | エージェントフレームワーク |
| claudecode-model | (プロジェクト依存) | ClaudeCodeモデル連携 |

### 内部依存

| モジュール | 用途 |
|-----------|------|
| mixseek-core | BaseMemberAgent, MemberAgentConfig, MemberAgentFactory |
| BaseGroqAgent | Groqエージェント基底クラス |
| BaseClaudeCodeAgent | ClaudeCodeエージェント基底クラス |
| PydanticAgentExecutorMixin | 共通実行ロジック |
| MemberAgentLogger | ログ出力 |
