# Getting Started

mixseek-plusを使い始めるためのガイドです。

## インストール

```bash
# 基本インストール
pip install mixseek-plus

# Playwright Web Fetcher機能を使用する場合
pip install mixseek-plus[playwright]
playwright install chromium
```

## 環境変数の設定

### プロバイダー別の要件

| プロバイダー | 必要な環境変数 | 説明 |
|--------------|----------------|------|
| Groq | `GROQ_API_KEY` | Groq APIキー（[console.groq.com](https://console.groq.com)で取得） |
| ClaudeCode | なし | Claude Code CLIのセッション認証を使用（APIキー不要） |

### オプション

| 変数名 | 説明 |
|--------|------|
| `TAVILY_API_KEY` | GroqでWeb検索機能を使用する場合に必要 |

```bash
# Groqを使用する場合
export GROQ_API_KEY="your-groq-api-key"
export TAVILY_API_KEY="your-tavily-api-key"  # Web検索を使う場合

# ClaudeCodeを使用する場合は環境変数不要
# Claude Code CLIがインストール・認証済みであることを確認
claude --version
```

## 最初のコード例

### Groqモデルの作成

```python
import mixseek_plus

# Groqモデルインスタンスを作成
model = mixseek_plus.create_model("groq:llama-3.3-70b-versatile")

# pydantic-aiのAgentで使用
from pydantic_ai import Agent

agent = Agent(model=model, output_type=str)
result = agent.run_sync("Hello, world!")
print(result.output)
```

### ClaudeCodeモデルの作成

```python
import mixseek_plus

# ClaudeCodeモデルインスタンスを作成（APIキー不要）
model = mixseek_plus.create_model("claudecode:claude-sonnet-4-5")

# 他のサポートモデル
model_haiku = mixseek_plus.create_model("claudecode:claude-haiku-4-5")
model_opus = mixseek_plus.create_model("claudecode:claude-opus-4-5")

# pydantic-aiのAgentで使用
from pydantic_ai import Agent

agent = Agent(model=model, output_type=str)
result = agent.run_sync("Hello, world!")
print(result.output)
```

### Memberエージェントの登録と使用

```python
import mixseek_plus

# Groqエージェントタイプを登録
mixseek_plus.register_groq_agents()

# ClaudeCodeエージェントタイプを登録
mixseek_plus.register_claudecode_agents()

# Playwrightエージェントタイプを登録（要: pip install mixseek-plus[playwright]）
mixseek_plus.register_playwright_agents()

# これでTOML設定で以下のタイプが使用可能
# - groq_plain, groq_web_search（Groq）
# - claudecode_plain（ClaudeCode）
# - playwright_markdown_fetch（Playwright Web Fetcher）
```

### Leader/Evaluatorでの使用

```python
import mixseek_plus

# patch_coreを呼び出してGroq/ClaudeCodeサポートを有効化
mixseek_plus.patch_core()

# これでLeader/EvaluatorでGroq/ClaudeCodeモデルが使用可能
from mixseek.agents.leader import LeaderConfig

# Groqを使用
config_groq = LeaderConfig(
    model="groq:llama-3.3-70b-versatile",
    # ...
)

# ClaudeCodeを使用
config_claudecode = LeaderConfig(
    model="claudecode:claude-sonnet-4-5",
    # ...
)
```

## 次のステップ

- [User Guide](user-guide.md) - 詳細な使用方法
- [API Reference](api-reference.md) - API仕様
