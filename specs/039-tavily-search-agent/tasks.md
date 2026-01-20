# Tasks: Tavily汎用検索エージェント

**Input**: Design documents from `/specs/039-tavily-search-agent/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [Markers] Description`

- **[TDD-RED]**: Test-First task (write failing test first)
- **[P]**: Can run in parallel (different files, no dependencies)
- **[US#]**: User story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## TDD Workflow (Constitution Article 1 - Non-Negotiable)

**すべてのPhaseは以下の順序で実行すること**:

1. **Red Phase**: テストタスク（[TDD-RED]マーク）を先に実行し、テストが失敗することを確認
2. **Green Phase**: 実装タスクを実行し、テストが成功することを確認
3. **Refactor Phase**: 必要に応じてリファクタリング

## Path Conventions

- **Single project**: `src/mixseek_plus/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure) ✅ COMPLETED

**Purpose**: Project initialization and basic structure

- [x] T001 Verify tavily-python dependency in pyproject.toml (>=0.7.4)
- [x] T002 [P] Add TavilyAPIError to src/mixseek_plus/errors.py
- [x] T003 [P] Add Tavily TypedDicts to src/mixseek_plus/types.py

---

## Phase 2: Foundational - Infrastructure Layer (TavilyAPIClient) ✅ COMPLETED

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### 2a. Test-First (Red Phase)

- [x] T004 [TDD-RED] Create unit tests for TavilyAPIClient in tests/unit/test_tavily_client.py
  - Test search() with mock response
  - Test extract() with mock response
  - Test get_search_context() with mock response
  - Test retry logic with mock failures (exponential backoff)
  - Test TavilySearchResult/TavilyExtractResult model validation
- [x] T005 [TDD-RED] Test TavilyAPIClient handles AUTH_ERROR (401) in tests/unit/test_tavily_client.py
- [x] T006 [TDD-RED] Test TavilyAPIClient handles RATE_LIMIT_ERROR (429) with retry in tests/unit/test_tavily_client.py
- [x] T007 [TDD-RED] Test TavilyAPIClient handles TIMEOUT_ERROR in tests/unit/test_tavily_client.py
- [x] T008 [TDD-RED] Test TavilyAPIClient handles VALIDATION_ERROR (400) in tests/unit/test_tavily_client.py

### 2b. Implementation (Green Phase)

- [x] T009 Create TavilySearchResult and TavilyExtractResult models in src/mixseek_plus/providers/tavily_client.py
- [x] T010 Implement TavilyAPIClient with search() method in src/mixseek_plus/providers/tavily_client.py
- [x] T011 Add extract() method to TavilyAPIClient in src/mixseek_plus/providers/tavily_client.py
- [x] T012 Add get_search_context() method to TavilyAPIClient in src/mixseek_plus/providers/tavily_client.py
- [x] T013 Implement exponential backoff retry logic in TavilyAPIClient in src/mixseek_plus/providers/tavily_client.py

**Checkpoint**: Infrastructure layer ready ✅
- [x] All T004-T008 tests pass (Green)
- [x] `uv run mypy src/mixseek_plus/providers/tavily_client.py` passes
- [x] TavilyAPIClient can be instantiated with valid API key

---

## Phase 3: Foundational - Domain Layer (TavilyToolsRepositoryMixin) ✅ COMPLETED

**Purpose**: Shared Mixin that provides Tavily tools to both Groq and ClaudeCode agents

**Depends on**: Phase 2 (TavilyAPIClient)

### 3a. Test-First (Red Phase)

- [x] T014 [TDD-RED] Create unit tests for TavilyToolsRepositoryMixin in tests/unit/test_tavily_tools_mixin.py
  - Test _register_tavily_tools() registers 3 tools
  - Test tavily_search tool returns formatted string per contracts/tavily-tools.md
  - Test tavily_extract tool returns formatted string per contracts/tavily-tools.md
  - Test tavily_context tool returns formatted string per contracts/tavily-tools.md
  - Test format_search_result matches contracts/tavily-tools.md section 2.4
  - Test format_extract_result matches contracts/tavily-tools.md section 3.4
- [x] T015 [TDD-RED] Test tavily_extract handles empty URL list with VALIDATION_ERROR in tests/unit/test_tavily_tools_mixin.py
- [x] T016 [TDD-RED] Test tavily_extract handles URL limit (>20) per NFR-004a in tests/unit/test_tavily_tools_mixin.py
- [x] T017 [TDD-RED] Test tavily_search returns "検索結果が見つかりませんでした" for 0 results in tests/unit/test_tavily_tools_mixin.py

### 3b. Implementation (Green Phase)

- [x] T018 Create TavilySearchDeps dataclass in src/mixseek_plus/agents/mixins/tavily_tools.py
- [x] T019 Create TavilyAgentProtocol in src/mixseek_plus/agents/mixins/tavily_tools.py
- [x] T020 Implement TavilyToolsRepositoryMixin._register_tavily_tools() with tavily_search tool in src/mixseek_plus/agents/mixins/tavily_tools.py
- [x] T021 Add tavily_extract tool to TavilyToolsRepositoryMixin in src/mixseek_plus/agents/mixins/tavily_tools.py
- [x] T022 Add tavily_context tool to TavilyToolsRepositoryMixin in src/mixseek_plus/agents/mixins/tavily_tools.py
- [x] T023 Add output formatting methods (format_search_result, format_extract_result) per contracts/tavily-tools.md in src/mixseek_plus/agents/mixins/tavily_tools.py
- [x] T024 [P] Export TavilyToolsRepositoryMixin in src/mixseek_plus/agents/mixins/__init__.py

**Checkpoint**: Foundation ready ✅
- [x] All T014-T017 tests pass (Green)
- [x] `uv run mypy src/mixseek_plus/agents/mixins/tavily_tools.py` passes
- [x] Output format matches contracts/tavily-tools.md sections 2.4, 3.4, 4.4

---

## Phase 4: User Story 1 - Groq版Tavily検索エージェントでWeb検索を実行 (Priority: P1) 🎯 MVP ✅ COMPLETED

**Goal**: Groqモデル + Tavily検索を組み合わせたエージェントでWeb検索を実行可能にする

**Independent Test**: TOML設定で`tavily_search`タイプのエージェントを定義し、検索クエリを送信して結果が返却されることを確認する

### 4a. Test-First (Red Phase)

- [x] T025 [TDD-RED] [US1] Create unit tests for GroqTavilySearchAgent in tests/unit/test_groq_tavily_search_agent.py
  - Test agent inherits BaseGroqAgent and TavilyToolsRepositoryMixin
  - Test _create_tavily_client() returns TavilyAPIClient with env API key
  - Test _create_deps() returns TavilySearchDeps
  - Test _get_agent_type_metadata() returns correct type info
  - Test agent registers 3 Tavily tools

### 4b. Implementation (Green Phase)

- [x] T026 [US1] Create GroqTavilySearchAgent class inheriting BaseGroqAgent and TavilyToolsRepositoryMixin in src/mixseek_plus/agents/groq_tavily_search_agent.py
- [x] T027 [US1] Implement _create_tavily_client() method in GroqTavilySearchAgent in src/mixseek_plus/agents/groq_tavily_search_agent.py
- [x] T028 [US1] Implement _create_deps() returning TavilySearchDeps in GroqTavilySearchAgent in src/mixseek_plus/agents/groq_tavily_search_agent.py
- [x] T029 [US1] Implement _get_agent_type_metadata() in GroqTavilySearchAgent in src/mixseek_plus/agents/groq_tavily_search_agent.py
- [x] T030 [US1] Register tavily_search agent type in factory via register_tavily_agents() in src/mixseek_plus/agents/__init__.py

**Checkpoint**: User Story 1 (Groq版Web検索) complete ✅
- [x] All T025 tests pass (Green)
- [x] `uv run mypy src/mixseek_plus/agents/groq_tavily_search_agent.py` passes
- [x] Factory creates GroqTavilySearchAgent for type="tavily_search"

---

## Phase 5: User Story 2 - ClaudeCode版Tavily検索エージェントでWeb検索を実行 (Priority: P1) ✅ COMPLETED

**Goal**: ClaudeCodeモデル + Tavily検索を組み合わせたエージェントでWeb検索を実行可能にする

**Independent Test**: TOML設定で`claudecode_tavily_search`タイプのエージェントを定義し、検索クエリを送信して結果が返却されることを確認する

### 5a. Test-First (Red Phase)

- [x] T031 [TDD-RED] [US2] Create unit tests for ClaudeCodeTavilySearchAgent in tests/unit/test_claudecode_tavily_search_agent.py
  - Test agent inherits BaseClaudeCodeAgent and TavilyToolsRepositoryMixin
  - Test _create_tavily_client() returns TavilyAPIClient with env API key
  - Test _create_deps() returns TavilySearchDeps
  - Test _get_agent_type_metadata() returns correct type info
  - Test agent registers 3 Tavily tools
- [x] T032 [TDD-RED] [US2] Test MCP tool naming convention (mcp__pydantic_tools__tavily_*) in tests/unit/test_claudecode_tavily_search_agent.py
- [x] T033 [TDD-RED] [US2] Test _wrap_tool_for_mcp() injects TavilySearchDeps correctly in tests/unit/test_claudecode_tavily_search_agent.py
- [x] T034 [TDD-RED] [US2] Test allowed_tools includes MCP tool names in tests/unit/test_claudecode_tavily_search_agent.py

### 5b. Implementation (Green Phase)

- [x] T035 [US2] Create ClaudeCodeTavilySearchAgent class inheriting BaseClaudeCodeAgent and TavilyToolsRepositoryMixin in src/mixseek_plus/agents/claudecode_tavily_search_agent.py
- [x] T036 [US2] Implement _create_tavily_client() method in ClaudeCodeTavilySearchAgent in src/mixseek_plus/agents/claudecode_tavily_search_agent.py
- [x] T037 [US2] Implement _create_deps() returning TavilySearchDeps in ClaudeCodeTavilySearchAgent in src/mixseek_plus/agents/claudecode_tavily_search_agent.py
- [x] T038 [US2] Implement _register_toolsets_if_claudecode() for MCP integration in ClaudeCodeTavilySearchAgent in src/mixseek_plus/agents/claudecode_tavily_search_agent.py
- [x] T039 [US2] Implement _get_agent_type_metadata() in ClaudeCodeTavilySearchAgent in src/mixseek_plus/agents/claudecode_tavily_search_agent.py
- [x] T040 [US2] Register claudecode_tavily_search agent type in factory via register_tavily_agents() in src/mixseek_plus/agents/__init__.py

**Checkpoint**: User Story 2 (ClaudeCode版Web検索) complete ✅
- [x] All T031-T034 tests pass (Green)
- [x] `uv run mypy src/mixseek_plus/agents/claudecode_tavily_search_agent.py` passes
- [x] Factory creates ClaudeCodeTavilySearchAgent for type="claudecode_tavily_search"
- [x] MCP tools registered with correct naming per contracts/tavily-tools.md section 6.1

---

## Phase 6: User Story 3 - URLからコンテンツを抽出 (Priority: P2) ✅ COMPLETED

**Goal**: tavily_extractツールを使用してURL群からコンテンツを抽出可能にする

**Independent Test**: `tavily_extract`ツールにURL群を渡し、各URLのコンテンツが抽出されることを確認する

**Note**: Core functionality implemented in Phase 3 (Mixin). This phase validates Acceptance Scenarios.

### 6a. Acceptance Scenario Validation

- [x] T041 [US3] Verify tavily_extract tool handles partial URL failures gracefully (returns success + failed_results)
- [x] T042 [US3] Verify tavily_extract validates URL format (http/https only) per contracts/tavily-tools.md section 3.3
- [x] T043 [US3] Verify tavily_extract handles empty URL list with VALIDATION_ERROR

### 6b. Integration Tests

- [x] T044 [P] [US3] Add integration test for tavily_extract with valid URLs in tests/integration/test_tavily_search_integration.py
- [x] T045 [P] [US3] Add integration test for tavily_extract with mixed valid/invalid URLs in tests/integration/test_tavily_search_integration.py

**Checkpoint**: User Story 3 (コンテンツ抽出) complete ✅
- [x] Acceptance Scenario 1 verified: 有効URL → コンテンツ抽出成功
- [x] Acceptance Scenario 2 verified: 一部無効URL → 有効URLのみ処理 + エラーハンドリング

---

## Phase 7: User Story 4 - RAG用検索コンテキストを取得 (Priority: P2) ✅ COMPLETED

**Goal**: tavily_contextツールを使用してRAG用に最適化されたコンテキストを取得可能にする

**Independent Test**: `tavily_context`ツールにクエリを渡し、RAG用に最適化されたコンテキスト文字列が返却されることを確認する

**Note**: Core functionality implemented in Phase 3 (Mixin). This phase validates Acceptance Scenarios.

### 7a. Acceptance Scenario Validation

- [x] T046 [US4] Verify tavily_context tool respects max_tokens parameter
- [x] T047 [US4] Verify tavily_context returns formatted string per contracts/tavily-tools.md section 4.4

### 7b. Integration Tests

- [x] T048 [P] [US4] Add integration test for tavily_context with query in tests/integration/test_tavily_search_integration.py
- [x] T049 [P] [US4] Add integration test for tavily_context with max_tokens in tests/integration/test_tavily_search_integration.py

**Checkpoint**: User Story 4 (RAGコンテキスト) complete ✅
- [x] Acceptance Scenario 1 verified: クエリ → RAG用コンテキスト返却
- [x] Acceptance Scenario 2 verified: max_tokens指定 → トークン数以内のコンテキスト返却

---

## Phase 8: User Story 5 - 既存groq_web_searchとの後方互換性維持 (Priority: P1) ✅ COMPLETED

**Goal**: 既存のgroq_web_searchエージェントが変更なしで動作することを保証する

**Independent Test**: 既存のgroq_web_search設定が変更なしで動作することを確認する

### 8a. Verification

- [x] T050 [US5] Verify groq_web_search agent code remains unchanged in src/mixseek_plus/agents/groq_web_search_agent.py (diff review)
- [x] T051 [US5] Verify groq_web_search and tavily_search can coexist in factory registration in src/mixseek_plus/agents/__init__.py

### 8b. Regression Tests

- [x] T052 [P] [US5] Add regression test ensuring groq_web_search still works in tests/integration/test_tavily_search_integration.py

**Checkpoint**: User Story 5 (後方互換性) complete ✅
- [x] Acceptance Scenario 1 verified: 既存設定 → 変更なしで動作
- [x] Acceptance Scenario 2 verified: 両エージェント → 独立して正常動作

---

## Phase 9: Polish & Cross-Cutting Concerns ✅ COMPLETED

**Purpose**: Improvements that affect multiple user stories

### 9a. Documentation (Sequential)

- [x] T053 Update README.md with Tavily検索エージェント使用例 (reference quickstart.md for consistency)
- [x] T054 Validate quickstart.md scenarios match implementation
  - Section 1.2: Groq版使用例が動作するか
  - Section 2.2: ClaudeCode版使用例が動作するか
  - Section 3: ツール出力が contracts/tavily-tools.md と一致するか

### 9b. Quality Checks (Sequential - T055 → T056)

- [x] T055 Run quality checks: `uv run ruff check --fix . && uv run ruff format . && uv run mypy .`
- [x] T056 Run pytest for all tests: `uv run pytest tests/`

**Final Checkpoint**: Production ready ✅
- [x] All unit tests pass
- [x] All integration tests pass (requires TAVILY_API_KEY)
- [x] ruff check clean
- [x] mypy clean
- [x] README.md updated

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ✅
    └── T001 → T002, T003 (parallel after T001)
              │
              ▼
Phase 2: Foundational - Infrastructure (TavilyAPIClient) ✅
    └── [TDD-RED] T004-T008 → [GREEN] T009-T013
              │
              ▼
Phase 3: Foundational - Domain (TavilyToolsRepositoryMixin) ✅
    └── [TDD-RED] T014-T017 → [GREEN] T018-T024
              │
              ├─────────────────────────┐
              ▼                         ▼
Phase 4: US1 (Groq) ✅       Phase 5: US2 (ClaudeCode) ✅
    └── [TDD-RED] T025           └── [TDD-RED] T031-T034
        → [GREEN] T026-T030          → [GREEN] T035-T040
              │                         │
              └─────────────────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
Phase 6: US3 (Extract)    Phase 7: US4 (Context)
    └── T041-T045             └── T046-T049
              │                       │
              └───────────┬───────────┘
                          ▼
              Phase 8: US5 (Backward Compat)
                  └── T050-T052
                          │
                          ▼
              Phase 9: Polish
                  └── T053 → T054 → T055 → T056
```

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Phase 2-3 (Infrastructure + Domain layers) ✅ COMPLETED
- **User Story 2 (P1)**: Depends on Phase 2-3 (Infrastructure + Domain layers) ✅ COMPLETED
- **User Story 3 (P2)**: Depends on Phase 3 (Domain layer) - can run parallel with US1/US2
- **User Story 4 (P2)**: Depends on Phase 3 (Domain layer) - can run parallel with US1/US2
- **User Story 5 (P1)**: Verification only - can run after US1 and US2 are registered

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel after T001
- **Phase 2**: T004-T008 (tests) run first, then T009-T013 (implementation)
- **Phase 3**: T014-T017 (tests) run first, then T018-T024 (implementation)
- **Phase 4 & 5**: User Story 1 (Groq) and User Story 2 (ClaudeCode) can run in parallel
- **Phase 6 & 7**: User Story 3 and User Story 4 can run in parallel
- **Phase 9**: T053-T056 are sequential (documentation before quality, quality before final test)

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2 + User Story 5)

1. Complete Phase 1: Setup (T001-T003) ✅
2. Complete Phase 2: Infrastructure Layer (T004-T013, TDD順) ✅
3. Complete Phase 3: Domain Layer (T014-T024, TDD順) ✅
4. Complete Phase 4: User Story 1 - Groq版 (T025-T030, TDD順) ✅
5. Complete Phase 5: User Story 2 - ClaudeCode版 (T031-T040, TDD順) ✅
6. Complete Phase 8: User Story 5 - 後方互換性検証 (T050-T052)
7. **STOP and VALIDATE**: Both agents functional, backward compatibility maintained
8. Deploy/demo if ready

### Incremental Delivery

1. Setup + Infrastructure + Domain → Foundation ready ✅
2. Add User Story 1 (Groq) → Test independently → Demo (MVP Groq!) ✅
3. Add User Story 2 (ClaudeCode) → Test independently → Demo (MVP ClaudeCode!) ✅
4. Add User Story 3 (Extract) → Integration tests → Enhanced features
5. Add User Story 4 (Context) → Integration tests → Full Tavily API coverage
6. Verify User Story 5 → Backward compatibility confirmed
7. Polish phase → Production ready

---

## Notes

- **[TDD-RED]** tasks = write failing test first (Constitution Article 1)
- **[P]** tasks = different files, no dependencies
- **[US#]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All output formatting must match contracts/tavily-tools.md
