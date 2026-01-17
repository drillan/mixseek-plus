# API Reference

mixseek-plusのAPI仕様です。

## Model Factory

### create_model

```python
def create_model(model_id: str) -> GroqModel | Model
```

モデルIDからLLMモデルインスタンスを作成します。

**引数**

| 名前 | 型 | 説明 |
|------|-----|------|
| `model_id` | `str` | プロバイダープレフィックス付きのモデルID |

**戻り値**

- Groqモデルの場合: `pydantic_ai.models.groq.GroqModel`
- mixseek-coreモデルの場合: 各プロバイダーのModelサブクラス

**例外**

- `ModelCreationError`: モデル作成に失敗した場合

**使用例**

```python
from mixseek_plus import create_model

# Groqモデル
model = create_model("groq:llama-3.3-70b-versatile")

# OpenAIモデル
model = create_model("openai:gpt-4o")
```

## Core Patch

### patch_core

```python
def patch_core() -> None
```

mixseek-coreの `create_authenticated_model` を拡張してGroqサポートを追加します。

Leader/EvaluatorエージェントでGroqモデルを使用する前に呼び出す必要があります。
この関数はべき等であり、複数回呼び出しても安全です。

**使用例**

```python
import mixseek_plus

mixseek_plus.patch_core()

# これでLeader/EvaluatorでGroqモデルが使用可能
from mixseek.agents.leader import LeaderConfig

config = LeaderConfig(model="groq:llama-3.3-70b-versatile", ...)
```

### check_groq_support

```python
def check_groq_support() -> None
```

Groqサポートが有効化されているか確認します。

**例外**

- `GroqNotPatchedError`: `patch_core()` が呼び出されていない場合

**使用例**

```python
from mixseek_plus import check_groq_support, patch_core, GroqNotPatchedError

try:
    check_groq_support()
except GroqNotPatchedError:
    patch_core()
```

## Agents

### register_groq_agents

```python
def register_groq_agents() -> None
```

Groqエージェントを `MemberAgentFactory` に登録します。
TOML設定で `groq_plain` および `groq_web_search` タイプを使用する前に呼び出す必要があります。

この関数はべき等であり、複数回呼び出しても安全です。

**使用例**

```python
from mixseek_plus import register_groq_agents

register_groq_agents()

# これでTOML設定でgroq_plain/groq_web_searchが使用可能
```

### GroqPlainAgent

```python
class GroqPlainAgent(BaseGroqAgent)
```

シンプルなテキスト応答を行うGroq Memberエージェントです。

**コンストラクタ**

```python
def __init__(self, config: MemberAgentConfig) -> None
```

| 引数 | 型 | 説明 |
|------|-----|------|
| `config` | `MemberAgentConfig` | エージェント設定 |

**例外**

- `ValueError`: モデル作成に失敗した場合（APIキー未設定など）

### GroqWebSearchAgent

```python
class GroqWebSearchAgent(BaseGroqAgent)
```

Web検索機能を持つGroq Memberエージェントです。
`GROQ_API_KEY` と `TAVILY_API_KEY` の両方が必要です。

**コンストラクタ**

```python
def __init__(self, config: MemberAgentConfig) -> None
```

| 引数 | 型 | 説明 |
|------|-----|------|
| `config` | `MemberAgentConfig` | エージェント設定 |

**例外**

- `ValueError`: 認証に失敗した場合（APIキー未設定など）

## Exceptions

### ModelCreationError

```python
class ModelCreationError(Exception)
```

モデル作成時のエラーを表す例外です。

**属性**

| 名前 | 型 | 説明 |
|------|-----|------|
| `provider` | `str \| None` | エラーが発生したプロバイダー |
| `suggestion` | `str` | ユーザーへの解決策の提案 |

**コンストラクタ**

```python
def __init__(
    self,
    message: str,
    provider: str | None = None,
    suggestion: str = "",
) -> None
```

### GroqNotPatchedError

```python
class GroqNotPatchedError(Exception)
```

`patch_core()` を呼び出さずにLeader/EvaluatorでGroqモデルを使用しようとした場合に発生する例外です。

**コンストラクタ**

```python
def __init__(self, message: str | None = None) -> None
```

`message` を省略すると、解決方法を含むデフォルトメッセージが使用されます。

### TavilySearchError

```python
from mixseek_plus.agents.groq_web_search_agent import TavilySearchError
```

```python
class TavilySearchError(Exception)
```

Tavily検索が失敗した場合に発生する例外です。`GroqWebSearchAgent` の使用時に発生する可能性があります。

この例外は以下のケースでラップされます：
- 認証エラー（無効なAPIキー）
- レート制限エラー
- ネットワークエラー
- 無効なレスポンス形式

**属性**

| 名前 | 型 | 説明 |
|------|-----|------|
| `original_error` | `Exception \| None` | 元となった例外 |

**コンストラクタ**

```python
def __init__(self, message: str, original_error: Exception | None = None) -> None
```
