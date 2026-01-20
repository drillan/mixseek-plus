# API Contract: Tavily Tools

**Date**: 2026-01-20
**Status**: Complete

## 1. ツール一覧

| ツール名 | 機能 | FR |
|---------|------|-----|
| `tavily_search` | Web検索を実行 | FR-003 |
| `tavily_extract` | URL群からコンテンツを抽出 | FR-004 |
| `tavily_context` | RAG用検索コンテキストを取得 | FR-005 |

## 2. tavily_search

### 2.1 概要

Web検索を実行し、検索結果（タイトル、URL、コンテンツ概要、スコア）を返却する。

### 2.2 インターフェース

```python
async def tavily_search(
    ctx: RunContext[TavilySearchDeps],
    query: str,
    search_depth: str = "basic",
    max_results: int = 5,
) -> str:
    """
    Web検索を実行する。

    Args:
        ctx: 実行コンテキスト（依存性注入）
        query: 検索クエリ（必須、空文字禁止、最大1000文字）
        search_depth: 検索詳細度 ("basic" または "advanced")
        max_results: 結果数 (1-20、デフォルト: 5)

    Returns:
        検索結果をフォーマットした文字列

    Raises:
        TavilyAPIError: API呼び出しエラー（認証失敗、レート制限等）
    """
```

### 2.3 入力パラメータ

| パラメータ | 型 | 必須 | デフォルト | バリデーション |
|-----------|-----|------|-----------|--------------|
| `query` | str | Yes | - | 空文字禁止、最大1000文字 |
| `search_depth` | str | No | "basic" | "basic" または "advanced" |
| `max_results` | int | No | 5 | 1以上20以下 |

### 2.4 出力フォーマット

```text
## 検索結果: {query}

### 1. {title}
URL: {url}
スコア: {score:.2f}
{content}

### 2. {title}
URL: {url}
スコア: {score:.2f}
{content}

...
```

**結果0件時**:
```text
## 検索結果: {query}

検索結果が見つかりませんでした。
```

### 2.5 エラーハンドリング

| エラー | 原因 | 対応 |
|--------|------|------|
| `TavilyAPIError(AUTH_ERROR)` | APIキー無効 | エラーメッセージを返却 |
| `TavilyAPIError(RATE_LIMIT_ERROR)` | レート制限超過 | リトライ後もエラーならエラーメッセージ返却 |
| `TavilyAPIError(VALIDATION_ERROR)` | 入力バリデーション失敗 | エラーメッセージを返却 |

## 3. tavily_extract

### 3.1 概要

指定したURL群からコンテンツを抽出する。

### 3.2 インターフェース

```python
async def tavily_extract(
    ctx: RunContext[TavilySearchDeps],
    urls: list[str],
) -> str:
    """
    URL群からコンテンツを抽出する。

    Args:
        ctx: 実行コンテキスト（依存性注入）
        urls: 抽出対象URL群（必須、空リスト禁止、各URLはhttp/https必須）

    Returns:
        抽出結果をフォーマットした文字列

    Raises:
        TavilyAPIError: API呼び出しエラー
    """
```

### 3.3 入力パラメータ

| パラメータ | 型 | 必須 | デフォルト | バリデーション |
|-----------|-----|------|-----------|--------------|
| `urls` | list[str] | Yes | - | 下記URLバリデーション参照 |

**URLバリデーション詳細**:

| ルール | 説明 | 例（有効） | 例（無効） |
|--------|------|-----------|-----------|
| 空リスト禁止 | 最低1つのURLが必要 | `["https://example.com"]` | `[]` |
| スキーム必須 | http:// または https:// | `https://example.com` | `example.com` |
| HTTPS推奨 | セキュリティ上HTTPSを推奨 | `https://example.com` | `http://example.com`（警告のみ） |
| ホスト名必須 | 有効なドメイン名が必要 | `https://example.com/path` | `https:///path` |
| 最大URL数 | 1回の呼び出しで最大20URL | 20個以下 | 21個以上 |
| 重複排除 | 同一URLは1つにマージ | - | - |

**バリデーションエラー時の挙動**:
- 空リスト: `TavilyAPIError(VALIDATION_ERROR)` を即座に発生
- 無効なURL形式: 該当URLを `failed_results` に記録し、有効なURLのみ処理継続
- 全URL無効: 結果として空の `results` と全URLを含む `failed_results` を返却

### 3.4 出力フォーマット

```text
## コンテンツ抽出結果

### URL: {url}
{raw_content}

---

### URL: {url}
{raw_content}

---

## 失敗したURL
- {url}: {error}
- {url}: {error}
```

**全URL成功時** (失敗セクションなし):
```text
## コンテンツ抽出結果

### URL: {url}
{raw_content}
```

**全URL失敗時**:
```text
## コンテンツ抽出結果

すべてのURLからコンテンツを抽出できませんでした。

## 失敗したURL
- {url}: {error}
```

### 3.5 エラーハンドリング

| エラー | 原因 | 対応 |
|--------|------|------|
| 個別URL失敗 | アクセス不可、パース失敗 | `failed_results`に記録、他URLは処理継続 |
| `TavilyAPIError(AUTH_ERROR)` | APIキー無効 | エラーメッセージを返却 |
| `TavilyAPIError(VALIDATION_ERROR)` | 入力バリデーション失敗 | エラーメッセージを返却 |

## 4. tavily_context

### 4.1 概要

RAG（検索拡張生成）用に最適化された検索コンテキスト文字列を取得する。

### 4.2 インターフェース

```python
async def tavily_context(
    ctx: RunContext[TavilySearchDeps],
    query: str,
    max_tokens: int | None = None,
) -> str:
    """
    RAG用検索コンテキストを取得する。

    Args:
        ctx: 実行コンテキスト（依存性注入）
        query: 検索クエリ（必須、空文字禁止、最大1000文字）
        max_tokens: 最大トークン数（省略時はAPI側デフォルト）

    Returns:
        RAG用に最適化されたコンテキスト文字列

    Raises:
        TavilyAPIError: API呼び出しエラー
    """
```

### 4.3 入力パラメータ

| パラメータ | 型 | 必須 | デフォルト | バリデーション |
|-----------|-----|------|-----------|--------------|
| `query` | str | Yes | - | 空文字禁止、最大1000文字 |
| `max_tokens` | int \| None | No | None | 1以上、None許容 |

### 4.4 出力フォーマット

```text
## RAG用検索コンテキスト: {query}

{context_string}
```

### 4.5 エラーハンドリング

| エラー | 原因 | 対応 |
|--------|------|------|
| `TavilyAPIError(AUTH_ERROR)` | APIキー無効 | エラーメッセージを返却 |
| `TavilyAPIError(RATE_LIMIT_ERROR)` | レート制限超過 | リトライ後もエラーならエラーメッセージ返却 |

## 5. 共通事項

### 5.1 ログ出力

すべてのツールは以下のログを出力する:

```python
# ツール開始
log_verbose_tool_start(tool_name, {"query": query})

# ツール完了
log_verbose_tool_done(tool_name, "success", execution_time_ms)

# ツール失敗
log_verbose_tool_done(tool_name, "failed", execution_time_ms)
```

### 5.2 メトリクス計測

```python
import time

start_time = time.perf_counter()
# ... ツール実行 ...
execution_time_ms = (time.perf_counter() - start_time) * 1000
```

### 5.3 エラーメッセージフォーマット

```text
Tavily API エラー: {error_message}
エラータイプ: {error_type}
```

## 6. ClaudeCode MCP統合

ClaudeCodeTavilySearchAgentでは、ツールはMCPツールとしてラップされる。

### 6.1 MCP Tool命名

| pydantic-ai tool | MCP tool名 |
|-----------------|------------|
| `tavily_search` | `mcp__pydantic_tools__tavily_search` |
| `tavily_extract` | `mcp__pydantic_tools__tavily_extract` |
| `tavily_context` | `mcp__pydantic_tools__tavily_context` |

### 6.2 MCPツールスキーマ

```json
{
  "name": "mcp__pydantic_tools__tavily_search",
  "description": "Web検索を実行する",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "検索クエリ"
      },
      "search_depth": {
        "type": "string",
        "enum": ["basic", "advanced"],
        "default": "basic"
      },
      "max_results": {
        "type": "integer",
        "minimum": 1,
        "maximum": 20,
        "default": 5
      }
    },
    "required": ["query"]
  }
}
```

## 7. 仕様との対応

| FR | ツール | 対応状況 |
|----|--------|---------|
| FR-003 | `tavily_search` | ✅ |
| FR-004 | `tavily_extract` | ✅ |
| FR-005 | `tavily_context` | ✅ |
| FR-006 | Mixin実装 | ✅ (TavilyToolsRepositoryMixin) |
| FR-006b | 3ツール登録 | ✅ |
