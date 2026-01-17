# Feature Specification: ClaudeCodeプロバイダーのサポート追加

**Feature Branch**: `008-claudecode-provider`
**Created**: 2026-01-17
**Status**: Draft
**Input**: Issue #8 - ClaudeCodeプロバイダーのサポート追加
**Parent Spec**: `specs/001-core-inheritance/spec.md` (FR-020, FR-023)

## Clarifications

### Session 2026-01-17

- Q: サポートするClaudeモデル名は何か？ → A: 公式ドキュメントに基づくモデルをサポート（詳細は「Key Entities > ClaudeCodeModel > サポートモデル」を参照）
- Q: User Story 2（mixseek-coreモデルへの委譲）は必要か？ → A: 削除。親仕様001-core-inheritance FR-020と重複。委譲機能は親仕様で定義済みであり、テストは親仕様のテストスイートでカバー済み
- Q: Success Criteriaに追加すべき重要な指標は？ → A: APIキーなしでmixseekのオーケストレーション処理が完遂すること（Claude Code CLIの認証を利用するため、環境変数のAPIキー設定が不要）

## Background

mixseek-coreは以下のLLMプロバイダーをサポートしている：
- Google Gemini (`google-gla:`)
- Vertex AI (`google-vertex:`)
- OpenAI (`openai:`)
- Anthropic (`anthropic:`)
- xAI Grok (`grok:`)
- xAI Grok Responses (`grok-responses:`)

mixseek-plusでは、これに加えて **claudecode-model** パッケージを使用した **ClaudeCode** プロバイダーをサポートする。

### ClaudeCodeModelの特徴

ClaudeCodeModelはClaude Code CLI経由でLLMを呼び出すモデルであり、以下の組み込みツールを使用可能：

| ツール | 機能 |
|--------|------|
| **Bash** | コマンド・コード実行 |
| **Read/Write/Edit** | ファイル操作 |
| **Glob/Grep** | ファイル検索 |
| **WebFetch/WebSearch** | Web検索・取得 |

そのため、mixseek-coreの`web_search`/`web_fetch`/`code_execution`タイプの個別エージェントは不要。
**ClaudeCodePlainAgent**がこれらの機能をすべて包含する。

### 認証の特徴

ClaudeCodeModelはClaude Code CLIのセッション認証を使用するため、**APIキー環境変数（ANTHROPIC_API_KEY等）の設定が不要**。これにより、mixseekのオーケストレーション処理をAPIキー管理なしで実行可能。

### 検証結果

`ai_working/validate-claudecode-model/`で事前検証済み：

| テスト | 結果 |
|--------|------|
| 依存関係チェック | ✅ 5/5 パス |
| インポートテスト | ✅ 6/6 パス |
| Model互換性テスト | ✅ 7/7 パス |
| Agent統合テスト | ✅ 4/4 パス |
| MemberAgentプロトタイプ | ✅ 5/5 パス |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Python APIでのClaudeCodeモデル作成 (Priority: P1)

開発者がPython APIで `mixseek_plus.create_model("claudecode:claude-sonnet-4-5")` を呼び出すと、ClaudeCodeModelインスタンスが返され、mixseek-coreのエージェントで利用できる。

**Why this priority**: ClaudeCodeプロバイダーの基本機能であり、他の全機能の前提となるため最優先。

**Independent Test**: `create_model()` を呼び出してClaudeCodeModelインスタンスが返されることで検証可能。単体テストではモック、統合テストでは実際のClaude Code CLIを使用する。

**Acceptance Scenarios**:

1. **Given** Claude Code CLIが利用可能な環境, **When** `mixseek_plus.create_model("claudecode:claude-sonnet-4-5")` を呼び出す, **Then** ClaudeCodeModelインスタンスが返される
2. **Given** Claude Code CLIが利用可能な環境, **When** `mixseek_plus.create_model("claudecode:claude-opus-4-5")` を呼び出す, **Then** ClaudeCodeModelインスタンスが返される
3. **Given** Claude Code CLIが利用可能な環境, **When** `mixseek_plus.create_model("claudecode:claude-haiku-4-5")` を呼び出す, **Then** ClaudeCodeModelインスタンスが返される

---

### User Story 2 - ClaudeCodePlainAgent Member Agentでの利用 (Priority: P1)

開発者がmixseek-plusのCustom Member Agentを使用して、ClaudeCodeModelでPlain推論機能（Bash、ファイル操作、Web検索を含む）を実行できる。

**Why this priority**: mixseek CLIワークフローでClaudeCodeを利用するための必須機能。ClaudeCodeModelは組み込みツールを持つため、単一のPlainAgentで複数機能を提供できる。

**Independent Test**: TOML設定で `type = "claudecode_plain"` を指定し、タスクが正常に実行されることで検証可能。

**Acceptance Scenarios**:

1. **Given** Claude Code CLIが利用可能な環境, **When** `type = "claudecode_plain"` のMember Agent設定でタスクを実行, **Then** ClaudeCodeModelでタスクが正常に完了する
2. **Given** mixseek-plusがインストールされた環境, **When** `MemberAgentFactory.register_agent()` でClaudeCodeエージェントを登録, **Then** TOMLから自動的にClaudeCodeエージェントが選択される

---

### User Story 3 - Leader/EvaluatorでのClaudeCode利用 (Priority: P2)

開発者がLeader AgentまたはEvaluatorでClaudeCodeモデルを指定すると、mixseek-plusのパッチ機能により正常に動作する。

**Why this priority**: チーム実行や評価でClaudeCodeを使用するために必要だが、Member Agent対応後に実装可能。

**Independent Test**: `mixseek_plus.patch_core()` を呼び出した後、Leader/Evaluatorの設定で `model = "claudecode:..."` を指定し動作することで検証可能。

**Acceptance Scenarios**:

1. **Given** `mixseek_plus.patch_core()` が呼び出された環境, **When** Leader設定で `model = "claudecode:claude-sonnet-4-5"` を指定, **Then** ClaudeCodeModelでタスク委譲が正常に動作する
2. **Given** `mixseek_plus.patch_core()` が呼び出された環境, **When** Evaluator設定で `model = "claudecode:claude-sonnet-4-5"` を指定, **Then** ClaudeCodeModelで評価が正常に実行される
3. **Given** パッチ未適用の環境, **When** Leader設定で `claudecode:` モデルを指定, **Then** 「mixseek_plus.patch_core() を呼び出してください」を含むエラーメッセージが表示される

---

### User Story 4 - CLIでのClaudeCode利用 (Priority: P1)

開発者がmixseek-plusをインストールすると、`mixseek` CLIコマンドが自動的にClaudeCode対応となり、追加設定なしでLeader/Evaluator/JudgmentでClaudeCodeモデルを使用できる。

**Why this priority**: CLI経由でのClaudeCode利用はUser Story 2, 3の実用的な前提条件であり、最優先で対応が必要。

**Independent Test**: mixseek-plusインストール後、`mixseek exec`でClaudeCodeモデルを指定したTOML設定を実行し、正常に動作することで検証可能。

**Acceptance Scenarios**:

1. **Given** mixseek-plusがインストールされた環境, **When** `mixseek exec --config claudecode-config.toml` を実行, **Then** Leader/Evaluator/JudgmentでClaudeCodeモデルが使用される
2. **Given** mixseek-plusがインストールされた環境, **When** `mixseek --version` を実行, **Then** mixseek-coreのバージョン情報が表示される（互換性維持）
3. **Given** mixseek-plusがインストールされた環境, **When** `mixseek` の任意のサブコマンドを実行, **Then** mixseek-coreと同一の動作をする

---

### User Story 5 - ツール設定のカスタマイズ (Priority: P2)

開発者がTOML設定でClaudeCodeエージェントのツール設定をカスタマイズし、利用可能なツールやパーミッションモードを制御できる。

**Why this priority**: 高度なユースケースのための機能だが、基本機能の後に対応可能。

**Independent Test**: TOML設定で `[members.tool_settings.claudecode]` を指定し、設定が反映されることで検証可能。

**Acceptance Scenarios**:

1. **Given** `allowed_tools = ["Read", "Glob", "Grep", "Bash"]` を指定, **When** ClaudeCodePlainAgentを実行, **Then** 指定されたツールのみが利用可能になる
2. **Given** `permission_mode = "bypassPermissions"` を指定, **When** ClaudeCodePlainAgentを実行, **Then** パーミッション確認がスキップされる
3. **Given** `tool_settings` が未指定, **When** ClaudeCodePlainAgentを実行, **Then** デフォルト設定（全ツール利用可能、通常パーミッション）で動作する

---

### Edge Cases

**Acceptance Scenarios**:

1. **Given** Claude Code CLIがインストールされていない環境, **When** `mixseek_plus.create_model("claudecode:claude-sonnet-4-5")` を呼び出す, **Then** 「Claude Code CLIがインストールされていません」を含むエラーメッセージが表示される
2. **Given** Claude Code CLIのセッションが無効な環境, **When** ClaudeCodeModelを使用しようとする, **Then** 適切なエラーメッセージとセッション再認証の案内が表示される
3. **Given** サポートされていないモデル名 `claudecode:nonexistent-model` を指定, **When** モデルを作成しようとする, **Then** ClaudeCode側からのエラーメッセージが適切にラップされて表示される

## Requirements *(mandatory)*

### Functional Requirements

> **注記**: 本仕様の要件IDは `CC-xxx` を使用（Groqプロバイダー仕様の `GR-xxx` と区別するため）

#### プロバイダー定義

- **CC-001**: `providers/__init__.py` に `CLAUDECODE_PROVIDER_PREFIX = "claudecode:"` を定義しなければならない

#### モデル作成機能

- **CC-010**: `mixseek_plus.create_model(model_id)` 関数が `claudecode:` プレフィックスのモデルIDを受け付けなければならない
- **CC-011**: `claudecode:` プレフィックスのモデルIDが指定された場合、`claudecode-model`パッケージの`ClaudeCodeModel`を使用してモデルインスタンスを作成しなければならない
- **CC-012**: 他プロバイダーへの委譲は親仕様 `001-core-inheritance` FR-020 に準拠する

#### モデルファクトリー

- **CC-020**: `providers/claudecode.py` を新規作成し、`create_claudecode_model()` 関数を実装しなければならない
- **CC-021**: `model_factory.py` で `claudecode:` プレフィックスを認識し、適切なモデル作成関数にルーティングしなければならない

#### Member Agent統合

- **CC-030**: `ClaudeCodePlainAgent` クラスを提供し、ClaudeCodeModelでの推論機能を実装しなければならない
- **CC-031**: ClaudeCodePlainAgentは`BaseMemberAgent`を継承し、mixseek-coreのインターフェースと互換性を持たなければならない
- **CC-032**: `MemberAgentFactory.register_agent()` で `claudecode_plain` タイプを登録しなければならない
- **CC-033**: TOML設定で `type = "claudecode_plain"` を指定可能でなければならない
- **CC-034**: ClaudeCodePlainAgentはClaudeCodeModelの組み込みツール（Bash、Read/Write/Edit、Glob/Grep、WebFetch/WebSearch）を活用しなければならない

#### ツール設定

- **CC-040**: TOML設定で `[members.tool_settings.claudecode]` セクションをサポートしなければならない
- **CC-041**: `allowed_tools` オプションで利用可能なツールを制限できなければならない
- **CC-042**: `permission_mode` オプションでパーミッションモードを設定できなければならない
- **CC-043**: ツール設定が未指定の場合、適切なデフォルト値で動作しなければならない

#### Leader/Evaluator統合（patch_core拡張）

- **CC-050**: `mixseek_plus.patch_core()` 関数で `claudecode:` プレフィックスを認識するように拡張しなければならない
- **CC-051**: パッチ適用後、Leader/Evaluator/Judgment設定で `claudecode:` プレフィックスのモデルが使用可能にならなければならない
- **CC-052**: パッチはPython APIでは明示的に呼び出す必要があり、自動適用してはならない。ただし、CLI経由での使用時はエントリーポイントでの自動適用が許可される

#### エラーハンドリング

- **CC-060**: Claude Code CLIが利用不可の場合、明確なエラーメッセージを表示しなければならない
- **CC-061**: ClaudeCodeModelからのエラーは、原因と対処法を含むエラーメッセージにラップしなければならない
- **CC-062**: 不正なモデルID形式の場合、正しい形式を示すエラーメッセージを表示しなければならない

#### エクスポート

- **CC-070**: `mixseek_plus` パッケージから `ClaudeCodePlainAgent` をインポート可能でなければならない
- **CC-071**: `agents/__init__.py` に `register_claudecode_agents()` 関数を追加しなければならない

### Key Entities

- **ClaudeCodeModel**: Claude Code CLI経由でLLMを呼び出すモデル
  - **属性**: `model_name`（モデル名）、`tool_settings`（ツール設定）
  - **組み込みツール**: Bash、Read/Write/Edit、Glob/Grep、WebFetch/WebSearch
  - **生成元**: `create_claudecode_model()` 関数
  - **サポートモデル**（公式ドキュメント準拠）:
    - Current: `claude-sonnet-4-5`, `claude-haiku-4-5`, `claude-opus-4-5`
    - Legacy: `claude-opus-4-1`, `claude-sonnet-4-0`, `claude-opus-4-0`
    - フルバージョン指定も可能（例: `claude-sonnet-4-5-20250929`）

- **ClaudeCodePlainAgent**: ClaudeCodeModelを使用するMember Agent
  - **属性**: `name`（エージェント名）、`model`（ClaudeCodeModel）、`tool_settings`（ツール設定）
  - **継承**: `BaseMemberAgent`
  - **特徴**: 単一エージェントで複数機能（推論、コード実行、ファイル操作、Web検索）を提供
  - **tool_settings優先順位**: Agent設定が最優先。未指定の場合はModelのtool_settings、それも未指定の場合はデフォルト値を使用

- **Provider**: LLMサービス提供者の識別子
  - **有効な値**: `claudecode`（mixseek-plus）、`groq`（mixseek-plus）、`openai`, `anthropic`, `google-gla`, `google-vertex`, `grok`, `grok-responses`（mixseek-core）
  - **モデルID形式**: `{provider}:{model_name}`（例: `claudecode:claude-sonnet-4-5`）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `mixseek_plus.create_model("claudecode:claude-sonnet-4-5")` が正常にClaudeCodeModelインスタンスを返す
- **SC-002**: `claudecode:claude-haiku-4-5` および `claudecode:claude-opus-4-5` が正常に動作する
- **SC-003**: `type = "claudecode_plain"` のMember Agent設定でタスクが正常に完了する
- **SC-004**: ClaudeCodePlainAgentでBash、ファイル操作、Web検索の各ツールが利用可能である
- **SC-005**: Leader/Evaluatorで `claudecode:` モデルを指定した場合、正常にタスクが実行される
- **SC-006**: CLI経由で `mixseek exec` がClaudeCode設定で正常に動作する
- **SC-007**: APIキー環境変数（ANTHROPIC_API_KEY等）を設定せずに、`claudecode:` モデルのみでmixseekのオーケストレーション処理（Team実行、Orchestrator実行）が完遂する

### Assumptions

- `claudecode-model` パッケージは依存関係として追加済みである
- Claude Code CLIがユーザーの環境にインストールされている
- pydantic-aiのModelインターフェースとClaudeCodeModelが互換性を持つ
- Groqプロバイダー（#3）と同様のパターンで実装可能である

### Implementation Approach

Groqプロバイダー（#3）と同様のパターンで実装：

| 対象 | 方式 | 理由 |
|------|------|------|
| Member Agent (PlainAgent) | Custom Agent実装 | `type: custom` で検証スキップ、ClaudeCodeModel使用 |
| Leader/Evaluator/Judgment | `patch_core()` 拡張 | `create_authenticated_model()` を拡張 |
| Web Search/Web Fetch/Code Execution | **対応不要** | ClaudeCodePlainAgentの組み込み機能として提供 |

### Constraints

ClaudeCodeModelの組み込みツールにより、以下の個別エージェントタイプは不要：

| エージェントタイプ | 理由 |
|------------------|------|
| claudecode_web_search | ClaudeCodePlainAgentのWebSearchツールで対応 |
| claudecode_web_fetch | ClaudeCodePlainAgentのWebFetchツールで対応 |
| claudecode_code_execution | ClaudeCodePlainAgentのBashツールで対応 |

### Test Strategy

- **単体テスト**: ClaudeCodeModelをモックし、`create_model()` の分岐ロジック・エラーハンドリングを検証。CI環境で常時実行。
- **統合テスト**: 実際のClaude Code CLIを呼び出し、エンドツーエンドの動作を検証。Claude Code CLIが利用可能な場合のみ実行（`pytest.mark.integration`）。
