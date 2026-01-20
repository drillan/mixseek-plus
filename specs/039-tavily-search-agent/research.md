# Research: Tavily汎用検索エージェント

**Date**: 2026-01-20
**Status**: Complete

## 1. 既存実装の調査

### 1.1 エージェント階層構造

```
BaseMemberAgent (mixseek-core)
├── BaseGroqAgent
│   ├── GroqPlainAgent
│   └── GroqWebSearchAgent (Tavily search機能)
├── BaseClaudeCodeAgent
│   └── ClaudeCodePlainAgent
└── BasePlaywrightAgent
    └── PlaywrightMarkdownFetchAgent
```

**PydanticAgentExecutorMixin**: Groq/Playwright両方で共有されるexecute()ロジック

### 1.2 GroqWebSearchAgentの実装パターン

**ファイル**: `src/mixseek_plus/agents/groq_web_search_agent.py`

**主要コンポーネント**:
- `GroqWebSearchDeps`: 依存性注入用dataclass（config + tavily_client）
- `web_search`ツール: `@self._agent.tool`デコレータで登録
- `_register_tools()`: ツール登録メソッド

**ツール登録パターン**:
```python
@self._agent.tool
async def web_search(ctx: RunContext[GroqWebSearchDeps], query: str) -> str:
    client = ctx.deps.tavily_client
    results = await client.search(query)
    return formatted_results
```

### 1.3 BaseClaudeCodeAgent詳細

**ファイル**: `src/mixseek_plus/agents/base_claudecode_agent.py`

**継承関係**:
```
BaseMemberAgent (mixseek-core)
└── BaseClaudeCodeAgent
    └── ClaudeCodePlainAgent
    └── ClaudeCodeTavilySearchAgent (新規)
```

**基本Depsクラス**:
```python
@dataclass
class ClaudeCodeAgentDeps:
    """Dependencies for ClaudeCode agents."""
    config: MemberAgentConfig
```

**抽象メソッド（サブクラスで実装必須）**:
```python
@abstractmethod
def _get_agent(self) -> Agent[ClaudeCodeAgentDeps, str]: ...

@abstractmethod
def _create_deps(self) -> ClaudeCodeAgentDeps: ...

@abstractmethod
def _get_agent_type_metadata(self) -> dict[str, str]: ...
```

**ClaudeCode固有エラー処理**:
```python
def _extract_api_error_details(self, error: Exception) -> tuple[str, str]:
    if isinstance(error, CLINotFoundError):
        return ("Claude Code CLI not found...", "CLI_NOT_FOUND")
    elif isinstance(error, CLIExecutionError):
        return (f"CLI execution error: {error}", "CLI_EXECUTION_ERROR")
    elif isinstance(error, CLIResponseParseError):
        return (f"Failed to parse response: {error}", "CLI_PARSE_ERROR")
    return (str(error), "EXECUTION_ERROR")
```

**execute()フロー**:
1. `log_execution_start()` でログ記録開始
2. タスク空文字チェック
3. `_create_deps()` で依存性作成
4. `self._get_agent().run(task, deps=deps)` で実行
5. 結果から `all_messages()` 取得
6. usage情報抽出（provider依存）
7. `_log_tool_calls_from_history()` でツール呼び出しログ
8. `MemberAgentResult.success()` で結果返却

**ツール設定解決（preset）**:
- `config.tool_settings.claudecode.preset` でプリセット名指定可能
- `MIXSEEK_WORKSPACE`環境変数からプリセット解決

### 1.4 ClaudeCode MCP統合パターン

**ファイル**: `src/mixseek_plus/agents/playwright_markdown_fetch_agent.py`

**重要**: ClaudeCodeModelは pydantic-aiの `@agent.tool` を直接認識しないため、MCPツールとしてラップが必要。

```python
def _register_toolsets_if_claudecode(self) -> None:
    from claudecode_model import ClaudeCodeModel
    if isinstance(self._model, ClaudeCodeModel):
        wrapped_tools = [self._wrap_tool_for_mcp(tool) for tool in tools]
        self._model.set_agent_toolsets(wrapped_tools)
```

**MCP tool命名規則**: `mcp__pydantic_tools__<tool_name>`

### 1.5 既存Mixinパターン

**ファイル**: `src/mixseek_plus/agents/mixins/execution.py`

**Protocol定義でMixinインターフェースを明示**:
```python
class AgentProtocol(Protocol):
    @property
    def agent_name(self) -> str: ...
    @property
    def logger(self) -> MemberAgentLogger: ...
    def _get_agent(self) -> Agent[object, str]: ...
    def _create_deps(self) -> object: ...
```

**Mixinが提供するメソッド**:
- `_execute_pydantic_agent()` - 共通実行ロジック
- `_extract_usage_info()` - トークン情報抽出
- `_log_tool_calls_if_verbose()` - verbose出力

## 2. Tavily API調査

### 2.1 Tavily Python SDK

**公式パッケージ**: `tavily-python`

**バージョン要件**: `>=0.7.4`

**バージョン選定根拠**:
- プロジェクト既存依存（`pyproject.toml`で定義済み）
- AsyncTavilyClientサポート（非同期処理必須）
- extract/get_search_context APIの安定サポート
- 既存GroqWebSearchAgentとの互換性確保

**主要メソッド**:
1. `search(query, **kwargs)` - Web検索
2. `extract(urls, **kwargs)` - URL群からコンテンツ抽出
3. `get_search_context(query, **kwargs)` - RAG用コンテキスト生成

### 2.2 Search APIパラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `query` | str | 検索クエリ（必須） |
| `search_depth` | str | "basic" or "advanced" |
| `max_results` | int | 結果数（default: 5, max: 20） |
| `include_answer` | bool | AI生成回答を含める |
| `include_raw_content` | bool | 生HTMLを含める |
| `include_images` | bool | 画像URLを含める |
| `include_domains` | list[str] | 対象ドメイン制限 |
| `exclude_domains` | list[str] | 除外ドメイン |

### 2.3 Extract APIパラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `urls` | list[str] | 抽出対象URL群（必須） |

### 2.4 Get Search Context APIパラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `query` | str | 検索クエリ（必須） |
| `max_tokens` | int | 最大トークン数 |
| `search_depth` | str | "basic" or "advanced" |
| `max_results` | int | 検索結果数 |

### 2.5 エラーレスポンス

| HTTPステータス | 意味 | リトライ可能 |
|---------------|------|------------|
| 401 | 認証失敗（APIキー無効） | No |
| 429 | レート制限超過 | Yes（バックオフ後） |
| 500 | サーバーエラー | Yes |
| 503 | サービス一時停止 | Yes |

## 3. 技術的決定事項

### 3.1 アーキテクチャ決定

**Decision**: 3層クリーンアーキテクチャ

```
Application Layer
├── GroqTavilySearchAgent (BaseGroqAgent + TavilyToolsRepositoryMixin)
└── ClaudeCodeTavilySearchAgent (BaseClaudeCodeAgent + TavilyToolsRepositoryMixin)

Domain Layer
└── TavilyToolsRepositoryMixin
    - register_tavily_tools(agent: Agent)
    - tavily_search, tavily_extract, tavily_context tools

Infrastructure Layer
└── TavilyAPIClient
    - search(), extract(), get_search_context()
    - HTTPエラー→TavilyAPIError変換
```

**Rationale**:
- Tavilyツール実装をMixin化することで、新プロバイダー追加時の再利用が容易
- 既存のPydanticAgentExecutorMixinパターンと一貫性
- テスト容易性向上（各層を独立テスト可能）

**Alternatives Rejected**:
- 各エージェントに直接ツール実装 → DRY違反、保守性低下

### 3.2 TavilyAPIClient設計

**Decision**: 薄いラッパークラスとして実装

```python
@dataclass
class TavilyAPIClient:
    client: AsyncTavilyClient
    timeout: float = 30.0
    max_retries: int = 3

    async def search(...) -> TavilySearchResult
    async def extract(...) -> TavilyExtractResult
    async def get_search_context(...) -> str
```

**Rationale**:
- tavily-pythonのAsyncTavilyClientを直接使用
- エラーハンドリングとリトライロジックをラップ
- Constitution Article 4（Simplicity）準拠

**Alternatives Rejected**:
- 完全な再実装 → 不必要な複雑性

### 3.3 Deps型設計

**Decision**: シンプルなdataclass

```python
@dataclass
class TavilySearchDeps:
    config: MemberAgentConfig
    tavily_client: TavilyAPIClient
```

**Rationale**:
- 既存のGroqWebSearchDepsと一貫性
- 将来的にGroqTavily/ClaudeCodeTavilyで共通Deps使用可能

### 3.4 ツール命名

**Decision**: Tavily固有の名前を使用

| ツール名 | 機能 |
|---------|------|
| `tavily_search` | Web検索 |
| `tavily_extract` | URL群からコンテンツ抽出 |
| `tavily_context` | RAG用コンテキスト取得 |

**Rationale**:
- spec.md Clarifications Session 2026-01-20で決定済み
- 機能が明確に識別可能

### 3.5 エラーハンドリング

**Decision**: カスタム例外クラス + リトライロジック

```python
class TavilyAPIError(Exception):
    """Tavily API呼び出しエラー"""
    status_code: int | None
    is_retryable: bool
    error_type: str  # AUTH_ERROR, RATE_LIMIT_ERROR, SERVER_ERROR, etc.
```

**Rationale**:
- FR-007a/FR-007b要件準拠
- 既存errors.py拡張
- リトライ可能性の明示

### 3.6 リトライ戦略

**Decision**: 指数バックオフ（NFR-002準拠）

```python
# 初回: 1秒
# 2回目: 2秒
# 3回目: 4秒
retry_delay = base_delay * (2 ** retry_count)
```

**Parameters**:
- max_retries: 3
- base_delay: 1.0秒
- max_delay: 10.0秒

### 3.7 ClaudeCode MCP統合

**Decision**: 既存パターンを踏襲

```python
def _register_toolsets_if_claudecode(self) -> None:
    if isinstance(self._model, ClaudeCodeModel):
        wrapped_tools = [self._wrap_tool_for_mcp(tool) for tool in tavily_tools]
        self._model.set_agent_toolsets(wrapped_tools)
```

**Rationale**:
- PlaywrightMarkdownFetchAgentの実装パターンと完全一致
- 動作実績あり

## 4. 後方互換性

### 4.1 既存groq_web_searchの維持

**Decision**: 変更なし

- `groq_web_search`エージェントタイプは完全に維持
- 新しい`tavily_search`は別のエージェントタイプとして追加
- ファクトリー登録は独立

**Rationale**:
- FR-008要件準拠
- 既存ユーザーへの影響ゼロ

## 5. テスト戦略

### 5.1 ユニットテスト

| テスト対象 | テストファイル |
|-----------|--------------|
| TavilyAPIClient | test_tavily_client.py |
| TavilyToolsRepositoryMixin | test_tavily_tools_mixin.py |
| GroqTavilySearchAgent | test_groq_tavily_search_agent.py |
| ClaudeCodeTavilySearchAgent | test_claudecode_tavily_search_agent.py |

### 5.2 統合テスト

- 実Tavily API呼び出しテスト（@pytest.mark.integration）
- 環境変数TAVILY_API_KEY存在チェック

## 6. 不明点解消

| 不明点 | 解決策 |
|--------|-------|
| Mixinでツール登録をどう共有するか | `register_tavily_tools(agent: Agent)` メソッドでAgent受け取り、ツール登録 |
| ClaudeCodeでのツール登録方法 | MCPツールラップパターン使用（PlaywrightMarkdownFetchAgent参照） |
| エラー型の設計 | TavilyAPIError + is_retryableフラグで統一 |
| Depsの共通化 | TavilySearchDepsを両エージェントで共有 |

## 7. 参照ファイル

| ファイル | 参照目的 |
|---------|---------|
| `src/mixseek_plus/agents/base_groq_agent.py` | Groq基底クラス構造 |
| `src/mixseek_plus/agents/base_claudecode_agent.py` | ClaudeCode基底クラス構造 |
| `src/mixseek_plus/agents/groq_web_search_agent.py` | Tavilyツール実装参考 |
| `src/mixseek_plus/agents/playwright_markdown_fetch_agent.py` | MCP統合パターン |
| `src/mixseek_plus/agents/mixins/execution.py` | Mixinパターン |
| `src/mixseek_plus/providers/tavily.py` | 認証検証実装 |
| `src/mixseek_plus/errors.py` | エラー定義 |
| `src/mixseek_plus/utils/verbose.py` | Verbose出力パターン |
