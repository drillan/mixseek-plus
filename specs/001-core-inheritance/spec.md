# Feature Specification: mixseek-core依存関係の検証とパッケージ基盤構築

**Feature Branch**: `001-core-inheritance`
**Created**: 2026-01-17
**Status**: Draft
**Input**: Issue #1 - mixseek-core依存関係の検証とパッケージ基盤構築

## Clarifications

### Session 2026-01-17

- Q: mixseek-plusの役割は何か？ → A: 拡張専用（mixseek-coreはそのまま使用、mixseek-plusは追加機能のみ提供）
- Q: 追加機能の提供方式は？ → A: Python APIとTOML設定の両方で追加機能を利用可能にする
- Q: 認証レイヤーの拡張方式は？ → A: ラッパー関数（`mixseek_plus.create_model()`）を提供し、内部でmixseek-coreに委譲
- Q: Issue #1のスコープは？ → A: mixseek-core依存関係と動作確認のみ。追加機能（Groq、Playwright等）は別issueで実装

## User Scenarios & Testing *(mandatory)*

### User Story 1 - mixseek-coreとmixseek-plusの併用 (Priority: P1)

開発者がmixseek-plusパッケージをインストールすると、mixseek-coreが依存関係として自動インストールされ、`mixseek` CLIと `from mixseek import ...` でmixseek-coreの全機能をそのまま利用できる。追加機能は `from mixseek_plus import ...` で利用する。

**Why this priority**: mixseek-plusの設計思想の根幹であり、既存mixseek-coreユーザーの移行コストを最小化するため最優先。

**Independent Test**: `pip install mixseek-plus` 後に `mixseek --help` と `from mixseek import Orchestrator` が動作することで検証可能。

**Acceptance Scenarios**:

1. **Given** mixseek-plusがインストールされている環境, **When** `from mixseek import PlainMemberAgent` を実行, **Then** mixseek-coreのクラスがエラーなくインポートできる
2. **Given** mixseek-plusがインストールされている環境, **When** `mixseek team "タスク" --config team.toml` を実行, **Then** mixseek-coreのCLIが正常に動作する
3. **Given** mixseek-plusがインストールされている環境, **When** `from mixseek_plus import GroqProvider` を実行, **Then** mixseek-plus固有の追加機能がインポートできる

---

### User Story 2 - mixseek CLIによるワークフロー実行 (Priority: P1)

開発者がmixseek-coreの `mixseek` CLIコマンドを使用して、ワークスペース初期化からチーム実行、Orchestrator実行まで全てのワークフローを実行できる。mixseek-plusは独自のCLIを提供せず、mixseek-coreのCLIをそのまま利用する。

**Why this priority**: 既存のmixseek-coreユーザーが同じコマンドで継続利用できるため重要。

**Independent Test**: `mixseek init` から `mixseek exec` まで一連のコマンドが正常に実行できることで検証可能。

**Acceptance Scenarios**:

1. **Given** 新しいディレクトリ, **When** `mixseek init` を実行, **Then** ワークスペースが初期化されサンプル設定ファイルが生成される
2. **Given** 初期化されたワークスペース, **When** `mixseek member "質問" --config agent.toml` を実行, **Then** Member Agentが実行され結果が表示される
3. **Given** 初期化されたワークスペース, **When** `mixseek team "タスク" --config team.toml` を実行, **Then** Team（Leader + Members）が実行され結果が表示される
4. **Given** 初期化されたワークスペース, **When** `mixseek exec "タスク" --config orchestrator.toml` を実行, **Then** 複数チームが並列実行されリーダーボードが表示される
5. **Given** 初期化されたワークスペース, **When** `mixseek ui` を実行, **Then** Streamlit Web UIが起動する

---

### User Story 3 - 既存mixseek-core設定ファイルの互換性 (Priority: P2)

mixseek-coreで作成した既存のTOML設定ファイルを変更なしでmixseek-plusで利用できる。

**Why this priority**: 既存ユーザーの移行を容易にするため重要。

**Independent Test**: mixseek-coreで動作確認済みのTOML設定ファイルをmixseek-plusで読み込み、同一の結果が得られることで検証可能。

**Acceptance Scenarios**:

1. **Given** mixseek-core用のteam.tomlファイル, **When** mixseek-plusで `--config team.toml` として使用, **Then** 設定が正しく読み込まれエラーなく動作する
2. **Given** mixseek-core用のorchestrator.tomlファイル, **When** mixseek-plusで `--config orchestrator.toml` として使用, **Then** 設定が正しく読み込まれエラーなく動作する
3. **Given** mixseek-core用のevaluator.tomlファイル, **When** mixseek-plusで使用, **Then** 評価機能が正しく動作する

---

### User Story 4 - 全LLMプロバイダーの利用 (Priority: P2)

開発者がmixseek-coreでサポートされている全LLMプロバイダー（Google Gemini、Vertex AI、OpenAI、Anthropic、xAI Grok）を利用できる。

**Why this priority**: LLMプロバイダーの選択肢はユーザーの利便性に直結するため重要。

**Independent Test**: 各プロバイダーのモデルを指定してMember Agentを実行し、正常にレスポンスが得られることで検証可能。

**Acceptance Scenarios**:

1. **Given** GOOGLE_API_KEYが設定された環境, **When** `model = "google-gla:gemini-2.5-flash"` を指定してエージェントを実行, **Then** Google Geminiからレスポンスが得られる
2. **Given** ANTHROPIC_API_KEYが設定された環境, **When** `model = "anthropic:claude-sonnet-4-5-20250929"` を指定してエージェントを実行, **Then** Anthropicからレスポンスが得られる
3. **Given** OPENAI_API_KEYが設定された環境, **When** `model = "openai:gpt-4o"` を指定してエージェントを実行, **Then** OpenAIからレスポンスが得られる
4. **Given** GROK_API_KEYが設定された環境, **When** `model = "grok:grok-2-1212"` を指定してエージェントを実行, **Then** xAI Grokからレスポンスが得られる

---

### User Story 5 - データ永続化とUI確認 (Priority: P3)

開発者がチーム実行結果をDuckDBに保存し、Streamlit UIで過去の実行履歴やリーダーボードを確認できる。これはmixseek-coreの機能であり、mixseek-plusインストール後も同様に利用可能。

**Why this priority**: 実行追跡とデバッグに重要だが、基本機能の後に実装可能。

**Independent Test**: `--save-db` オプションで実行後、UIでデータが表示されることで検証可能。

**Acceptance Scenarios**:

1. **Given** 初期化されたワークスペース, **When** `mixseek team "タスク" --config team.toml --save-db` を実行, **Then** 結果がDuckDBに保存される
2. **Given** DuckDBにデータが保存された状態, **When** `mixseek ui` でUIを起動, **Then** 過去の実行履歴が表示される
3. **Given** Orchestrator実行後のDuckDB, **When** UIでリーダーボードを確認, **Then** チームごとのスコアとランキングが表示される

---

### User Story 6 - Observability（Logfire）の利用 (Priority: P3)

開発者がLogfireオプションを使用して、実行の詳細なトレースとメトリクスを収集できる。これはmixseek-coreの機能であり、mixseek-plusインストール後も同様に利用可能。

**Why this priority**: 本番運用やデバッグに有用だが、基本機能完成後に対応可能。

**Independent Test**: `--logfire` オプションで実行し、Logfireダッシュボードでトレースが確認できることで検証可能。

**Acceptance Scenarios**:

1. **Given** Logfireが設定された環境, **When** `mixseek team "タスク" --config team.toml --logfire` を実行, **Then** Logfireにトレースが送信される
2. **Given** Logfireが設定された環境, **When** `--logfire-metadata` オプションを使用, **Then** メタデータのみがLogfireに送信される
3. **Given** Logfireが設定された環境, **When** `--logfire-http` オプションを使用, **Then** HTTP通信詳細を含むトレースが送信される

---

### Edge Cases

- mixseek-coreがインストールされていない環境でmixseek-plusをインストールしようとした場合、適切なエラーメッセージと依存関係のインストールガイダンスが表示される
- MIXSEEK_WORKSPACE環境変数が未設定の場合、明確なエラーメッセージと設定方法が表示される
- 対応していないLLMプロバイダーを指定した場合、サポートされているプロバイダー一覧を含むエラーメッセージが表示される
- mixseek-coreの将来バージョンでAPIが変更された場合、非互換性を検出して警告を表示する

## Implementation Scope

### 既に完了している項目

- **pyproject.toml**: mixseek-core依存関係は既に設定済み

### 本issueで実装する項目

1. **検証テスト作成**
   - 依存関係インストールの検証テスト
   - `mixseek` CLIコマンド動作の検証テスト
   - `from mixseek import ...` APIインポートの検証テスト

2. **パッケージ基盤整備**
   - `src/mixseek_plus/__init__.py` の整備（将来の追加機能用の基盤）
   - パッケージメタデータの整備

### スコープ外（別issueで実装）

- Groqプロバイダーの追加
- Playwrightフェッチャーの追加
- その他のmixseek-plus固有機能

## Requirements *(mandatory)*

### Functional Requirements

#### 依存関係管理

- **FR-001**: `pip install mixseek-plus` により、mixseek-coreが依存関係として自動インストールされなければならない
- **FR-002**: mixseek-plusインストール後、`mixseek` CLIコマンドが利用可能でなければならない
- **FR-003**: mixseek-plusインストール後、`from mixseek import ...` でmixseek-coreの全APIがインポート可能でなければならない

#### mixseek-core機能の利用保証（mixseek-coreが提供、mixseek-plusは継承）

- **FR-010**: `mixseek` CLIで全コマンド（init, member, team, exec, config, evaluate, ui）が実行可能でなければならない
- **FR-011**: mixseek-coreの全LLMプロバイダー（Google Gemini, Vertex AI, OpenAI, Anthropic, xAI Grok）が利用可能でなければならない
- **FR-012**: mixseek-coreの既存TOML設定ファイルが変更なしで動作しなければならない
- **FR-013**: MIXSEEK_WORKSPACE環境変数が認識されなければならない
- **FR-014**: DuckDBへのデータ永続化（round_history, leader_board）が動作しなければならない
- **FR-015**: Logfireによるトレース送信（--logfire, --logfire-metadata, --logfire-http）が動作しなければならない

#### mixseek-plus固有の追加機能（**スコープ外 - 別issueで実装**）

> **注記**: 以下の要件はIssue #1のスコープ外です。将来の別issueで実装予定。
> 統合方式の設計指針として記載しています。

##### Python API（将来実装）

- **FR-020**: `mixseek_plus.create_model()` ラッパー関数を提供し、追加プロバイダー（Groq等）をサポートする。mixseek-coreのプロバイダーは内部で `mixseek.core.auth.create_authenticated_model()` に委譲する
- **FR-021**: `MemberAgentFactory.register_agent()` を使用して追加エージェント（PlaywrightFetcher等）を登録する
- **FR-022**: `mixseek_plus` パッケージから `GroqProvider`, `PlaywrightFetcher` 等の追加コンポーネントをインポート可能にする

##### TOML設定統合（将来実装）

- **FR-023**: TOML設定ファイルで `model = "groq:*"` を指定した場合、`mixseek_plus.create_model()` 経由でGroqプロバイダーが使用される
- **FR-024**: TOML設定ファイルで `type = "playwright_fetch"` を指定した場合、登録済みのPlaywrightFetcherエージェントが使用される
- **FR-025**: mixseek-plus追加機能のTOML設定は、mixseek-coreの既存設定スキーマと互換性を維持する

### Key Entities

- **Member Agent**: タスクを実行する専門エージェント。plain、web_search、web_fetch、code_executionの4タイプがある
- **Leader Agent**: 複数のMember Agentを統括し、タスクを分析・委譲するエージェント
- **Team**: 1つのLeader Agentと複数のMember Agentで構成される実行単位
- **Orchestrator**: 複数のTeamを並列実行し、最高スコアの結果を選択するコンポーネント
- **Evaluator**: Agent出力を評価し、スコアを算出するコンポーネント
- **RoundController**: マルチラウンド実行を制御するコンポーネント

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pip install mixseek-plus` により、mixseek-coreが自動インストールされる
- **SC-002**: mixseek-plusインストール後、`mixseek --help` が正常に動作する
- **SC-003**: mixseek-plusインストール後、`from mixseek import Orchestrator` が正常にインポートできる
- **SC-004**: mixseek-coreの既存TOML設定ファイルが100%互換で動作する
- **SC-005**: mixseek-coreの全LLMプロバイダー（5プロバイダー）が `mixseek` CLI経由で利用可能である

### Assumptions

- mixseek-coreはpip経由でインストール可能なPythonパッケージとして公開されている
- mixseek-coreの公開APIは安定しており、メジャーバージョン内で後方互換性が維持される
- ユーザーはPython 3.13以上の環境を使用している
- LLMプロバイダーのAPIキーはユーザーが各自で取得・設定する
- mixseek-plusは独自のCLIコマンドを提供せず、mixseek-coreの `mixseek` CLIをそのまま利用する
