# Getting Started

mixseek-plusを使い始めるためのガイドです。

## インストール

```bash
pip install mixseek-plus
```

## 環境変数の設定

### 必須

| 変数名 | 説明 |
|--------|------|
| `GROQ_API_KEY` | Groq APIキー（[console.groq.com](https://console.groq.com)で取得） |

### オプション

| 変数名 | 説明 |
|--------|------|
| `TAVILY_API_KEY` | Web検索機能を使用する場合に必要 |

```bash
export GROQ_API_KEY="your-groq-api-key"
export TAVILY_API_KEY="your-tavily-api-key"  # Web検索を使う場合
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

### Memberエージェントの登録と使用

```python
import mixseek_plus

# Groqエージェントタイプを登録
mixseek_plus.register_groq_agents()

# これでTOML設定でgroq_plain/groq_web_searchが使用可能
```

### Leader/Evaluatorでの使用

```python
import mixseek_plus

# patch_coreを呼び出してGroqサポートを有効化
mixseek_plus.patch_core()

# これでLeader/EvaluatorでGroqモデルが使用可能
from mixseek.agents.leader import LeaderConfig

config = LeaderConfig(
    model="groq:llama-3.3-70b-versatile",
    # ...
)
```

## 次のステップ

- [User Guide](user-guide.md) - 詳細な使用方法
- [API Reference](api-reference.md) - API仕様
