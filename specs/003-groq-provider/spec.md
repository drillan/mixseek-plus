# Feature Specification: Groqプロバイダーのサポート追加

**Feature Branch**: `003-groq-provider`
**Created**: 2026-01-17
**Status**: Draft
**Input**: Issue #3 - Groqプロバイダーのサポート追加
**Parent Spec**: `specs/001-core-inheritance/spec.md` (FR-020, FR-023)

## Clarifications

### Session 2026-01-17

- Q: サポートモデルリストをどのように定義するか？ → A: Production + Previewモデルを含める（`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `qwen/qwen3-32b`等）
- Q: スラッシュを含むモデル名の扱いは？ → A: スラッシュをそのまま許可（`groq:qwen/qwen3-32b`形式）
- Q: mixseek-coreのエージェント制約への対応方針は？ → A: (1) Member AgentはCustom Agent実装、(2) Leader/EvaluatorはMonkey-patchで暫定対応。将来的にmixseek-coreへPR提出

## Background

mixseek-coreは以下のLLMプロバイダーをサポートしている：
- Google Gemini (`google-gla:`)
- Vertex AI (`google-vertex:`)
- OpenAI (`openai:`)
- Anthropic (`anthropic:`)
- xAI Grok (`grok:`)

mixseek-plusでは、これに加えて **Groq (Groq Inc.)** プロバイダーをサポートする。

### 重要: Grok vs Groq の区別

| サービス | 会社       | プレフィックス | 環境変数        |
|----------|------------|----------------|-----------------|
| Grok     | xAI        | `grok:`        | `GROK_API_KEY`  |
| **Groq** | Groq Inc.  | `groq:`        | `GROQ_API_KEY`  |

両者は名前が類似しているが、完全に異なるサービスである。本仕様はGroq Inc.のサービスを対象とする。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Python APIでのGroqモデル作成 (Priority: P1)

開発者がPython APIで `mixseek_plus.create_model("groq:llama-3.3-70b-versatile")` を呼び出すと、Groqモデルインスタンスが返され、mixseek-coreのエージェントで利用できる。

**Why this priority**: Groqプロバイダーの基本機能であり、他の全機能の前提となるため最優先。

**Independent Test**: 環境変数 `GROQ_API_KEY` を設定し、`create_model()` を呼び出してモデルインスタンスが返されることで検証可能。単体テストではモック、統合テストでは実APIを使用する。

**Acceptance Scenarios**:

1. **Given** `GROQ_API_KEY` が設定された環境, **When** `mixseek_plus.create_model("groq:llama-3.3-70b-versatile")` を呼び出す, **Then** Groqモデルインスタンスが返される
2. **Given** `GROQ_API_KEY` が設定された環境, **When** `mixseek_plus.create_model("groq:llama-3.1-8b-instant")` を呼び出す, **Then** Groqモデルインスタンスが返される
3. **Given** `GROQ_API_KEY` が設定された環境, **When** `mixseek_plus.create_model("groq:qwen/qwen3-32b")` を呼び出す, **Then** Groqモデルインスタンスが返される（Previewモデル）

---

### User Story 2 - mixseek-coreモデルへの委譲 (Priority: P1)

開発者がmixseek-coreでサポートされているモデルID（例: `openai:gpt-4o`）で `mixseek_plus.create_model()` を呼び出すと、mixseek-coreの認証・モデル作成機能に正しく委譲される。

**Why this priority**: mixseek-coreとの互換性維持は必須要件であり、Groq対応と同等に重要。

**Independent Test**: mixseek-coreでサポートされている各プロバイダーのモデルIDで `create_model()` を呼び出し、正常に動作することで検証可能。

**Acceptance Scenarios**:

1. **Given** `OPENAI_API_KEY` が設定された環境, **When** `mixseek_plus.create_model("openai:gpt-4o")` を呼び出す, **Then** mixseek-coreの `create_authenticated_model()` に委譲され、OpenAIモデルインスタンスが返される
2. **Given** `ANTHROPIC_API_KEY` が設定された環境, **When** `mixseek_plus.create_model("anthropic:claude-sonnet-4-5-20250929")` を呼び出す, **Then** mixseek-coreに委譲され、Anthropicモデルインスタンスが返される
3. **Given** `GOOGLE_API_KEY` が設定された環境, **When** `mixseek_plus.create_model("google-gla:gemini-2.5-flash")` を呼び出す, **Then** mixseek-coreに委譲され、Geminiモデルインスタンスが返される

---

### User Story 3 - APIキー未設定時のエラーハンドリング (Priority: P2)

開発者が `GROQ_API_KEY` を設定せずにGroqモデルを使用しようとすると、問題と解決策を明確に示すエラーメッセージが表示される。

**Why this priority**: ユーザー体験の向上に重要だが、基本機能の後に対応可能。

**Independent Test**: 環境変数未設定の状態で `create_model()` を呼び出し、適切なエラーが発生することで検証可能。

**Acceptance Scenarios**:

1. **Given** `GROQ_API_KEY` が未設定の環境, **When** `mixseek_plus.create_model("groq:llama-3.3-70b-versatile")` を呼び出す, **Then** 「GROQ_API_KEY環境変数が設定されていません」を含むエラーメッセージが表示される
2. **Given** `GROQ_API_KEY` が空文字の環境, **When** Groqモデルを使用しようとする, **Then** 「GROQ_API_KEY環境変数が設定されていません」を含むエラーメッセージが表示される
3. **Given** `GROQ_API_KEY` が `gsk_` で始まらない値の環境, **When** Groqモデルを使用しようとする, **Then** 「GROQ_API_KEYの形式が不正です」を含むエラーメッセージが表示される

---

### User Story 4 - 不正なモデルID形式のエラーハンドリング (Priority: P2)

開発者が不正な形式のモデルIDを指定すると、正しい形式を示すエラーメッセージが表示される。

**Why this priority**: ユーザー体験の向上に重要だが、基本機能の後に対応可能。

**Independent Test**: 不正な形式のモデルIDで `create_model()` を呼び出し、適切なエラーが発生することで検証可能。

**Acceptance Scenarios**:

1. **Given** 任意の環境, **When** `mixseek_plus.create_model("groq-llama")` （コロンなし）を呼び出す, **Then** 「モデルIDは 'provider:model-name' 形式で指定してください」を含むエラーメッセージが表示される
2. **Given** 任意の環境, **When** `mixseek_plus.create_model("unknown:model")` （未知のプロバイダー）を呼び出す, **Then** サポートされているプロバイダー一覧を含むエラーメッセージが表示される

---

### User Story 5 - Member AgentでのGroq利用 (Priority: P1)

開発者がmixseek-plusのCustom Member Agentを使用して、GroqモデルでPlain/Web Search相当の機能を実行できる。

**Why this priority**: mixseek CLIワークフローでGroqを利用するための必須機能。

**Independent Test**: TOML設定で `type = "groq_plain"` を指定し、タスクが正常に実行されることで検証可能。

**Acceptance Scenarios**:

1. **Given** `GROQ_API_KEY` が設定された環境, **When** `type = "groq_plain"` のMember Agent設定でタスクを実行, **Then** Groqモデルでタスクが正常に完了する
2. **Given** `GROQ_API_KEY` が設定された環境, **When** `type = "groq_web_search"` のMember Agent設定でWeb検索タスクを実行, **Then** Groqモデルで検索結果を含む回答が返される
3. **Given** mixseek-plusがインストールされた環境, **When** `MemberAgentFactory.register_agent()` でGroqエージェントを登録, **Then** TOMLから自動的にGroqエージェントが選択される

---

### User Story 6 - Leader/EvaluatorでのGroq利用 (Priority: P2)

開発者がLeader AgentまたはEvaluatorでGroqモデルを指定すると、mixseek-plusのパッチ機能により正常に動作する。

**Why this priority**: チーム実行や評価でGroqを使用するために必要だが、Member Agent対応後に実装可能。

**Independent Test**: `mixseek_plus.patch_core()` を呼び出した後、Leader/Evaluatorの設定で `model = "groq:..."` を指定し動作することで検証可能。

**Acceptance Scenarios**:

1. **Given** `mixseek_plus.patch_core()` が呼び出された環境, **When** Leader設定で `model = "groq:llama-3.3-70b-versatile"` を指定, **Then** Groqモデルでタスク委譲が正常に動作する
2. **Given** `mixseek_plus.patch_core()` が呼び出された環境, **When** Evaluator設定で `model = "groq:llama-3.1-8b-instant"` を指定, **Then** Groqモデルで評価が正常に実行される
3. **Given** パッチ未適用の環境, **When** Leader設定で `groq:` モデルを指定, **Then** 「mixseek_plus.patch_core() を呼び出してください」を含むエラーメッセージが表示される

---

### Edge Cases

**Acceptance Scenarios**:

1. **Given** `GROQ_API_KEY` が設定された環境, **When** Groq APIがレート制限（HTTP 429）を返す, **Then** 「レート制限に達しました。しばらく待ってから再試行してください」を含むエラーメッセージが表示される
2. **Given** `GROQ_API_KEY` が設定された環境, **When** Groq APIが一時的にダウン（HTTP 503）している, **Then** 「Groqサービスが一時的に利用できません」を含むエラーメッセージが表示される
3. **Given** `GROQ_API_KEY` が設定された環境, **When** 存在しないモデル名 `groq:nonexistent-model` を指定, **Then** Groq APIからのエラーメッセージが適切にラップされて表示される

## Requirements *(mandatory)*

### Functional Requirements

> **注記**: 本仕様の要件IDは `GR-xxx` を使用（親仕様 `001-core-inheritance` の `FR-xxx` と区別するため）

#### モデル作成機能

- **GR-001**: `mixseek_plus.create_model(model_id)` 関数を提供し、`groq:` プレフィックスのモデルIDを受け付けなければならない
- **GR-002**: `groq:` プレフィックスのモデルIDが指定された場合、Groqプロバイダーを使用してモデルインスタンスを作成しなければならない
- **GR-003**: `groq:` 以外のプレフィックスのモデルIDが指定された場合、mixseek-coreの `create_authenticated_model()` に処理を委譲しなければならない

#### 認証

- **GR-010**: Groqモデル作成時、環境変数 `GROQ_API_KEY` からAPIキーを取得しなければならない
- **GR-011**: `GROQ_API_KEY` が未設定または空の場合、明確なエラーメッセージを表示しなければならない
- **GR-012**: `GROQ_API_KEY` が `gsk_` で始まらない場合、形式不正のエラーメッセージを表示しなければならない

#### サポートモデル

- **GR-020**: 以下のGroqモデルをサポートしなければならない（Production + Preview）：
  - Production: `groq:llama-3.3-70b-versatile`, `groq:llama-3.1-8b-instant`
  - Preview: `groq:meta-llama/llama-4-scout-17b-16e-instruct`, `groq:qwen/qwen3-32b`
- **GR-021**: 上記以外のGroq APIモデルも `groq:model-name` 形式で指定可能でなければならない（モデルの検証はGroq API側で行われる）
- **GR-022**: モデル名にスラッシュを含む場合（例: `groq:qwen/qwen3-32b`）、そのまま受け付けなければならない

#### エラーハンドリング

- **GR-030**: 不正なモデルID形式（コロンなし等）の場合、正しい形式を示すエラーメッセージを表示しなければならない
- **GR-031**: 未知のプロバイダープレフィックスの場合、サポートされているプロバイダー一覧を含むエラーメッセージを表示しなければならない
- **GR-032**: Groq API呼び出し時のエラー（認証エラー、レート制限、サービス障害等）は、原因と対処法を含むエラーメッセージを表示しなければならない

#### Member Agent統合

- **GR-050**: `GroqPlainMemberAgent` クラスを提供し、Groqモデルでの推論機能を実装しなければならない
- **GR-051**: `GroqWebSearchMemberAgent` クラスを提供し、Groqモデルでの検索機能を実装しなければならない
- **GR-052**: 上記エージェントは `BaseMemberAgent` を継承し、mixseek-coreのインターフェースと互換性を持たなければならない
- **GR-053**: `MemberAgentFactory.register_agent()` で `groq_plain`, `groq_web_search` タイプを登録しなければならない
- **GR-054**: TOML設定で `type = "groq_plain"` または `type = "groq_web_search"` を指定可能でなければならない

#### Leader/Evaluator統合（暫定対応）

- **GR-060**: `mixseek_plus.patch_core()` 関数を提供し、mixseek-coreの `create_authenticated_model()` を拡張しなければならない
- **GR-061**: パッチ適用後、Leader/Evaluator設定で `groq:` プレフィックスのモデルが使用可能になならなければならない
- **GR-062**: パッチは明示的に呼び出す必要があり、自動適用してはならない（暗黙的動作禁止）
- **GR-063**: パッチ未適用で `groq:` モデルが使用された場合、適切なエラーメッセージを表示しなければならない

#### エクスポート

- **GR-040**: `mixseek_plus` パッケージから `create_model` 関数をインポート可能でなければならない
- **GR-041**: `mixseek_plus` パッケージから `patch_core` 関数をインポート可能でなければならない
- **GR-042**: `mixseek_plus` パッケージから `GroqPlainMemberAgent`, `GroqWebSearchMemberAgent` をインポート可能でなければならない

### Key Entities

- **Model**: LLMプロバイダーへの接続を抽象化したオブジェクト
  - **属性**: `provider_id`（プロバイダー識別子）, `model_name`（モデル名）
  - **不変条件**: `provider_id` は空文字不可、`model_name` は空文字不可
  - **生成元**: `create_model()` 関数のみ（直接インスタンス化は非推奨）

- **Provider**: LLMサービス提供者の識別子
  - **有効な値**: `groq`（mixseek-plus）、`openai`, `anthropic`, `google-gla`, `google-vertex`, `grok`（mixseek-core）
  - **環境変数マッピング**: `groq` → `GROQ_API_KEY`
  - **モデルID形式**: `{provider}:{model_name}`（例: `groq:llama-3.3-70b-versatile`）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `mixseek_plus.create_model("groq:llama-3.3-70b-versatile")` が正常にモデルインスタンスを返す
- **SC-002**: mixseek-coreでサポートされている全プロバイダー（5種類）のモデルIDが `mixseek_plus.create_model()` で正常に動作する
- **SC-003**: APIキー未設定時のエラーメッセージに「GROQ_API_KEY」と「設定」の両方が含まれる
- **SC-004**: 不正なモデルID形式のエラーメッセージに正しい形式の例が含まれる

### Assumptions

- Groq APIは公開されており、APIキーで認証可能である
- pydantic-aiライブラリがGroqプロバイダーをサポートしている
- mixseek-coreの `create_authenticated_model()` 関数は安定したAPIを提供している
- ユーザーはGroq Console（https://console.groq.com/keys）でAPIキーを取得済みである

### Implementation Approach

mixseek-coreには以下の制約があり、直接的なGroq対応は不可能：

1. **Config Validation**: `MemberAgentConfig.validate_model()` がBuiltinエージェントで6プロバイダーのみ許可
2. **Model Creation**: `create_authenticated_model()` が `groq:` プレフィックスを認識しない
3. **Agent-specific**: `web_fetch`, `code_execution` はプロバイダー固有制約あり

**対応戦略**:

| 対象 | 方式 | 理由 |
|------|------|------|
| Member Agent (Plain/WebSearch相当) | Custom Agent実装 | `type: custom` で検証スキップ、独自モデル作成 |
| Leader/Evaluator | Monkey-patch | `create_authenticated_model()` を拡張 |
| Web Fetch/Code Execution | 対応不可 | mixseek-core側の明示的制約 |

**将来的対応**:
- mixseek-coreへPR提出し、`groq:` プレフィックスを標準サポートに追加
- PR承認後、monkey-patchを削除し標準APIに移行

### Constraints

以下のエージェントはGroqで使用不可（mixseek-core側の制約）:

| エージェント | 理由 |
|-------------|------|
| Web Fetch | Anthropic/Google専用ツール |
| Code Execution | Anthropic専用ツール |

### Test Strategy

- **単体テスト**: Groq APIをモックし、`create_model()` の分岐ロジック・エラーハンドリングを検証。CI環境で常時実行。
- **統合テスト**: 実際のGroq APIを呼び出し、エンドツーエンドの動作を検証。`GROQ_API_KEY` が設定されている場合のみ実行（`pytest.mark.integration`）。
