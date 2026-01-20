# Tasks: ClaudeCodeModel固有のロギング・オブザーバビリティ

**Input**: Design documents from `/specs/033-claudecode-logging/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Tests are included as TDD is required per project constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/mixseek_plus/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and new module structure

- [x] T001 Create `src/mixseek_plus/utils/` directory structure if not exists
- [x] T002 [P] Create `src/mixseek_plus/observability/` directory with `__init__.py`
- [x] T003 [P] Verify mixseek-core `MemberAgentLogger` availability and interface

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement `_is_verbose_mode()` helper function in `src/mixseek_plus/core_patch.py`
- [x] T005 [P] Implement `_is_logfire_mode()` helper function in `src/mixseek_plus/core_patch.py`
- [x] T006 Verify existing `--verbose` and `--logfire` CLI options work with mixseek-core

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - MCPツール呼び出しのログ確認 (Priority: P1) 🎯 MVP

**Goal**: ClaudeCodeModelを使用するエージェントがMCPツールを呼び出した際に、ログで確認可能にする

**Independent Test**: ClaudeCodeModelでMCPツールを呼び出し、ログファイルに適切な情報が記録されることを確認

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [P] [US1] Unit test for `_wrap_tool_function_for_mcp()` logging in `tests/unit/test_core_patch_logging.py`
- [x] T008 [P] [US1] Unit test for `PlaywrightMarkdownFetchAgent` MCP tool logging in `tests/unit/test_playwright_agent_logging.py`

### Implementation for User Story 1

- [x] T009 [US1] Add `time.perf_counter()` timing and `log_tool_invocation()` call to `_wrap_tool_function_for_mcp()` in `src/mixseek_plus/core_patch.py`
- [x] T010 [US1] Add logging to `_wrap_tool_for_mcp()` in `src/mixseek_plus/agents/playwright_markdown_fetch_agent.py`
- [x] T011 [US1] Ensure `execution_id` is passed through `TeamDependencies` for log correlation in `src/mixseek_plus/core_patch.py`
- [x] T012 [US1] Verify automatic secret masking via `MemberAgentLogger._sanitize_parameters()` works correctly

**Checkpoint**: At this point, User Story 1 should be fully functional - MCP tool calls are logged with timing, status, and sanitized parameters

---

## Phase 4: User Story 2 - Verboseモードでの詳細ログ確認 (Priority: P2)

**Goal**: `--verbose`オプションで詳細ログを確認可能にする

**Independent Test**: `MIXSEEK_VERBOSE=1`でエージェントを実行し、詳細ログがコンソールとファイルに出力されることを確認

### Tests for User Story 2 ⚠️

- [x] T013 [P] [US2] Unit test for `ClaudeCodeToolCallExtractor.extract_tool_calls()` in `tests/unit/test_claudecode_logging.py`
- [x] T014 [P] [US2] Unit test for `_log_tool_calls_from_history()` in `tests/unit/test_base_claudecode_agent_logging.py`

### Implementation for User Story 2

- [x] T015 [US2] Create `src/mixseek_plus/utils/claudecode_logging.py` with `ClaudeCodeToolCallExtractor` class
- [x] T016 [US2] Implement `extract_tool_calls()` method to extract `ToolCallPart`/`ToolReturnPart` from pydantic-ai messages
- [x] T017 [US2] Implement `_summarize_args()` method with 100-char limit in `src/mixseek_plus/utils/claudecode_logging.py`
- [x] T018 [US2] Implement `_summarize_result()` method with 200-char limit in `src/mixseek_plus/utils/claudecode_logging.py`
- [x] T019 [US2] Add `_log_tool_calls_from_history()` method to `src/mixseek_plus/agents/base_claudecode_agent.py`
- [x] T020 [US2] Add verbose console output (conditional on `_is_verbose_mode()`) in `src/mixseek_plus/core_patch.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - verbose mode shows detailed console logs with truncated args/results

---

## Phase 5: User Story 3 - Logfireによるオブザーバビリティ統合 (Priority: P3)

**Goal**: `--logfire`オプションでpydantic-ai自動インストルメンテーションを有効化

**Independent Test**: `MIXSEEK_LOGFIRE=1`と`logfire`パッケージインストール状態でエージェントを実行し、Logfireにデータが送信されることを確認

### Tests for User Story 3 ⚠️

- [x] T021 [P] [US3] Unit test for `setup_logfire_instrumentation()` in `tests/unit/test_logfire_integration.py`
- [x] T022 [P] [US3] Unit test for logfire package not installed warning in `tests/unit/test_logfire_integration.py`

### Implementation for User Story 3

- [x] T023 [US3] Create `src/mixseek_plus/observability/logfire_integration.py` with `setup_logfire_instrumentation()` function
- [x] T024 [US3] Implement optional import check for `logfire` package with graceful fallback
- [x] T025 [US3] Implement warning message when `--logfire` is specified but package not installed
- [x] T026 [US3] Add pydantic-ai auto-instrumentation setup via `logfire.instrument_pydantic_ai()` (if available)
- [x] T027 [US3] Export `setup_logfire_instrumentation` from `src/mixseek_plus/observability/__init__.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T028 [P] Update `src/mixseek_plus/utils/__init__.py` to export `ClaudeCodeToolCallExtractor`
- [x] T029 [P] Add `logfire` to optional dependencies in `pyproject.toml` under `[project.optional-dependencies]`
- [x] T030 Run `uv run ruff check --fix . && uv run ruff format . && uv run mypy .` for code quality
- [x] T031 Run `uv run pytest` to verify all tests pass
- [x] T032 Run quickstart.md validation (manual test with `--verbose` and `--logfire` options)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories should proceed sequentially in priority order (P1 → P2 → P3)
  - P2 and P3 can start in parallel if staffed, but P1 is the MVP
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1 logging infrastructure but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent from US1/US2, only depends on environment variables

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Helper functions/utilities before main implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003 can run in parallel (different directories/concerns)
- T004, T005 can run in parallel (different helper functions, same file - but independent)
- T007, T008 can run in parallel (different test files)
- T013, T014 can run in parallel (different test files)
- T021, T022 can run in parallel (same test file, different test cases)
- T028, T029 can run in parallel (different files)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for _wrap_tool_function_for_mcp() logging in tests/unit/test_core_patch_logging.py"
Task: "Unit test for PlaywrightMarkdownFetchAgent MCP tool logging in tests/unit/test_playwright_agent_logging.py"

# After tests fail, implement sequentially:
Task: "Add time.perf_counter() timing and log_tool_invocation() call to _wrap_tool_function_for_mcp()"
Task: "Add logging to _wrap_tool_for_mcp() in playwright_markdown_fetch_agent.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD Red-Green-Refactor)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
