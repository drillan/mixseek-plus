# Tasks: ClaudeCodeプロバイダーのサポート追加

**Input**: Design documents from `/specs/008-claudecode-provider/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: TDDワークフローに従い、単体テスト・統合テストを含む（spec.md Test Strategy参照）

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/mixseek_plus/`, `tests/` at repository root
- Paths follow existing Groq provider structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and provider constants

- [X] T001 Define `CLAUDECODE_PROVIDER_PREFIX = "claudecode:"` in `src/mixseek_plus/providers/__init__.py`
- [X] T002 [P] Add `ClaudeCodeNotPatchedError` exception class in `src/mixseek_plus/errors.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create `src/mixseek_plus/providers/claudecode.py` with `create_claudecode_model()` function
- [X] T004 Add `claudecode:` routing in `src/mixseek_plus/model_factory.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Python APIでのClaudeCodeモデル作成 (Priority: P1) 🎯 MVP

**Goal**: `mixseek_plus.create_model("claudecode:claude-sonnet-4-5")` がClaudeCodeModelインスタンスを返す

**Independent Test**: `create_model()` を呼び出してClaudeCodeModelインスタンスが返されることで検証

**Mapped Requirements**: CC-001, CC-010, CC-011, CC-020, CC-021, CC-060, CC-062

### Tests for User Story 1 (TDD: Write FIRST, ensure FAIL)

- [X] T005 [P] [US1] Unit test for `create_claudecode_model()` in `tests/unit/test_claudecode_provider.py`
- [X] T006 [P] [US1] Unit test for `claudecode:` routing in `tests/unit/test_model_factory.py`

### Implementation for User Story 1

- [X] T007 [US1] Implement `create_claudecode_model()` function in `src/mixseek_plus/providers/claudecode.py`
- [X] T008 [US1] Add `claudecode:` routing logic in `src/mixseek_plus/model_factory.py`
- [X] T009 [US1] Export `create_model` and `create_claudecode_model` from `src/mixseek_plus/__init__.py`

**Checkpoint**: User Story 1 should be fully functional - `create_model("claudecode:...")` works

---

## Phase 4: User Story 2 - ClaudeCodePlainAgent Member Agentでの利用 (Priority: P1)

**Goal**: TOML設定で `type = "claudecode_plain"` を指定してMember Agentとしてタスクを実行できる

**Independent Test**: `type = "claudecode_plain"` のMember Agent設定でタスクが正常に実行される

**Mapped Requirements**: CC-030, CC-031, CC-032, CC-033, CC-034, CC-061, CC-070, CC-071

### Tests for User Story 2 (TDD: Write FIRST, ensure FAIL)

- [X] T010 [P] [US2] Unit test for `BaseClaudeCodeAgent` base class in `tests/unit/test_base_claudecode_agent.py`
- [X] T011 [P] [US2] Unit test for `ClaudeCodePlainAgent` in `tests/unit/test_claudecode_plain_agent.py`
- [X] T012 [P] [US2] Unit test for agent factory registration in `tests/unit/test_agent_factory_registration.py`

### Implementation for User Story 2

- [X] T013 [P] [US2] Create `BaseClaudeCodeAgent` base class in `src/mixseek_plus/agents/base_claudecode_agent.py`
- [X] T014 [US2] Create `ClaudeCodePlainAgent` in `src/mixseek_plus/agents/claudecode_agent.py`
- [X] T015 [US2] Add `register_claudecode_agents()` function in `src/mixseek_plus/agents/__init__.py`
- [X] T016 [US2] Export `ClaudeCodePlainAgent` from `src/mixseek_plus/__init__.py`

**Checkpoint**: User Story 2 should be fully functional - `type = "claudecode_plain"` works

---

## Phase 5: User Story 3 - Leader/EvaluatorでのClaudeCode利用 (Priority: P2)

**Goal**: `patch_core()` 呼び出し後、Leader/Evaluator設定で `claudecode:` モデルが使用可能

**Independent Test**: `patch_core()` 後、Leader/Evaluator設定で `model = "claudecode:..."` が動作

**Mapped Requirements**: CC-050, CC-051, CC-052

### Tests for User Story 3 (TDD: Write FIRST, ensure FAIL)

- [X] T017 [P] [US3] Unit test for `patch_core()` ClaudeCode extension in `tests/unit/test_patch_core.py`
- [X] T018 [P] [US3] Unit test for unpatched detection in `tests/unit/test_unpatched_detection.py`

### Implementation for User Story 3

- [X] T019 [US3] Extend `patch_core()` to support `claudecode:` prefix in `src/mixseek_plus/core_patch.py`
- [X] T020 [US3] Add `ClaudeCodeNotPatchedError` handling for unpatched usage

**Checkpoint**: User Story 3 should be fully functional - Leader/Evaluator with ClaudeCode works

---

## Phase 6: User Story 4 - CLIでのClaudeCode利用 (Priority: P1)

**Goal**: `mixseek exec` コマンドでClaudeCode設定のTOMLを実行できる

**Independent Test**: `mixseek exec --config claudecode-config.toml` が正常に動作

**Mapped Requirements**: CC-052 (CLI auto-patch)

### Tests for User Story 4 (TDD: Write FIRST, ensure FAIL)

- [X] T021 [P] [US4] Unit test for CLI ClaudeCode auto-patch in `tests/unit/test_cli.py`

### Implementation for User Story 4

- [X] T022 [US4] Add ClaudeCode agent registration in CLI entrypoint `src/mixseek_plus/cli.py`

**Checkpoint**: User Story 4 should be fully functional - CLI with ClaudeCode works

---

## Phase 7: User Story 5 - ツール設定のカスタマイズ (Priority: P2)

**Goal**: TOML設定で `[members.tool_settings.claudecode]` セクションを使ってツール設定をカスタマイズできる

**Independent Test**: `tool_settings.claudecode` の設定が `ClaudeCodePlainAgent` に反映される

**Mapped Requirements**: CC-040, CC-041, CC-042, CC-043

### Tests for User Story 5 (TDD: Write FIRST, ensure FAIL)

- [X] T023 [P] [US5] Unit test for tool_settings parsing in `tests/unit/test_claudecode_plain_agent.py`

### Implementation for User Story 5

- [X] T024 [US5] Implement `ClaudeCodeToolSettings` parsing in `ClaudeCodePlainAgent` constructor
- [X] T025 [US5] Pass tool_settings to `ClaudeCodeModel` constructor

**Checkpoint**: User Story 5 should be fully functional - tool_settings customization works

---

## Phase 8: Integration Tests

**Purpose**: End-to-end validation with real Claude Code CLI

### Integration Tests

- [X] T026 [P] Integration test for model creation in `tests/integration/test_claudecode_api.py`
- [X] T027 [P] Integration test for agent execution in `tests/integration/test_claudecode_agent_execution.py`
- [X] T028 [P] Integration test for CLI in `tests/integration/test_cli_claudecode.py`

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 Verify all public exports in `src/mixseek_plus/__init__.py`
- [X] T030 Run `uv run ruff check --fix . && uv run ruff format . && uv run mypy .`
- [X] T031 Run full test suite `uv run pytest`
- [X] T032 Run quickstart.md validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (Phase 3): No dependencies on other stories
  - US2 (Phase 4): Depends on US1 (uses `create_claudecode_model()`)
  - US3 (Phase 5): Depends on US2 (needs agent infrastructure)
  - US4 (Phase 6): Depends on US2, US3 (registers agents and patches)
  - US5 (Phase 7): Depends on US2 (extends `ClaudeCodePlainAgent`)
- **Integration Tests (Phase 8)**: Depends on all user story implementation
- **Polish (Phase 9)**: Depends on all phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundation → US1 完了後、`create_model()` が動作
- **User Story 2 (P1)**: US1 → US2 完了後、`ClaudeCodePlainAgent` が動作
- **User Story 3 (P2)**: US2 → US3 完了後、Leader/Evaluator が動作
- **User Story 4 (P1)**: US2+US3 → US4 完了後、CLI が動作
- **User Story 5 (P2)**: US2 → US5 完了後、tool_settings が動作

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T001-T002) can run in parallel
- All tests for a user story marked [P] can run in parallel
- Integration tests (T026-T028) can run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task: "Unit test for BaseClaudeCodeAgent in tests/unit/test_base_claudecode_agent.py"
Task: "Unit test for ClaudeCodePlainAgent in tests/unit/test_claudecode_plain_agent.py"
Task: "Unit test for agent factory registration in tests/unit/test_agent_factory_registration.py"

# After tests fail, launch base class:
Task: "Create BaseClaudeCodeAgent in src/mixseek_plus/agents/base_claudecode_agent.py"

# Then sequential implementation:
Task: "Create ClaudeCodePlainAgent in src/mixseek_plus/agents/claudecode_agent.py"
Task: "Add register_claudecode_agents() in src/mixseek_plus/agents/__init__.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Python API)
4. **STOP and VALIDATE**: Test `create_model("claudecode:...")` works

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → `create_model()` works (MVP!)
3. Add User Story 2 → Test independently → `ClaudeCodePlainAgent` works
4. Add User Story 4 → Test independently → CLI works
5. Add User Story 3 → Test independently → Leader/Evaluator works
6. Add User Story 5 → Test independently → tool_settings works
7. Integration Tests + Polish → Release ready

### Priority Adjustment Note

User Story 4 (CLI) depends on US2 and US3, but is marked P1 in spec.md.
Recommended execution order: US1 → US2 → US3 → US4 → US5 to satisfy dependencies.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD: Write tests FIRST, ensure they FAIL, then implement
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Reference: Groq provider implementation in `specs/003-groq-provider/`
