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

**Independent Test**: 環境変数 `GROQ_API_KEY` を設定し、`create_model()` を呼び出してモデルインスタンスが返されることで検証可能。

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

---

### User Story 4 - 不正なモデルID形式のエラーハンドリング (Priority: P2)

開発者が不正な形式のモデルIDを指定すると、正しい形式を示すエラーメッセージが表示される。

**Why this priority**: ユーザー体験の向上に重要だが、基本機能の後に対応可能。

**Independent Test**: 不正な形式のモデルIDで `create_model()` を呼び出し、適切なエラーが発生することで検証可能。

**Acceptance Scenarios**:

1. **Given** 任意の環境, **When** `mixseek_plus.create_model("groq-llama")` （コロンなし）を呼び出す, **Then** 「モデルIDは 'provider:model-name' 形式で指定してください」を含むエラーメッセージが表示される
2. **Given** 任意の環境, **When** `mixseek_plus.create_model("unknown:model")` （未知のプロバイダー）を呼び出す, **Then** サポートされているプロバイダー一覧を含むエラーメッセージが表示される

---

### Edge Cases

- Groq APIがレート制限を返した場合、リトライ可能であることを示すエラーメッセージが表示される
- Groq APIが一時的にダウンしている場合、サービス障害を示すエラーメッセージが表示される
- 存在しないGroqモデル名を指定した場合、利用可能なモデル一覧を含むエラーメッセージが表示される

## Requirements *(mandatory)*

### Functional Requirements

#### モデル作成機能

- **FR-001**: `mixseek_plus.create_model(model_id)` 関数を提供し、`groq:` プレフィックスのモデルIDを受け付けなければならない
- **FR-002**: `groq:` プレフィックスのモデルIDが指定された場合、Groqプロバイダーを使用してモデルインスタンスを作成しなければならない
- **FR-003**: `groq:` 以外のプレフィックスのモデルIDが指定された場合、mixseek-coreの `create_authenticated_model()` に処理を委譲しなければならない

#### 認証

- **FR-010**: Groqモデル作成時、環境変数 `GROQ_API_KEY` からAPIキーを取得しなければならない
- **FR-011**: `GROQ_API_KEY` が未設定または空の場合、明確なエラーメッセージを表示しなければならない

#### サポートモデル

- **FR-020**: 以下のGroqモデルをサポートしなければならない（Production + Preview）：
  - Production: `groq:llama-3.3-70b-versatile`, `groq:llama-3.1-8b-instant`
  - Preview: `groq:meta-llama/llama-4-scout-17b-16e-instruct`, `groq:qwen/qwen3-32b` 等
- **FR-021**: Groq APIで利用可能な他のモデルも `groq:model-name` 形式で指定可能でなければならない
- **FR-022**: モデル名にスラッシュを含む場合（例: `groq:qwen/qwen3-32b`）、そのまま受け付けなければならない

#### エラーハンドリング

- **FR-030**: 不正なモデルID形式（コロンなし等）の場合、正しい形式を示すエラーメッセージを表示しなければならない
- **FR-031**: 未知のプロバイダープレフィックスの場合、サポートされているプロバイダー一覧を含むエラーメッセージを表示しなければならない
- **FR-032**: Groq API呼び出し時のエラー（認証エラー、レート制限、サービス障害等）は、原因と対処法を含むエラーメッセージを表示しなければならない

#### エクスポート

- **FR-040**: `mixseek_plus` パッケージから `create_model` 関数をインポート可能でなければならない

### Key Entities

- **Model**: LLMプロバイダーへの接続を抽象化したオブジェクト。プロバイダー固有の認証情報とAPI呼び出しをカプセル化する
- **Provider**: LLMサービス提供者（Groq, OpenAI, Anthropic等）の識別子。モデルIDのプレフィックスとして使用される

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
