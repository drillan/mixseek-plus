# Tasks: Groqプロバイダーのサポート追加

**Input**: Design documents from `/specs/003-groq-provider/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: テストはTDD必須のため含む（CLAUDE.mdの「TDD必須」に準拠）

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**現状**:
- Phase 1-7完了。全ての要件（GR-001〜GR-073）が実装済み
- **完了**: GR-063（未パッチ時エラーメッセージ）とGR-032（詳細APIエラー）がPhase 7で実装完了

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure - 完了済み

実装済みのファイル（確認用）:
- `src/mixseek_plus/__init__.py` - パッケージエクスポート
- `src/mixseek_plus/errors.py` - ModelCreationError例外
- `src/mixseek_plus/model_factory.py` - create_model()実装
- `src/mixseek_plus/providers/groq.py` - Groqモデル作成
- `src/mixseek_plus/providers/__init__.py` - プロバイダー定数
- `src/mixseek_plus/agents/groq_agent.py` - GroqPlainAgent（基本実装）

**Status**: ✅ 完了（GR-001〜GR-003, GR-010〜GR-012, GR-020〜GR-022, GR-030〜GR-031, GR-040）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before remaining user stories can be implemented

- [X] T001 Create test fixtures and conftest.py in tests/conftest.py
- [X] T002 [P] Create unit test base structure in tests/unit/__init__.py
- [X] T003 [P] Create integration test base structure in tests/integration/__init__.py

**Checkpoint**: ✅ テスト基盤準備完了 - User Story実装開始可能

---

## Phase 3: User Story 5 - Member AgentでのGroq利用 (Priority: P1) 🎯 MVP

**Goal**: GroqPlainAgent/GroqWebSearchAgentをMemberAgentFactoryに登録し、TOML設定から利用可能にする

**Independent Test**: `type = "groq_plain"` または `type = "groq_web_search"` でTOML設定を作成し、タスクが正常に実行されることで検証

**要件**: GR-050, GR-051, GR-052, GR-053, GR-054

### Tests for User Story 5 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T004 [P] [US5] Unit test for GroqPlainAgent in tests/unit/test_groq_plain_agent.py
- [X] T005 [P] [US5] Unit test for GroqWebSearchAgent in tests/unit/test_groq_web_search_agent.py
- [X] T006 [P] [US5] Unit test for Factory registration in tests/unit/test_agent_factory_registration.py
- [X] T007 [P] [US5] Integration test for GroqPlainAgent execution in tests/integration/test_groq_agent_execution.py

### Implementation for User Story 5

- [X] T008 [US5] Complete GroqPlainAgent implementation with execute() method in src/mixseek_plus/agents/groq_agent.py
- [X] T009 [US5] Implement GroqWebSearchAgent with WebSearchTool in src/mixseek_plus/agents/groq_web_search_agent.py
- [X] T010 [US5] Implement Factory registration function in src/mixseek_plus/agents/__init__.py
- [X] T011 [US5] Add GroqAgentDeps dataclass refinement in src/mixseek_plus/agents/groq_agent.py
- [X] T012 [US5] Update __init__.py exports for GroqPlainAgent, GroqWebSearchAgent in src/mixseek_plus/__init__.py

**Checkpoint**: ✅ Member Agent機能がTOML設定から利用可能

---

## Phase 4: User Story 6 - Leader/EvaluatorでのGroq利用 (Priority: P2)

**Goal**: patch_core()関数でLeader/EvaluatorのGroq対応を実現

**Independent Test**: `mixseek_plus.patch_core()` 後、Leader/Evaluator設定で `model = "groq:..."` が動作することで検証

**要件**: GR-060, GR-061, GR-062, GR-063, GR-041

### Tests for User Story 6 ⚠️

- [X] T013 [P] [US6] Unit test for patch_core() function in tests/unit/test_patch_core.py
- [X] T014 [P] [US6] Unit test for idempotency of patch_core() in tests/unit/test_patch_core.py
- [X] T015 [P] [US6] Unit test for unpatched error message in tests/unit/test_patch_core.py

### Implementation for User Story 6

- [X] T016 [US6] Implement patch_core() function in src/mixseek_plus/core_patch.py
- [X] T017 [US6] Add patch state tracking for idempotency in src/mixseek_plus/core_patch.py
- [X] T018 [US6] Add unpatched usage detection and error message in src/mixseek_plus/core_patch.py
- [X] T019 [US6] Export patch_core from __init__.py in src/mixseek_plus/__init__.py

**Checkpoint**: ✅ Leader/EvaluatorでGroqモデル利用可能

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T020 [P] Complete GR-032 API error wrapping in execute() methods in src/mixseek_plus/agents/groq_agent.py
- [X] T021 [P] Complete GR-032 API error wrapping in GroqWebSearchAgent in src/mixseek_plus/agents/groq_web_search_agent.py
- [X] T022 Run quickstart.md validation scenarios
- [X] T023 Run full test suite and quality checks (ruff, mypy, pytest)

---

## Phase 6: CLI統合 (User Story 7) - NEW

**Goal**: `mixseek`コマンドを上書きし、mixseek-plusインストールで自動的にGroq対応を有効化

**要件**: GR-070, GR-071, GR-072, GR-073

### Tests for User Story 7 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T024 [P] [US7] Unit test for CLI wrapper in tests/unit/test_cli.py

### Implementation for User Story 7

- [X] T025 [US7] Create CLI wrapper module in src/mixseek_plus/cli.py
- [X] T026 [US7] Add console_scripts entry point in pyproject.toml
- [X] T027 [US7] Integration test with Groq config via CLI

**Checkpoint**: ✅ `mixseek exec`でGroqモデルが使用可能

---

## Phase 7: ギャップ解消 (Spec-Implementation Alignment)

**Purpose**: spec.mdと実装のギャップを解消

**背景**: Phase 4-5でGR-063, GR-032は「完了」とマークされたが、実装確認の結果、以下のギャップが発見された：
- GR-063: 未パッチ時のエラーメッセージが未実装（is_patched()は存在するが、エラー検出・メッセージ表示機構がない）
- GR-032: 詳細なAPIエラーラップが不完全（429, 503の具体的なエラーメッセージがない）

**要件**: GR-063（完全実装）, GR-032（詳細エラーラップ）

### Tests for Gap Resolution ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T028 [P] [GAP] Unit test for unpatched groq: usage detection in tests/unit/test_unpatched_detection.py
  - groq:プレフィックス使用時にpatch_core()未呼び出しの場合、明確なエラーメッセージが表示されることを検証
  - エラーメッセージに「patch_core()を呼び出してください」等の案内が含まれることを検証

- [X] T029 [P] [GAP] Unit test for detailed API error handling in tests/unit/test_api_error_details.py
  - HTTP 429エラー時に「レート制限」を示すエラーメッセージが表示されることを検証
  - HTTP 503エラー時に「サービス一時停止」を示すエラーメッセージが表示されることを検証

### Implementation for Gap Resolution

- [X] T030 [GAP] Implement unpatched usage detection with helpful error message in src/mixseek_plus/core_patch.py
  - mixseek-coreのcreate_authenticated_modelがgroq:プレフィックスで呼ばれた場合の検出
  - 「mixseek_plus.patch_core()を呼び出してからgroq:モデルを使用してください」等のメッセージ

- [X] T031 [GAP] Implement detailed API error wrapping in src/mixseek_plus/agents/groq_agent.py
  - HTTP 429: "Groq API rate limit exceeded. Please wait and retry."
  - HTTP 503: "Groq service temporarily unavailable. Please try again later."

- [X] T032 [GAP] Implement detailed API error wrapping in src/mixseek_plus/agents/groq_web_search_agent.py
  - T031と同様のエラーハンドリングをGroqWebSearchAgentにも適用

**Checkpoint**: ✅ spec.mdの全要件が実装と一致

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: ✅ 完了済み
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 5 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **User Story 6 (Phase 4)**: Depends on Foundational (Phase 2) completion - 独立して実装可能
- **Polish (Phase 5)**: Depends on all user stories being complete
- **Gap Resolution (Phase 7)**: Depends on Phase 5 completion - spec.mdと実装の整合性確保

### User Story Dependencies

- **User Story 5 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 6 (P2)**: Can start after Foundational (Phase 2) - No dependencies on US5

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Foundational tasks marked [P] can run in parallel (T002, T003)
- All tests for US5 marked [P] can run in parallel (T004, T005, T006, T007)
- All tests for US6 marked [P] can run in parallel (T013, T014, T015)
- User Story 5 and User Story 6 can be worked on in parallel by different team members (after Foundational completion)
- Polish phase tasks marked [P] can run in parallel (T020, T021)
- Gap Resolution tests marked [P] can run in parallel (T028, T029)
- T031 and T032 can run in parallel (異なるファイルのエラーハンドリング実装)

---

## Parallel Example: User Story 5

```bash
# Launch all tests for User Story 5 together:
Task: "Unit test for GroqPlainAgent in tests/unit/test_groq_plain_agent.py"
Task: "Unit test for GroqWebSearchAgent in tests/unit/test_groq_web_search_agent.py"
Task: "Unit test for Factory registration in tests/unit/test_agent_factory_registration.py"
Task: "Integration test for GroqPlainAgent execution in tests/integration/test_groq_agent_execution.py"
```

---

## Implementation Strategy

### MVP First (User Story 5 Only)

1. Complete Phase 2: Foundational (test infrastructure)
2. Complete Phase 3: User Story 5 (Member Agent統合)
3. **STOP and VALIDATE**: Test Member Agent機能が独立して動作
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Foundational → テスト基盤準備完了
2. Add User Story 5 → Test independently → Demo (MVP!)
   - GroqPlainAgent/GroqWebSearchAgentがTOML設定から利用可能
3. Add User Story 6 → Test independently → Demo
   - Leader/Evaluatorでもgroq:モデルが利用可能
4. Add Polish → Full validation → Release

### Parallel Team Strategy

With multiple developers:

1. Team completes Foundational together
2. Once Foundational is done:
   - Developer A: User Story 5 (Member Agent)
   - Developer B: User Story 6 (patch_core)
3. Stories complete and integrate independently

---

## Requirement Traceability

| Req ID | Task IDs | Status |
|--------|----------|--------|
| GR-050 | T004, T008, T011 | ✅ DONE |
| GR-051 | T005, T009 | ✅ DONE |
| GR-052 | T008, T009 | ✅ DONE |
| GR-053 | T006, T010 | ✅ DONE |
| GR-054 | T006, T010 | ✅ DONE |
| GR-060 | T013, T016 | ✅ DONE |
| GR-061 | T016 | ✅ DONE |
| GR-062 | T014, T017 | ✅ DONE |
| GR-063 | T015, T018, T028, T030 | ✅ DONE |
| GR-041 | T019 | ✅ DONE |
| GR-042 | T012 | ✅ DONE |
| GR-032 | T020, T021, T029, T031, T032 | ✅ DONE |
| GR-070 | T025, T026 | ✅ DONE |
| GR-071 | T025 | ✅ DONE |
| GR-072 | T027 | ✅ DONE |
| GR-073 | T025 | ✅ DONE |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- GR-001〜GR-031, GR-040, GR-020〜GR-022 are already implemented (see plan.md)
