# Quickstart: Tavily汎用検索エージェント

**Date**: 2026-01-20

## 前提条件

1. Tavily APIキーを取得: https://tavily.com/
2. 環境変数を設定:

```bash
export TAVILY_API_KEY="tvly-xxxxxxxxxxxxx"
```

## 1. Groq版 Tavily検索エージェント

### 1.1 TOML設定

```toml
# mixseek.toml
[[members]]
name = "tavily-researcher"
type = "tavily_search"
model = "groq:llama-3.3-70b-versatile"
system_prompt = """
あなたはリサーチアシスタントです。
以下のツールを使用して情報収集を行います:
- tavily_search: Web検索（詳細度・結果数調整可能）
- tavily_extract: URL群からコンテンツ抽出
- tavily_context: RAG用コンテキスト生成
"""
temperature = 0.3
max_tokens = 4000
```

### 1.2 使用例

```python
import asyncio
from mixseek.agents.member.factory import MemberAgentFactory
from mixseek.agents.member.config import MemberAgentConfig
from mixseek_plus.agents import register_tavily_agents

# Tavily検索エージェントを登録
register_tavily_agents()

async def main():
    # 設定を作成
    config = MemberAgentConfig(
        name="tavily-researcher",
        type="tavily_search",
        model="groq:llama-3.3-70b-versatile",
        system_prompt="あなたはリサーチアシスタントです。",
    )

    # エージェントを作成
    agent = MemberAgentFactory.create_agent(config)

    # Web検索を実行
    result = await agent.execute(
        "Pythonの最新バージョンについて調べてください。"
    )

    print(result.content)

asyncio.run(main())
```

## 2. ClaudeCode版 Tavily検索エージェント

### 2.1 TOML設定

```toml
# mixseek.toml
[[members]]
name = "tavily-claude"
type = "claudecode_tavily_search"
model = "claudecode:claude-sonnet-4-5"
system_prompt = """
ClaudeCodeの能力とTavily検索を組み合わせたリサーチャーです。
Web検索、コンテンツ抽出、RAGコンテキスト生成が可能です。
"""
temperature = 0.5
max_tokens = 8000
```

### 2.2 使用例

```python
import asyncio
from mixseek.agents.member.factory import MemberAgentFactory
from mixseek.agents.member.config import MemberAgentConfig
from mixseek_plus.agents import register_tavily_agents, register_claudecode_agents

# エージェントを登録
register_claudecode_agents()
register_tavily_agents()

async def main():
    # 設定を作成
    config = MemberAgentConfig(
        name="tavily-claude",
        type="claudecode_tavily_search",
        model="claudecode:claude-sonnet-4-5",
        system_prompt="ClaudeCodeとTavily検索を組み合わせたリサーチャーです。",
    )

    agent = MemberAgentFactory.create_agent(config)

    # Web検索を実行
    result = await agent.execute(
        "最新のAI研究動向についてまとめてください。"
    )

    print(result.content)

asyncio.run(main())
```

## 3. ツールの直接使用

エージェントを通じてツールを呼び出す際の例:

### 3.1 tavily_search (Web検索)

```text
ユーザー: Python 3.13の新機能について調べて

エージェント: tavily_searchツールを使用してWeb検索を実行します。

[ツール呼び出し: tavily_search]
query: "Python 3.13 新機能"
search_depth: "advanced"
max_results: 5

[結果]
## 検索結果: Python 3.13 新機能

### 1. Python 3.13の新機能 - Python公式ドキュメント
URL: https://docs.python.org/ja/3.13/whatsnew/3.13.html
スコア: 0.95
Python 3.13では、インタープリタの改善、型ヒントの強化...

### 2. Python 3.13リリースノート
URL: https://www.python.org/downloads/release/python-3130/
スコア: 0.89
...
```

### 3.2 tavily_extract (コンテンツ抽出)

```text
ユーザー: このURLの内容を詳しく教えて: https://example.com/article1, https://example.com/article2

エージェント: tavily_extractツールを使用してコンテンツを抽出します。

[ツール呼び出し: tavily_extract]
urls: ["https://example.com/article1", "https://example.com/article2"]

[結果]
## コンテンツ抽出結果

### URL: https://example.com/article1
記事の全文がここに表示されます...

---

### URL: https://example.com/article2
記事の全文がここに表示されます...
```

### 3.3 tavily_context (RAG用コンテキスト)

```text
ユーザー: 量子コンピューティングについてのコンテキストを準備して

エージェント: tavily_contextツールを使用してRAG用コンテキストを取得します。

[ツール呼び出し: tavily_context]
query: "量子コンピューティング 基礎 応用"
max_tokens: 2000

[結果]
## RAG用検索コンテキスト: 量子コンピューティング 基礎 応用

量子コンピューティングは、量子力学の原理を利用した計算手法です。
従来のビット（0または1）に対し、量子ビット（キュービット）は
重ね合わせ状態を取ることができ、並列計算を可能にします...
```

## 4. Verboseモードの有効化

詳細なログを確認するには、環境変数を設定:

```bash
export MIXSEEK_VERBOSE=1
```

出力例:
```text
[VERBOSE] tavily_search started: {"query": "Python 3.13 新機能"}
[VERBOSE] tavily_search completed: success in 1234ms
```

## 5. エラーハンドリング

### 5.1 認証エラー

```text
Tavily API エラー: 認証に失敗しました。APIキーを確認してください。
エラータイプ: AUTH_ERROR
```

**対処法**: `TAVILY_API_KEY`環境変数が正しく設定されているか確認

### 5.2 レート制限

```text
Tavily API エラー: レート制限に達しました。しばらく待ってから再試行してください。
エラータイプ: RATE_LIMIT_ERROR
```

**対処法**: リトライが自動的に行われます（最大3回、指数バックオフ）

## 6. 既存groq_web_searchとの違い

| 機能 | groq_web_search | tavily_search / claudecode_tavily_search |
|------|-----------------|------------------------------------------|
| Web検索 | ✅ `web_search` | ✅ `tavily_search` |
| コンテンツ抽出 | ❌ | ✅ `tavily_extract` |
| RAGコンテキスト | ❌ | ✅ `tavily_context` |
| ClaudeCode対応 | ❌ | ✅ |
| 検索詳細度設定 | ❌ | ✅ (basic/advanced) |

**注意**: 既存の`groq_web_search`は引き続き使用可能です（後方互換性維持）。

## 7. 設定オプション

### 7.1 モデル設定

| パラメータ | 説明 | デフォルト |
|-----------|------|-----------|
| `temperature` | 生成の多様性 (0.0-1.0) | プロバイダー依存 |
| `max_tokens` | 最大出力トークン数 | プロバイダー依存 |
| `max_retries` | API呼び出しリトライ回数 | 3 |

### 7.2 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `TAVILY_API_KEY` | Tavily APIキー | Yes |
| `GROQ_API_KEY` | Groq APIキー（Groq版使用時） | Yes (Groq版) |
| `MIXSEEK_VERBOSE` | Verboseモード有効化 | No |
