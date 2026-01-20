# mixseek-plus

mixseek-coreの拡張パッケージ。Groqモデルサポート、Playwrightフェッチ機能強化、ClaudeCodeモデル対応などの追加機能を提供。

## インストール

### 基本インストール

```bash
pip install git+https://github.com/drillan/mixseek-plus
```

### Playwright機能を使用する場合

```bash
pip install "git+https://github.com/drillan/mixseek-plus#egg=mixseek-plus[playwright]"
playwright install chromium
```

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `GROQ_API_KEY` | Groq使用時 | Groq APIキー |
| `TAVILY_API_KEY` | Tavily使用時 | Tavily検索エージェント利用に必要 |

## クイックスタート

### Groqエージェント

```python
import mixseek_plus

# Groqモデルの作成
model = mixseek_plus.create_model("groq:llama-3.3-70b-versatile")

# Leader/Evaluatorでの使用（patch_core が必要）
mixseek_plus.patch_core()

# TOMLファイルでgroq_plain/groq_web_searchを使う場合
mixseek_plus.register_groq_agents()
```

```toml
# team.toml

# Leaderの設定（patch_core()が必要）
[leader]
model = "groq:llama-3.3-70b-versatile"

# Memberエージェントの設定
[[members]]
name = "groq-assistant"
type = "groq_plain"
model = "groq:llama-3.3-70b-versatile"

[[members]]
name = "web-searcher"
type = "groq_web_search"
model = "groq:llama-3.3-70b-versatile"
```

### Tavily検索エージェント

Tavily APIを使用したWeb検索、コンテンツ抽出、RAGコンテキスト生成が可能なエージェント。
Groq版とClaudeCode版の2種類があります。

```python
from mixseek_plus import patch_core
from mixseek_plus.agents import register_groq_agents, register_tavily_agents

patch_core()
register_groq_agents()
register_tavily_agents()
```

```toml
# team.toml

# Groq版 Tavily検索エージェント
[[members]]
name = "tavily-researcher"
type = "tavily_search"
model = "groq:llama-3.3-70b-versatile"
system_prompt = """
リサーチアシスタントです。以下のツールを使用:
- tavily_search: Web検索
- tavily_extract: URL群からコンテンツ抽出
- tavily_context: RAG用コンテキスト生成
"""

# ClaudeCode版 Tavily検索エージェント
[[members]]
name = "tavily-claude"
type = "claudecode_tavily_search"
model = "claudecode:claude-sonnet-4-5"
system_prompt = "ClaudeCodeとTavily検索を組み合わせたリサーチャーです。"
```

#### Tavilyツール

| ツール | 機能 |
|--------|------|
| `tavily_search` | Web検索（詳細度・結果数調整可能） |
| `tavily_extract` | URL群からコンテンツ抽出 |
| `tavily_context` | RAG用コンテキスト生成 |

### Playwright Webフェッチャー

Playwrightを使用してWebページを取得し、MarkItDownでMarkdown形式に変換するエージェント。

```python
from mixseek_plus import patch_core
from mixseek_plus.agents import register_playwright_agents

patch_core()
register_playwright_agents()
```

```toml
# team.toml

[[members]]
name = "web-fetcher"
type = "playwright_markdown_fetch"
model = "groq:llama-3.3-70b-versatile"
system_prompt = "Webページを取得して分析するアシスタントです。"

[members.playwright]
headless = true
timeout_ms = 30000
wait_for_load_state = "networkidle"
```

#### Playwright設定オプション

| オプション | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `headless` | bool | `true` | ヘッドレスモードで実行（`false`でボット対策回避） |
| `timeout_ms` | int | `30000` | タイムアウト（ミリ秒） |
| `wait_for_load_state` | string | `"load"` | 待機条件（`load`/`domcontentloaded`/`networkidle`） |
| `retry_count` | int | `0` | リトライ回数 |
| `retry_delay_ms` | int | `1000` | リトライ遅延（ミリ秒、指数バックオフ適用） |
| `block_resources` | list | `null` | ブロックするリソース（`image`/`font`/`stylesheet`等） |

### CLIの使用

```bash
# チーム実行
mixseek-plus team "タスク" --config team.toml
# または短縮形
mskp team "タスク" --config team.toml
```

## 主要機能

- **mixseek-core継承** - mixseek-coreの全機能を利用可能
- **Groqモデルサポート**
  - `create_model("groq:...")` でGroqモデル作成
  - `groq_plain`, `groq_web_search` エージェント
  - Leader/EvaluatorへのGroq統合（`patch_core()`）
- **Tavily検索エージェント**
  - `tavily_search` (Groq版), `claudecode_tavily_search` (ClaudeCode版)
  - Web検索、コンテンツ抽出、RAGコンテキスト生成
  - 3つのツール: `tavily_search`, `tavily_extract`, `tavily_context`
- **Playwright Webフェッチャー**
  - `playwright_markdown_fetch` エージェント
  - ボット対策サイト対応（headedモード）
  - MarkItDownによるHTML→Markdown変換
  - リトライ、リソースブロック機能
- **ClaudeCodeモデルサポート**
  - `claudecode:` プロバイダー対応
  - Claude Code組み込みツール利用可能

## ドキュメント

- [Getting Started](./docs/getting-started.md) - 導入ガイド
- [User Guide](./docs/user-guide.md) - 使用方法の詳細
- [API Reference](./docs/api-reference.md) - API仕様

## ライセンス

TBD
