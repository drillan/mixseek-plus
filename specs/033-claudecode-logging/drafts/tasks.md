# Issue #33: タスクリスト

## Phase 1: 短期対応（即効性）

### Task 1.1: core_patch.pyにログ追加
- [ ] `_is_verbose_mode()`関数を追加
- [ ] `_summarize_tool_args()`関数を追加
- [ ] `_wrap_tool_function_for_mcp()`にログ出力を追加
  - [ ] ツール呼び出し開始ログ
  - [ ] ツール呼び出し成功ログ（実行時間含む）
  - [ ] ツール呼び出しエラーログ

### Task 1.2: playwright_markdown_fetch_agent.pyにログ追加
- [ ] `_wrap_tool_for_mcp()`に同様のログパターンを適用
- [ ] 実行時間測定を追加

## Phase 2: 中期対応（メッセージ抽出）

### Task 2.1: utils/claudecode_logging.py作成
- [ ] `ClaudeCodeToolCallExtractor`クラス実装
- [ ] `extract_tool_calls()`メソッド実装
- [ ] `_summarize_args()`関数実装
- [ ] `_summarize_result()`関数実装
- [ ] `_match_tool_return()`関数実装

### Task 2.2: base_claudecode_agent.py拡張
- [ ] `_log_tool_calls()`メソッド追加
- [ ] `_is_verbose_mode()`メソッド追加
- [ ] `execute()`メソッドで`_log_tool_calls()`呼び出し追加

### Task 2.3: テスト作成
- [ ] `tests/unit/test_claudecode_logging.py`作成
  - [ ] `TestClaudeCodeToolCallExtractor`
  - [ ] `TestSummarizeArgs`
  - [ ] `TestSummarizeResult`

## Phase 3: 中期対応（Logfire）

### Task 3.1: observability/パッケージ作成
- [ ] `src/mixseek_plus/observability/__init__.py`作成
- [ ] `src/mixseek_plus/observability/logfire_integration.py`作成
  - [ ] `is_logfire_enabled()`関数実装
  - [ ] `setup_logfire_instrumentation()`関数実装

### Task 3.2: テスト作成
- [ ] `tests/unit/test_logfire_integration.py`作成
  - [ ] `TestIsLogfireEnabled`
  - [ ] `TestSetupLogfireInstrumentation`

## Phase 4: ドキュメント・統合

### Task 4.1: ドキュメント更新
- [ ] README.mdにロギング設定セクション追加
- [ ] 使用例を追加

### Task 4.2: 品質チェック
- [ ] `uv run ruff check --fix .`
- [ ] `uv run ruff format .`
- [ ] `uv run mypy .`
- [ ] `uv run pytest`

## 依存関係

```
Task 1.1 → Task 1.2 （パターンの確立）
Task 2.1 → Task 2.2 （ユーティリティの使用）
Task 2.2 → Task 2.3 （テスト対象の作成）
Task 3.1 → Task 3.2 （テスト対象の作成）
Phase 1, 2, 3 → Phase 4 （ドキュメント・品質チェック）
```

## 見積もり

| Phase | タスク数 | 難易度 |
|-------|---------|--------|
| Phase 1 | 2 | 低 |
| Phase 2 | 3 | 中 |
| Phase 3 | 2 | 低 |
| Phase 4 | 2 | 低 |
