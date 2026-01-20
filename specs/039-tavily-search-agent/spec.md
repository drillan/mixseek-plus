# Feature Specification: Tavily汎用検索エージェント

**Feature Branch**: `039-tavily-search-agent`
**Created**: 2026-01-20
**Status**: Draft
**Input**: GitHub Issue #39 - TAVILY APIを使った汎用検索エージェントの追加

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Groq版Tavily検索エージェントでWeb検索を実行 (Priority: P1)

開発者として、GroqモデルとTavily検索を組み合わせたエージェントを使用して、Web検索を実行し、リサーチ結果を取得したい。

**Why this priority**: Web検索は最も基本的で頻繁に使用される機能であり、これがなければTavily統合の価値を実現できない。

**Independent Test**: TOML設定でtavily_searchタイプのエージェントを定義し、検索クエリを送信して結果が返却されることを確認する。

**Acceptance Scenarios**:

1. **Given** Tavily APIキーが設定されている, **When** ユーザーが`tavily_search`ツールで検索クエリを送信する, **Then** 検索結果（タイトル、URL、コンテンツ概要）が返却される
2. **Given** Tavily APIキーが設定されている, **When** 検索結果の詳細度（basic/advanced）を指定する, **Then** 指定した詳細度に応じた結果が返却される
3. **Given** Tavily APIキーが設定されている, **When** 検索結果数を指定する, **Then** 指定した数の結果が返却される
4. **Given** Tavily APIキーが無効または未設定, **When** 検索クエリを送信する, **Then** 認証エラーメッセージが返却される

---

### User Story 2 - ClaudeCode版Tavily検索エージェントでWeb検索を実行 (Priority: P1)

開発者として、ClaudeCodeモデルとTavily検索を組み合わせたエージェントを使用して、Web検索を実行し、リサーチ結果を取得したい。

**Why this priority**: GroqとClaudeCodeの両方をサポートすることがIssueの主要要件であり、どちらか一方だけでは要件を満たせない。

**Independent Test**: TOML設定でclaudecode_tavily_searchタイプのエージェントを定義し、検索クエリを送信して結果が返却されることを確認する。

**Acceptance Scenarios**:

1. **Given** Tavily APIキーとClaudeCode環境が設定されている, **When** ユーザーが`tavily_search`ツールで検索クエリを送信する, **Then** 検索結果（タイトル、URL、コンテンツ概要）が返却される
2. **Given** Tavily APIキーが設定されている, **When** 検索結果の詳細度（basic/advanced）を指定する, **Then** 指定した詳細度に応じた結果が返却される
3. **Given** Tavily APIキーが無効または未設定, **When** 検索クエリを送信する, **Then** 認証エラーメッセージが返却される

---

### User Story 3 - URLからコンテンツを抽出 (Priority: P2)

開発者として、指定したURLのリストからコンテンツを抽出し、詳細な情報を取得したい。

**Why this priority**: `tavily_extract`はTavilyの追加機能であり、基本的なWeb検索が動作してから実装すべき。

**Independent Test**: `tavily_extract`ツールにURL群を渡し、各URLのコンテンツが抽出されることを確認する。

**Acceptance Scenarios**:

1. **Given** 有効なURLリストが存在する, **When** ユーザーが`tavily_extract`ツールでURLを指定する, **Then** 各URLからコンテンツが抽出されて返却される
2. **Given** 一部無効なURLが含まれている, **When** ユーザーが`tavily_extract`ツールでURLを指定する, **Then** 有効なURLのコンテンツのみ返却され、無効なURLは適切にエラーハンドリングされる

---

### User Story 4 - RAG用検索コンテキストを取得 (Priority: P2)

開発者として、クエリに対するRAG（検索拡張生成）用の検索コンテキストを取得し、LLMの回答品質を向上させたい。

**Why this priority**: `tavily_context`はTavilyの高度な機能であり、基本検索機能の後に実装すべき。

**Independent Test**: `tavily_context`ツールにクエリを渡し、RAG用に最適化されたコンテキスト文字列が返却されることを確認する。

**Acceptance Scenarios**:

1. **Given** Tavily APIキーが設定されている, **When** ユーザーが`tavily_context`ツールでクエリを送信する, **Then** RAG用に最適化されたコンテキスト文字列が返却される
2. **Given** Tavily APIキーが設定されている, **When** 最大トークン数を指定する, **Then** 指定したトークン数以内のコンテキストが返却される

---

### User Story 5 - 既存groq_web_searchとの後方互換性維持 (Priority: P1)

既存ユーザーとして、現在使用しているgroq_web_searchエージェントが引き続き動作することを期待する。

**Why this priority**: 後方互換性は既存ユーザーの信頼を維持するために必須。

**Independent Test**: 既存のgroq_web_search設定が変更なしで動作することを確認する。

**Acceptance Scenarios**:

1. **Given** 既存のgroq_web_search設定がある, **When** システムを更新する, **Then** 既存設定が変更なしで動作する
2. **Given** 新旧両方のエージェントタイプが存在する, **When** groq_web_searchとtavily_searchを同時に使用する, **Then** 両方が独立して正常に動作する

---

### Edge Cases

- APIキーが無効または期限切れの場合、明確なエラーメッセージを返却する
- ネットワーク障害時のタイムアウト処理とリトライ
- Tavily APIのレート制限に達した場合の適切なエラーハンドリング
- 空の検索クエリや無効なURLに対する入力バリデーション
- 検索結果が0件の場合の適切なハンドリング

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムはGroqモデル用のTavily検索エージェント（タイプ: `tavily_search`）を提供すること
- **FR-002**: システムはClaudeCodeモデル用のTavily検索エージェント（タイプ: `claudecode_tavily_search`）を提供すること
- **FR-003**: 両エージェントは`tavily_search`ツールでWeb検索を実行できること
- **FR-004**: 両エージェントは`tavily_extract`ツールでURL群からコンテンツを抽出できること
- **FR-005**: 両エージェントは`tavily_context`ツールでRAG用コンテキストを取得できること
- **FR-006**: Tavilyツールの実装は共通のMixin（TavilyToolsRepositoryMixin）として提供し、コード重複を避けること
  - **FR-006b**: Mixinは3つのツール（`tavily_search`, `tavily_extract`, `tavily_context`）を登録すること
- **FR-007**: TavilyAPIClientはTavily公式APIの全機能（search, extract, get_search_context）をラップすること
  - **FR-007a**: TavilyAPIClientはHTTPエラーをTavilyAPIErrorに変換すること
  - **FR-007b**: TavilyAPIClientはレート制限エラーを検出し、リトライ可能かを示すこと
- **FR-008**: 既存の`groq_web_search`エージェントは変更せず、後方互換性を維持すること
- **FR-009**: 両エージェントはTOML設定ファイルで定義・使用できること
- **FR-010**: APIエラー（認証失敗、レート制限、タイムアウト等）は適切なエラーメッセージで処理すること

### Non-Functional Requirements

- **NFR-001**: Tavily API呼び出しのデフォルトタイムアウトは30秒とする
- **NFR-002**: APIエラー時のリトライは最大3回とし、指数バックオフを適用する
  - **NFR-002a**: リトライ時の最大待機時間は10秒とする
  - **NFR-002b**: 初回リトライ待機時間は1秒とする
  - **NFR-002c**: バックオフ係数は2とする（1秒 → 2秒 → 4秒、上限10秒）
- **NFR-003**: ログ出力はMemberAgentLoggerを使用し、既存エージェントと統一する
- **NFR-004**: tavily_extractの1回の呼び出しで処理するURL数は最大20とする
  - **NFR-004a**: 20件を超えるURLが指定された場合、最初の20件のみ処理し、警告ログを出力する
- **NFR-005**: APIキーは環境変数（TAVILY_API_KEY）からのみ取得し、コード内にハードコードしないこと

### Key Entities

- **TavilyAPIClient**: Tavily公式APIとの通信を担当するラッパークラス。search, extract, get_search_contextメソッドを提供
- **TavilySearchResult**: Web検索結果を表すデータ構造。タイトル、URL、コンテンツ、スコア等を含む
- **TavilyExtractResult**: URL抽出結果を表すデータ構造。URL、抽出コンテンツ、メタデータを含む
- **TavilyToolsRepositoryMixin**: エージェントにTavilyツールを登録するMixin。ツール実装の共通化を担う
- **GroqTavilySearchAgent**: Groqモデル + Tavilyツールを組み合わせたエージェント
- **ClaudeCodeTavilySearchAgent**: ClaudeCodeモデル + Tavilyツールを組み合わせたエージェント

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ユーザーはTOML設定で`tavily_search`または`claudecode_tavily_search`タイプを指定するだけでTavily検索エージェントを使用開始できる
- **SC-002**: 3つの全Tavilyツール（`tavily_search`, `tavily_extract`, `tavily_context`）が両エージェントで利用可能である
- **SC-003**: 既存の`groq_web_search`設定は変更なしで引き続き動作する
- **SC-004**: すべてのユニットテストがパスし、カバレッジは主要機能をカバーする
- **SC-005**: mypy strictモードで型エラーが発生しない
- **SC-006**: ruffによるLintチェックがクリアである
- **SC-007**: 将来的に新しいLLMプロバイダー（Gemini, OpenAI等）を追加する際、TavilyToolsRepositoryMixinを継承するだけでTavily機能を利用できる

## Clarifications

### Session 2026-01-20

- Q: Tavilyエージェントのツール名をどのように命名しますか？ → A: Tavily固有の名前に変更: `tavily_search`, `tavily_extract`, `tavily_context`
- Q: 非機能要件（タイムアウト、リトライ、ロギング）を追加しますか？ → A: 追加する（タイムアウト30秒、リトライ3回指数バックオフ、MemberAgentLogger使用）
- Q: TavilyAPIClientにエラー変換とリトライ可能性の検出責務を追加しますか？ → A: 追加する（FR-007a: HTTPエラー→TavilyAPIError変換、FR-007b: リトライ可能性の検出）
- Q: Mixinのインターフェースを明確化するサブ要件を追加しますか？ → A: FR-006bのみ追加（3ツール登録を明記、メソッド名は計画フェーズで決定）
- Q: 認証エラーシナリオをAcceptance Scenariosに追加しますか？ → A: User Story 1/2両方に追加

## Assumptions

- Tavily APIキーは環境変数`TAVILY_API_KEY`で提供される
- ネットワーク接続が利用可能である
- Tavily APIの利用料金・制限はユーザーの責任範囲である
- pydantic-aiフレームワークを使用したエージェント実装パターンに従う
- 非同期（async/await）パターンを使用する
