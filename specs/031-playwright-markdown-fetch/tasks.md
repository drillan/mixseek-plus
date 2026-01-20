# Tasks: Playwright + MarkItDown統合Webフェッチャー

**Input**: Design documents from `/specs/031-playwright-markdown-fetch/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: テストは `/speckit.implement` 実行時にTDDワークフローで作成される想定。

**Organization**: タスクはUser Story単位でグループ化されており、各Storyは独立して実装・テスト可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: User Story番号（例: US1, US2, US3）
- 説明には正確なファイルパスを含む

## Path Conventions

- **Single project**: `src/mixseek_plus/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: プロジェクト初期化と依存関係追加

- [X] T001 pyproject.tomlに`[playwright]`オプション依存関係を追加 (`playwright>=1.50.0`, `markitdown>=0.1.4`)
- [X] T002 [P] `src/mixseek_plus/errors.py`にPlaywright関連エラークラス追加 (`PlaywrightNotInstalledError`, `FetchError`, `ConversionError`)
- [X] T003 [P] `src/mixseek_plus/agents/__init__.py`にPlaywrightエージェントのexportスタブ追加

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 全User Storyで共通利用する基盤コンポーネント

**⚠️ CRITICAL**: このフェーズ完了まで User Story 実装は開始不可

- [X] T004 `src/mixseek_plus/agents/base_playwright_agent.py`に`PlaywrightConfig`モデル作成（headless, timeout_ms, wait_for_load_state, retry_count, retry_delay_ms, block_resources）
- [X] T005 `src/mixseek_plus/agents/base_playwright_agent.py`に`FetchResult`データクラス作成
- [X] T006 `src/mixseek_plus/agents/base_playwright_agent.py`に`BasePlaywrightAgent`基底クラス作成（ブラウザライフサイクル管理、`_ensure_browser()`, `close()`）
- [X] T007 `src/mixseek_plus/agents/base_playwright_agent.py`に`_check_playwright_available()`関数追加（インポート確認、明確なエラーメッセージ）
- [X] T008 `tests/conftest.py`にPlaywright用fixtureを追加（モックブラウザ、テスト設定）

**Checkpoint**: 基盤準備完了 - User Story実装開始可能

---

## Phase 3: User Story 1 - 基本的なWebページ取得とMarkdown変換 (Priority: P1) 🎯 MVP

**Goal**: `type = "playwright_markdown_fetch"`でエージェントを設定し、WebページをMarkdown形式で取得できる

**Independent Test**: 静的サイト（例：docs.python.org）からコンテンツを取得してMarkdown形式で返却される

### Implementation for User Story 1

- [X] T009 [US1] `src/mixseek_plus/agents/base_playwright_agent.py`に`_fetch_page(url)`メソッド実装（ページ取得、HTML取得）
- [X] T010 [US1] `src/mixseek_plus/agents/base_playwright_agent.py`に`_convert_to_markdown(html)`メソッド実装（MarkItDown使用）
- [X] T011 [US1] `src/mixseek_plus/agents/playwright_markdown_fetch_agent.py`に`PlaywrightMarkdownFetchAgent`クラス作成（`BasePlaywrightAgent`継承、任意モデル対応）
- [X] T012 [US1] `src/mixseek_plus/agents/playwright_markdown_fetch_agent.py`に`fetch_page`ツール定義（pydantic-ai Tool）
- [X] T013 [US1] `src/mixseek_plus/agents/playwright_markdown_fetch_agent.py`に`execute()`メソッド実装（LLMとfetch_pageツール統合）
- [X] T014 [US1] `src/mixseek_plus/agents/__init__.py`に`register_playwright_agents()`関数作成（MemberAgentFactory登録）
- [X] T015 [US1] `src/mixseek_plus/__init__.py`に`PlaywrightMarkdownFetchAgent`, `register_playwright_agents`をexport追加
- [X] T016 [US1] 無効なURL（存在しないドメイン）に対する適切なエラーハンドリング追加

**Checkpoint**: User Story 1完了 - 基本的なWebページ取得とMarkdown変換が独立して動作

---

## Phase 4: User Story 2 - ボット対策サイトからのコンテンツ取得 (Priority: P2)

**Goal**: `headless = false`でCloudflare等のボット対策を回避してコンテンツ取得

**Independent Test**: headedモードでCloudflare保護サイトにアクセスし、403ではなくコンテンツ取得可能

### Implementation for User Story 2

- [X] T017 [US2] `src/mixseek_plus/agents/base_playwright_agent.py`の`_ensure_browser()`でheadless設定を適用
- [X] T018 [US2] headlessモードでブロックされた場合のログ記録機能追加

**Checkpoint**: User Story 2完了 - headed/headlessモード切替が独立して動作

---

## Phase 5: User Story 3 - 設定可能なタイムアウトと待機条件 (Priority: P3)

**Goal**: タイムアウト（`timeout_ms`）と待機条件（`wait_for_load_state`）を設定可能

**Independent Test**: `timeout_ms = 60000`と`wait_for_load_state = "networkidle"`を設定し、SPAサイトから完全なコンテンツ取得

### Implementation for User Story 3

- [X] T019 [US3] `src/mixseek_plus/agents/base_playwright_agent.py`の`_fetch_page()`で`timeout_ms`設定を適用
- [X] T020 [US3] `src/mixseek_plus/agents/base_playwright_agent.py`の`_fetch_page()`で`wait_for_load_state`設定を適用（load/domcontentloaded/networkidle）
- [X] T021 [US3] タイムアウト発生時の明確なエラーメッセージ実装

**Checkpoint**: User Story 3完了 - タイムアウトと待機条件設定が独立して動作

---

## Phase 6: User Story 4 - HTTPリトライ機能 (Priority: P4)

**Goal**: 一時的なネットワーク障害に対して指数バックオフでリトライ

**Independent Test**: `retry_count = 3`設定で、最初の2回503→3回目成功のシナリオをテスト

### Implementation for User Story 4

- [X] T022 [US4] `src/mixseek_plus/agents/base_playwright_agent.py`に`_fetch_with_retry(url)`メソッド実装（指数バックオフ: delay * 2^attempt）
- [X] T023 [US4] リトライ対象エラー判定ロジック実装（503、接続エラー等）
- [X] T024 [US4] 全リトライ失敗時のエラーメッセージに試行回数を含める

**Checkpoint**: User Story 4完了 - HTTPリトライ機能が独立して動作

---

## Phase 7: User Story 5 - リソースブロック機能 (Priority: P5)

**Goal**: 画像/フォント等の不要リソースをブロックして高速化

**Independent Test**: `block_resources = ["image", "font"]`設定で画像が多いページでも高速取得

### Implementation for User Story 5

- [X] T025 [US5] `src/mixseek_plus/agents/base_playwright_agent.py`に`_setup_resource_blocking(page)`メソッド実装（route.abort使用）
- [X] T026 [US5] `_fetch_page()`で`_setup_resource_blocking()`を呼び出し

**Checkpoint**: User Story 5完了 - リソースブロック機能が独立して動作

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 全User Storyに影響する改善

- [X] T027 [P] Edge Case対応: JavaScriptエラーページのDOMからコンテンツ取得
- [X] T028 [P] Edge Case対応: リダイレクト発生時の最終URL取得
- [X] T029 [P] Edge Case対応: 空のページ（body空）の警告メッセージ
- [X] T030 [P] Edge Case対応: 非HTMLコンテンツ（PDF、JSON）のエラーメッセージ
- [X] T031 品質チェック実行: `uv run ruff check --fix . && uv run ruff format . && uv run mypy .`
- [ ] T032 quickstart.md検証: サンプルコードの動作確認

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし - 即時開始可能
- **Foundational (Phase 2)**: Setup完了後 - 全User Storyをブロック
- **User Stories (Phase 3-7)**: Foundational完了後
  - User Story 1 (P1): 基盤 → MVP
  - User Story 2-5 (P2-P5): US1完了後、順次または並列実行可能
- **Polish (Phase 8)**: 全User Story完了後

### User Story Dependencies

- **User Story 1 (P1)**: Foundational完了後 - 他Storyに依存なし → MVP
- **User Story 2 (P2)**: US1完了後 - `_ensure_browser()`の拡張
- **User Story 3 (P3)**: US1完了後 - `_fetch_page()`の拡張
- **User Story 4 (P4)**: US1完了後 - 独立した`_fetch_with_retry()`メソッド
- **User Story 5 (P5)**: US1完了後 - 独立した`_setup_resource_blocking()`メソッド

### Within Each User Story

- コアロジック → エラーハンドリング → 統合
- 各タスク完了後にコミット

### Parallel Opportunities

- Setup内のT002, T003は並列実行可能
- Foundational内は順次（T004→T005→T006→T007）
- User Story 2-5はUS1完了後、並列実行可能（異なるメソッド実装）
- Polish内のT027-T030は並列実行可能

---

## Parallel Example: Setup Phase

```bash
# Setup Phase - 並列実行可能なタスク:
Task: T002 "errors.pyにPlaywright関連エラークラス追加"
Task: T003 "agents/__init__.pyにexportスタブ追加"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup完了
2. Phase 2: Foundational完了（CRITICAL）
3. Phase 3: User Story 1完了
4. **STOP and VALIDATE**: 静的サイトでMarkdown取得テスト
5. MVP完了 → デモ/デプロイ可能

### Incremental Delivery

1. Setup + Foundational → 基盤準備完了
2. User Story 1 → 基本Webフェッチ → MVP!
3. User Story 2 → headedモード対応 → ボット対策回避
4. User Story 3 → タイムアウト/待機条件 → SPA対応
5. User Story 4 → リトライ機能 → 信頼性向上
6. User Story 5 → リソースブロック → パフォーマンス最適化
7. Polish → Edge Case対応 → 完成

---

## Notes

- [P] タスク = 異なるファイル、依存関係なし
- [Story] ラベルでUser Storyへのトレーサビリティ確保
- 各User Storyは独立して完了・テスト可能
- タスク完了毎または論理グループ毎にコミット
- チェックポイントで独立検証可能
