# Feature Specification: Playwright + MarkItDown統合Webフェッチャー

**Feature Branch**: `031-playwright-markdown-fetch`
**Created**: 2026-01-19
**Status**: Draft
**Input**: GitHub Issue #31 - Playwright + MarkItDownを統合したWebフェッチャーエージェントの実装

## Clarifications

### Session 2026-01-19

- Q: エージェントの利用モデルプロバイダーは？ → A: 任意のモデル対応（新しい基底クラスを作成、model設定で任意のプロバイダーを指定）
- Q: mixseek-coreへのエージェント登録方式は？ → A: MemberAgentFactory.register_agent()を使用（mixseek-core標準パターン、TOML typeから自動解決）
- Q: fetch_pageツールの動作モードは？ → A: ツールモード（LLMがfetch_pageツールを呼び出し、URLを渡してMarkdownを取得）
- Q: Playwrightブラウザのライフサイクル管理は？ → A: エージェント単位で保持（エージェント初期化時に起動、エージェント終了時に終了）

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 基本的なWebページ取得とMarkdown変換 (Priority: P1)

開発者として、Playwright統合エージェントを使用してWebページを取得し、LLMが解釈しやすいMarkdown形式でコンテンツを受け取りたい。これにより、動的コンテンツを含むページでも適切に処理できる。

**Why this priority**: コア機能であり、他のすべての機能の基盤となる。この機能がなければエージェント自体が利用できない。

**Independent Test**: `type = "playwright_markdown_fetch"`でエージェントを設定し、静的サイト（例：docs.python.org）からコンテンツを取得してMarkdown形式で返却されることを確認できる。

**Acceptance Scenarios**:

1. **Given** TOML設定で`type = "playwright_markdown_fetch"`のエージェントが定義されている, **When** エージェントがURLを受け取って実行される, **Then** ページコンテンツがMarkdown形式で返却される
2. **Given** 有効なURLが指定されている, **When** ページを取得する, **Then** 見出し・リスト・テーブルなどの構造が意味的に保持されたMarkdownが生成される
3. **Given** 無効なURL（存在しないドメイン）が指定されている, **When** 取得を試みる, **Then** 適切なエラーメッセージが返却される

---

### User Story 2 - ボット対策サイトからのコンテンツ取得 (Priority: P2)

開発者として、Cloudflare等のボット対策で保護されたサイトからでもコンテンツを取得したい。headedモードでブラウザを起動することで、ボット検知を回避できる。

**Why this priority**: mixseek-core web_fetchの制限を克服する主要な差別化ポイント。この機能により、より多くのサイトからコンテンツ取得が可能になる。

**Independent Test**: headedモード（`headless = false`）でCloudflare保護サイトにアクセスし、403エラーではなくコンテンツが取得できることを確認できる。

**Acceptance Scenarios**:

1. **Given** `headless = false`でエージェントが設定されている, **When** ボット対策で保護されたサイトにアクセスする, **Then** 人間と同様にコンテンツを取得できる
2. **Given** デフォルト設定（headlessモード）でエージェントが設定されている, **When** ボット対策で保護されたサイトにアクセスする, **Then** アクセスがブロックされる可能性があることをログに記録する

---

### User Story 3 - 設定可能なタイムアウトと待機条件 (Priority: P3)

開発者として、ページ読み込みのタイムアウトや待機条件を設定したい。これにより、遅いサイトや動的にコンテンツを読み込むサイトに対応できる。

**Why this priority**: 信頼性向上のための機能。基本機能が動作した後に、より堅牢な動作を実現する。

**Independent Test**: `timeout_ms = 60000`と`wait_for_load_state = "networkidle"`を設定し、JavaScript重視のSPAサイトから完全なコンテンツが取得できることを確認できる。

**Acceptance Scenarios**:

1. **Given** `timeout_ms = 30000`が設定されている, **When** ページ読み込みが30秒を超える, **Then** タイムアウトエラーが返却される
2. **Given** `wait_for_load_state = "networkidle"`が設定されている, **When** ページを取得する, **Then** ネットワークアクティビティが落ち着くまで待機してからコンテンツを取得する
3. **Given** `wait_for_load_state = "domcontentloaded"`が設定されている, **When** ページを取得する, **Then** DOMロード完了時点でコンテンツを取得する

---

### User Story 4 - HTTPリトライ機能 (Priority: P4)

開発者として、一時的なネットワーク障害や503エラーに対して自動リトライしたい。指数バックオフにより、サーバーへの負荷を軽減しながら信頼性を向上できる。

**Why this priority**: ネットワーク障害への耐性を提供するが、基本機能とは独立して動作する追加機能。

**Independent Test**: `retry_count = 3`と`retry_delay_ms = 1000`を設定し、モックサーバーで最初の2回は503を返し、3回目で成功するシナリオをテストできる。

**Acceptance Scenarios**:

1. **Given** `retry_count = 3`が設定されている, **When** 最初のリクエストが一時的なエラー（503等）を返す, **Then** 最大3回までリトライする
2. **Given** `retry_delay_ms = 1000`が設定されている, **When** リトライする, **Then** 各リトライ間で指数バックオフ（1秒→2秒→4秒）を適用する
3. **Given** すべてのリトライが失敗した, **When** 最終結果を返す, **Then** 最後のエラーメッセージと試行回数を含むエラーが返却される

---

### User Story 5 - リソースブロック機能 (Priority: P5)

開発者として、画像やフォントなどの不要なリソースのダウンロードをブロックしたい。これにより、帯域幅を節約し、ページ読み込み時間を短縮できる。

**Why this priority**: パフォーマンス最適化機能。基本機能には影響せず、実行効率を向上させるオプション。

**Independent Test**: `block_resources = ["image", "font"]`を設定し、画像が多いページでも高速に取得できることを確認できる。

**Acceptance Scenarios**:

1. **Given** `block_resources = ["image", "font"]`が設定されている, **When** ページを取得する, **Then** 画像とフォントのリクエストがブロックされる
2. **Given** `block_resources`が設定されていない, **When** ページを取得する, **Then** すべてのリソースが通常通りダウンロードされる

---

### Edge Cases

- 接続がタイムアウトした場合：設定されたタイムアウト時間後に適切なエラーメッセージを返却
- JavaScriptエラーが発生したページ：エラーを無視してDOMの現在の状態からコンテンツを取得
- リダイレクトが発生した場合：最終的なURLのコンテンツを取得
- 空のページ（bodyが空）の場合：空のMarkdownと警告メッセージを返却
- 非HTMLコンテンツ（PDF、JSON等）：HTMLではない旨のエラーメッセージを返却
- Playwrightがインストールされていない場合：明確なエラーメッセージでインストール方法を案内

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは`playwright_markdown_fetch`タイプのMember Agentを提供しなければならない
- **FR-002**: システムはTOML設定でPlaywright固有設定（headless, timeout_ms, wait_for_load_state等）を指定可能でなければならない
- **FR-003**: システムはHTTPリトライ（指数バックオフ）に対応しなければならない
- **FR-004**: システムはリソースブロック機能（画像/フォント等を除外）を提供しなければならない
- **FR-005**: システムは取得したHTMLコンテンツをMarkItDownを使用してMarkdown形式に変換しなければならない
- **FR-006**: システムは任意のモデルプロバイダーに対応し、TOML設定の`model`フィールドで指定されたプロバイダー（groq:*, anthropic:*, openai:*等）を使用できなければならない
- **FR-007**: システムはPlaywrightをオプション依存関係として提供しなければならない
- **FR-008**: エージェントは`fetch_page`ツールを提供し、URLを受け取ってMarkdownを返却しなければならない
- **FR-009**: システムは`MemberAgentFactory.register_agent()`を使用してエージェントを登録し、TOML設定の`type`フィールドから自動解決されなければならない
- **FR-010**: Playwrightブラウザはエージェント初期化時に起動し、エージェント終了時に適切にクローズされなければならない（エージェント単位のライフサイクル管理）

### Key Entities

- **PlaywrightMarkdownFetchAgent**: Playwrightでページを取得しMarkdownに変換するMember Agent
- **PlaywrightConfig**: Playwright固有の設定（headless, timeout_ms, wait_for_load_state, retry_count, retry_delay_ms, block_resources）
- **FetchResult**: 取得結果（content: Markdown, url: 最終URL, status: 成功/失敗, error: エラーメッセージ）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `type = "playwright_markdown_fetch"`でエージェントが利用可能
- **SC-002**: headedモードでCloudflare保護サイトからコンテンツ取得可能
- **SC-003**: 取得コンテンツがMarkdown形式で返却される（見出し/リスト/テーブルの構造保持）
- **SC-004**: 単体テスト・統合テスト完備（カバレッジ90%以上）
- **SC-005**: pyproject.tomlにPlaywrightオプション依存関係が追加されている
- **SC-006**: HTML→Markdown変換により、元のHTMLと比較してトークン数が50%以上削減される

## Assumptions

- MarkItDownライブラリが安定しており、HTML→Markdown変換に適している
- Playwrightブラウザ（Chromium）がターゲット環境にインストール可能
- ユーザーはheadedモードを使用する場合、GUIが利用可能な環境で実行する
- mixseek-coreの`BaseMemberAgent`と`MemberAgentConfig`のインターフェースは安定している
- 指数バックオフのベース遅延は設定された`retry_delay_ms`を使用する

## Out of Scope

- 認証が必要なサイトへのログイン機能
- Cookie/セッション管理
- スクリーンショット取得機能
- PDF出力機能
- 複数URL同時取得（並列処理）
- ブラウザプロファイル/キャッシュの永続化
