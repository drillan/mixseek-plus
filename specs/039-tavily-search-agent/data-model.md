# Data Model: Tavily汎用検索エージェント

**Date**: 2026-01-20
**Status**: Complete

## 1. エンティティ概要

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Infrastructure Layer                          │
├─────────────────────────────────────────────────────────────────────┤
│  TavilyAPIClient                                                    │
│  ├── TavilySearchResult                                             │
│  ├── TavilyExtractResult                                            │
│  └── TavilyAPIError                                                 │
└─────────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Domain Layer                                   │
├─────────────────────────────────────────────────────────────────────┤
│  TavilyToolsRepositoryMixin                                         │
│  └── TavilySearchDeps                                               │
└─────────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Application Layer                              │
├─────────────────────────────────────────────────────────────────────┤
│  GroqTavilySearchAgent        ClaudeCodeTavilySearchAgent           │
└─────────────────────────────────────────────────────────────────────┘
```

## 2. Infrastructure Layer エンティティ

### 2.1 TavilySearchResult

Web検索結果を表すデータ構造。

```python
from pydantic import BaseModel, Field

class TavilySearchResultItem(BaseModel):
    """単一の検索結果アイテム"""
    title: str = Field(..., description="検索結果のタイトル")
    url: str = Field(..., description="検索結果のURL")
    content: str = Field(..., description="コンテンツの概要")
    score: float = Field(..., description="関連度スコア (0.0-1.0)")
    raw_content: str | None = Field(default=None, description="生HTMLコンテンツ (include_raw_content=True時)")

class TavilySearchResult(BaseModel):
    """Web検索結果全体"""
    query: str = Field(..., description="検索クエリ")
    answer: str | None = Field(default=None, description="AI生成回答 (include_answer=True時)")
    results: list[TavilySearchResultItem] = Field(default_factory=list, description="検索結果リスト")
    images: list[str] | None = Field(default=None, description="画像URL群 (include_images=True時)")
    response_time: float = Field(..., description="API応答時間（秒）")
```

### 2.2 TavilyExtractResult

URL群からのコンテンツ抽出結果。

```python
class TavilyExtractResultItem(BaseModel):
    """単一のURL抽出結果"""
    url: str = Field(..., description="抽出元URL")
    raw_content: str = Field(..., description="抽出されたコンテンツ")

class TavilyExtractFailedItem(BaseModel):
    """抽出失敗アイテム"""
    url: str = Field(..., description="失敗したURL")
    error: str = Field(..., description="エラーメッセージ")

class TavilyExtractResult(BaseModel):
    """URL抽出結果全体"""
    results: list[TavilyExtractResultItem] = Field(default_factory=list, description="成功した抽出結果")
    failed_results: list[TavilyExtractFailedItem] = Field(default_factory=list, description="失敗した抽出結果")
    response_time: float = Field(..., description="API応答時間（秒）")
```

### 2.3 TavilyAPIError

Tavily API呼び出しエラー。

```python
class TavilyAPIError(Exception):
    """Tavily API呼び出しエラー"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_type: str = "API_ERROR",
        is_retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type  # AUTH_ERROR, RATE_LIMIT_ERROR, SERVER_ERROR, TIMEOUT_ERROR, NETWORK_ERROR
        self.is_retryable = is_retryable
```

**エラータイプ一覧**:

| error_type | HTTPステータス | is_retryable | 説明 |
|------------|--------------|--------------|------|
| AUTH_ERROR | 401 | False | 認証失敗（APIキー無効） |
| RATE_LIMIT_ERROR | 429 | True | レート制限超過 |
| SERVER_ERROR | 500 | True | サーバー内部エラー |
| SERVICE_UNAVAILABLE | 503 | True | サービス一時停止 |
| TIMEOUT_ERROR | N/A | True | タイムアウト |
| NETWORK_ERROR | N/A | True | ネットワークエラー |
| VALIDATION_ERROR | 400 | False | 入力バリデーションエラー |

### 2.4 TavilyAPIClient

Tavily公式APIのラッパークラス。

```python
from dataclasses import dataclass
from tavily import AsyncTavilyClient

@dataclass
class TavilyAPIClient:
    """Tavily公式APIとの通信を担当するラッパークラス"""

    api_key: str
    timeout: float = 30.0  # NFR-001準拠
    max_retries: int = 3   # NFR-002準拠
    base_delay: float = 1.0
    max_delay: float = 10.0  # 最大待機時間

    _client: AsyncTavilyClient = field(init=False)

    def __post_init__(self) -> None:
        self._client = AsyncTavilyClient(api_key=self.api_key)

    async def search(
        self,
        query: str,
        *,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
    ) -> TavilySearchResult:
        """Web検索を実行"""
        ...

    async def extract(
        self,
        urls: list[str],
    ) -> TavilyExtractResult:
        """URL群からコンテンツを抽出"""
        ...

    async def get_search_context(
        self,
        query: str,
        *,
        search_depth: str = "basic",
        max_results: int = 5,
        max_tokens: int | None = None,
    ) -> str:
        """RAG用検索コンテキストを取得"""
        ...
```

## 3. Domain Layer エンティティ

### 3.1 TavilySearchDeps

依存性注入用dataclass。Groq/ClaudeCode両エージェントで共有。

```python
from dataclasses import dataclass
from mixseek_core import MemberAgentConfig

@dataclass
class TavilySearchDeps:
    """Tavily検索エージェント用依存性"""
    config: MemberAgentConfig
    tavily_client: TavilyAPIClient
```

### 3.2 TavilyToolsRepositoryMixin

エージェントにTavilyツールを登録するMixin。

```python
from typing import Protocol, TYPE_CHECKING, Callable, Any
from pydantic_ai import Agent, RunContext

if TYPE_CHECKING:
    from mixseek_core import MemberAgentLogger

class TavilyAgentProtocol(Protocol):
    """TavilyToolsRepositoryMixinが期待するエージェントインターフェース"""

    @property
    def logger(self) -> "MemberAgentLogger": ...

    def _get_agent(self) -> Agent[TavilySearchDeps, str]: ...

class TavilyToolsRepositoryMixin:
    """エージェントにTavilyツールを登録するMixin"""

    def _register_tavily_tools(self: TavilyAgentProtocol) -> list[Callable[..., Any]]:
        """Tavilyツールをエージェントに登録し、登録したツール関数のリストを返す"""

        agent = self._get_agent()
        tools: list[Callable[..., Any]] = []

        @agent.tool
        async def tavily_search(
            ctx: RunContext[TavilySearchDeps],
            query: str,
            search_depth: str = "basic",
            max_results: int = 5,
        ) -> str:
            """Web検索を実行"""
            ...

        @agent.tool
        async def tavily_extract(
            ctx: RunContext[TavilySearchDeps],
            urls: list[str],
        ) -> str:
            """URL群からコンテンツを抽出"""
            ...

        @agent.tool
        async def tavily_context(
            ctx: RunContext[TavilySearchDeps],
            query: str,
            max_tokens: int | None = None,
        ) -> str:
            """RAG用検索コンテキストを取得"""
            ...

        tools.extend([tavily_search, tavily_extract, tavily_context])
        return tools
```

## 4. Application Layer エンティティ

### 4.1 GroqTavilySearchAgent

Groqモデル + Tavilyツールのエージェント。

```python
from mixseek_plus.agents.base_groq_agent import BaseGroqAgent
from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin

class GroqTavilySearchAgent(TavilyToolsRepositoryMixin, BaseGroqAgent):
    """Groqモデル + Tavilyツールのエージェント"""

    def __init__(self, config: MemberAgentConfig) -> None:
        super().__init__(config)
        self._tavily_client = self._create_tavily_client()
        self._register_tavily_tools()

    def _create_tavily_client(self) -> TavilyAPIClient:
        """TavilyAPIClientを作成"""
        ...

    def _create_deps(self) -> TavilySearchDeps:
        """依存性を作成"""
        return TavilySearchDeps(
            config=self.config,
            tavily_client=self._tavily_client,
        )
```

### 4.2 ClaudeCodeTavilySearchAgent

ClaudeCodeモデル + Tavilyツールのエージェント。

```python
from mixseek_plus.agents.base_claudecode_agent import BaseClaudeCodeAgent
from mixseek_plus.agents.mixins.tavily_tools import TavilyToolsRepositoryMixin

class ClaudeCodeTavilySearchAgent(TavilyToolsRepositoryMixin, BaseClaudeCodeAgent):
    """ClaudeCodeモデル + Tavilyツールのエージェント"""

    def __init__(self, config: MemberAgentConfig) -> None:
        super().__init__(config)
        self._tavily_client = self._create_tavily_client()
        self._tavily_tools = self._register_tavily_tools()
        self._register_toolsets_if_claudecode()  # MCP統合

    def _create_tavily_client(self) -> TavilyAPIClient:
        """TavilyAPIClientを作成"""
        ...

    def _create_deps(self) -> TavilySearchDeps:
        """依存性を作成"""
        return TavilySearchDeps(
            config=self.config,
            tavily_client=self._tavily_client,
        )

    def _register_toolsets_if_claudecode(self) -> None:
        """ClaudeCodeModel用にMCPツールとして登録"""
        from claudecode_model import ClaudeCodeModel
        if isinstance(self._model, ClaudeCodeModel):
            wrapped_tools = [self._wrap_tool_for_mcp(tool) for tool in self._tavily_tools]
            self._model.set_agent_toolsets(wrapped_tools)
```

## 5. TypedDict定義（types.py拡張）

```python
from typing import TypedDict

class TavilySearchResultItemDict(TypedDict, total=False):
    """検索結果アイテムの辞書型"""
    title: str
    url: str
    content: str
    score: float
    raw_content: str | None

class TavilySearchResultDict(TypedDict, total=False):
    """検索結果全体の辞書型"""
    query: str
    answer: str | None
    results: list[TavilySearchResultItemDict]
    images: list[str] | None
    response_time: float

class TavilyExtractResultItemDict(TypedDict, total=False):
    """抽出結果アイテムの辞書型"""
    url: str
    raw_content: str

class TavilyExtractFailedItemDict(TypedDict, total=False):
    """抽出失敗アイテムの辞書型"""
    url: str
    error: str

class TavilyExtractResultDict(TypedDict, total=False):
    """抽出結果全体の辞書型"""
    results: list[TavilyExtractResultItemDict]
    failed_results: list[TavilyExtractFailedItemDict]
    response_time: float
```

## 6. 状態遷移図

### 6.1 TavilyAPIClient リトライ状態

```
┌─────────┐
│  IDLE   │
└────┬────┘
     │ request()
     ▼
┌─────────────┐   success    ┌──────────┐
│  EXECUTING  │────────────→│  SUCCESS │
└─────┬───────┘              └──────────┘
      │
      │ error (is_retryable=True, retries < max_retries)
      ▼
┌─────────────┐   exponential backoff
│  RETRYING   │────────────────────────┐
└─────────────┘                        │
      ▲                                │
      │                                │
      └────────────────────────────────┘
      │
      │ error (is_retryable=False OR retries >= max_retries)
      ▼
┌──────────┐
│  FAILED  │
└──────────┘
```

### 6.2 リトライパラメータ

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| max_retries | 3 | 最大リトライ回数 |
| base_delay | 1.0秒 | 初回リトライ待機時間 |
| max_delay | 10.0秒 | 最大待機時間 |
| backoff_multiplier | 2 | 指数バックオフ係数 |

**待機時間計算**: `min(base_delay * (2 ** retry_count), max_delay)`

## 7. バリデーションルール

### 7.1 入力バリデーション

| フィールド | ルール |
|-----------|-------|
| query (search/context) | 空文字禁止、最大1000文字 |
| urls (extract) | 空リスト禁止、各URLはhttp/https必須 |
| search_depth | "basic" または "advanced" のみ |
| max_results | 1以上20以下 |
| max_tokens (context) | 1以上、None許容 |

### 7.2 出力バリデーション

- `TavilySearchResult.results`: 空リスト許容（結果0件時）
- `TavilyExtractResult.results`: 空リスト許容（全URL失敗時）
- `score`: 0.0以上1.0以下

## 8. ファイル配置

| エンティティ | ファイル |
|-------------|---------|
| TavilySearchResult, TavilyExtractResult | `src/mixseek_plus/providers/tavily_client.py` |
| TavilyAPIError | `src/mixseek_plus/errors.py` |
| TavilyAPIClient | `src/mixseek_plus/providers/tavily_client.py` |
| TavilySearchDeps | `src/mixseek_plus/agents/mixins/tavily_tools.py` |
| TavilyToolsRepositoryMixin | `src/mixseek_plus/agents/mixins/tavily_tools.py` |
| GroqTavilySearchAgent | `src/mixseek_plus/agents/groq_tavily_search_agent.py` |
| ClaudeCodeTavilySearchAgent | `src/mixseek_plus/agents/claudecode_tavily_search_agent.py` |
| TypedDict定義 | `src/mixseek_plus/types.py` |
