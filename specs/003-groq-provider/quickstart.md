# Quickstart: Groqプロバイダーの利用

**Branch**: `003-groq-provider` | **Date**: 2026-01-17

## 前提条件

1. **Groq APIキーの取得**: https://console.groq.com/keys
2. **環境変数の設定**: `GROQ_API_KEY=gsk_...`

## インストール

```bash
pip install mixseek-plus
```

## 基本的な使い方

### 1. モデルの作成

```python
from mixseek_plus import create_model

# Groqモデルの作成
model = create_model("groq:llama-3.3-70b-versatile")

# pydantic-ai Agentで使用
from pydantic_ai import Agent
agent = Agent(model)
result = await agent.run("Hello, world!")
```

### 2. mixseek-coreモデルへの委譲

```python
from mixseek_plus import create_model

# OpenAIモデル（mixseek-coreに委譲）
openai_model = create_model("openai:gpt-4o")

# Anthropicモデル
anthropic_model = create_model("anthropic:claude-sonnet-4-5-20250929")

# Google Gemini
gemini_model = create_model("google-gla:gemini-2.5-flash")
```

### 3. Custom Member Agentの使用

```python
from mixseek.models.member_agent import MemberAgentConfig
from mixseek_plus.agents import GroqPlainAgent

# 設定の作成
config = MemberAgentConfig(
    name="groq-assistant",
    type="custom",
    model="groq:llama-3.3-70b-versatile",
    system_instruction="You are a helpful assistant.",
)

# エージェントの作成と実行
agent = GroqPlainAgent(config)
result = await agent.execute("What is the capital of France?")
print(result.content)
```

### 4. Leader/Evaluatorでの使用（patch_core）

```python
import mixseek_plus

# Groq対応を有効化（明示的に呼び出す必要あり）
mixseek_plus.patch_core()

# これでLeader/Evaluatorで groq: モデルが使用可能
from mixseek.agents.leader import LeaderConfig
leader_config = LeaderConfig(
    model="groq:llama-3.3-70b-versatile",
    # ...
)
```

## サポートされているモデル

### Production モデル

| モデルID | 説明 |
|----------|------|
| `groq:llama-3.3-70b-versatile` | Llama 3.3 70B（汎用） |
| `groq:llama-3.1-8b-instant` | Llama 3.1 8B（高速） |

### Preview モデル

| モデルID | 説明 |
|----------|------|
| `groq:meta-llama/llama-4-scout-17b-16e-instruct` | Llama 4 Scout |
| `groq:qwen/qwen3-32b` | Qwen3 32B |

**注**: 上記以外のモデルも`groq:model-name`形式で指定可能です。モデルの存在確認はGroq API側で行われます。

## エラーハンドリング

```python
from mixseek_plus import create_model, ModelCreationError

try:
    model = create_model("groq:llama-3.3-70b-versatile")
except ModelCreationError as e:
    print(f"エラー: {e}")
    # エラー例:
    # - [groq] GROQ_API_KEY環境変数が設定されていません
    # - [groq] GROQ_API_KEYの形式が不正です
    # - サポートされていないプロバイダー: xxx
```

## エージェント別対応状況

| エージェント | Groq対応 | 使用方法 |
|-------------|:--------:|---------|
| Leader | ✅ | `patch_core()` 後に使用 |
| Evaluator | ✅ | `patch_core()` 後に使用 |
| Member - Plain | ✅ | `GroqPlainAgent` |
| Member - Web Search | ✅ | `GroqWebSearchAgent` |
| Member - Web Fetch | ❌ | 非対応（Anthropic/Googleのみ） |
| Member - Code Execution | ❌ | 非対応（Anthropicのみ） |

## 5. CLI経由での利用

mixseek-plusをインストールすると、`mixseek`コマンドが自動的にGroq対応になります。

```bash
# 設定ファイルを指定して実行
mixseek exec --config groq-config.toml --prompt "質問内容"

# ヘルプの表示
mixseek --help

# バージョン確認
mixseek --version
```

**注意**: mixseek-plusをインストールすると、mixseek-coreの`mixseek`コマンドが上書きされます。
Groq対応以外の動作はmixseek-coreと完全に互換性があります。

## TOML設定例

```toml
[[members]]
name = "groq-assistant"
type = "groq_plain"
model = "groq:llama-3.3-70b-versatile"
system_instruction = "You are a helpful assistant."
temperature = 0.7
max_tokens = 1024
```

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|:----:|------|
| `GROQ_API_KEY` | ✓ | Groq APIキー（`gsk_`で始まる） |
