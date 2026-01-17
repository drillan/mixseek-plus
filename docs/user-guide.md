# User Guide

mixseek-plusの詳細な使用方法を説明します。

## Model Factory

`create_model()` 関数を使用して、Groqまたはmixseek-core対応モデルのインスタンスを作成します。

### 基本的な使用方法

```python
from mixseek_plus import create_model

# Groqモデル
model = create_model("groq:llama-3.3-70b-versatile")
model = create_model("groq:qwen/qwen3-32b")

# mixseek-coreモデル（OpenAI、Anthropicなど）
model = create_model("openai:gpt-4o")
model = create_model("anthropic:claude-sonnet-4-5-20250929")
```

### モデルID形式

モデルIDは `provider:model-name` の形式で指定します。

| プロバイダー | 例 |
|--------------|-----|
| `groq` | `groq:llama-3.3-70b-versatile` |
| `openai` | `openai:gpt-4o` |
| `anthropic` | `anthropic:claude-sonnet-4-5-20250929` |
| `google-gla` | `google-gla:gemini-2.0-flash` |
| `google-vertex` | `google-vertex:gemini-2.0-flash` |
| `grok` | `grok:grok-2` |
| `grok-responses` | `grok-responses:grok-2` |

## Memberエージェント

mixseek-plusは2種類のGroq Memberエージェントを提供します。

### エージェントの登録

TOML設定でエージェントを使用する前に、登録が必要です。

```python
from mixseek_plus import register_groq_agents

register_groq_agents()
```

### GroqPlainAgent

シンプルなテキスト応答エージェントです。

```toml
[[members]]
name = "groq-assistant"
type = "groq_plain"
model = "groq:llama-3.3-70b-versatile"
system_instruction = "あなたは親切なアシスタントです。"
```

### GroqWebSearchAgent

Web検索機能を持つエージェントです。`TAVILY_API_KEY` が必要です。

```toml
[[members]]
name = "web-researcher"
type = "groq_web_search"
model = "groq:llama-3.3-70b-versatile"
system_instruction = "あなたは情報収集のスペシャリストです。"
```

### エージェントの設定オプション

```toml
[[members]]
name = "custom-agent"
type = "groq_plain"
model = "groq:llama-3.3-70b-versatile"
system_instruction = "エージェントへの指示"
system_prompt = "追加のシステムプロンプト"
max_retries = 3
temperature = 0.7
max_tokens = 4096
stop_sequences = ["END", "STOP"]
top_p = 0.9
seed = 42
timeout_seconds = 30.0
```

| オプション | 型 | 説明 |
|------------|-----|------|
| `system_instruction` | `str` | エージェントへの指示 |
| `system_prompt` | `str` | 追加のシステムプロンプト |
| `max_retries` | `int` | リトライ回数 |
| `temperature` | `float` | 生成の温度パラメータ |
| `max_tokens` | `int` | 最大トークン数 |
| `stop_sequences` | `list[str]` | 生成を停止するシーケンス |
| `top_p` | `float` | Top-pサンプリングの確率 |
| `seed` | `int` | 再現性のための乱数シード |
| `timeout_seconds` | `float` | リクエストタイムアウト秒数 |

## Leader/Evaluatorでの使用

Leader/EvaluatorエージェントでGroqモデルを使用するには、`patch_core()` を呼び出す必要があります。

### patch_coreの使用

```python
import mixseek_plus

# アプリケーション起動時に一度だけ呼び出す
mixseek_plus.patch_core()
```

### TOML設定例

```toml
[leader]
model = "groq:llama-3.3-70b-versatile"
max_rounds = 5

[evaluator]
model = "groq:llama-3.3-70b-versatile"

[[members]]
name = "researcher"
type = "groq_web_search"
model = "groq:llama-3.3-70b-versatile"
```

### 完全なセットアップ例

```python
import mixseek_plus

# 1. Core patchを適用
mixseek_plus.patch_core()

# 2. エージェントを登録
mixseek_plus.register_groq_agents()

# 3. これでTOML設定を使用可能
from mixseek import Team

team = Team.from_toml("team.toml")
result = team.run("タスクを実行してください")
```

## CLIの使用

```bash
# チーム実行
mixseek team "タスク" --config team.toml

# ヘルプ表示
mixseek --help
```

## トラブルシューティング

### ModelCreationError: GROQ_API_KEY...

Groq APIキーが設定されていません。

```bash
export GROQ_API_KEY="your-groq-api-key"
```

### GroqNotPatchedError

Leader/EvaluatorでGroqモデルを使用する前に `patch_core()` を呼び出してください。

```python
import mixseek_plus
mixseek_plus.patch_core()
```

### TAVILY_API_KEY...

Web検索エージェントを使用する場合は、Tavily APIキーが必要です。

```bash
export TAVILY_API_KEY="your-tavily-api-key"
```
