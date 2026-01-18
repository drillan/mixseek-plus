# API Reference

mixseek-plusのAPI仕様です。

## Model Factory

### create_model

```python
def create_model(model_id: str) -> GroqModel | ClaudeCodeModel | Model
```

モデルIDからLLMモデルインスタンスを作成します。

**引数**

| 名前 | 型 | 説明 |
|------|-----|------|
| `model_id` | `str` | プロバイダープレフィックス付きのモデルID |

**戻り値**

- Groqモデルの場合: `pydantic_ai.models.groq.GroqModel`
- ClaudeCodeモデルの場合: `claudecode_model.ClaudeCodeModel`
- mixseek-coreモデルの場合: 各プロバイダーのModelサブクラス

**例外**

- `ModelCreationError`: モデル作成に失敗した場合

**使用例**

```python
from mixseek_plus import create_model

# Groqモデル
model = create_model("groq:llama-3.3-70b-versatile")

# ClaudeCodeモデル
model = create_model("claudecode:claude-sonnet-4-5")

# OpenAIモデル
model = create_model("openai:gpt-4o")
```

## Core Patch

### patch_core

```python
def patch_core() -> None
```

mixseek-coreの `create_authenticated_model` を拡張してGroqおよびClaudeCodeサポートを追加します。

Leader/EvaluatorエージェントでGroqまたはClaudeCodeモデルを使用する前に呼び出す必要があります。
この関数はべき等であり、複数回呼び出しても安全です。

**使用例**

```python
import mixseek_plus

mixseek_plus.patch_core()

# これでLeader/EvaluatorでGroq/ClaudeCodeモデルが使用可能
from mixseek.agents.leader import LeaderConfig

config = LeaderConfig(model="groq:llama-3.3-70b-versatile", ...)
config = LeaderConfig(model="claudecode:claude-sonnet-4-5", ...)
```

### configure_claudecode_tool_settings

```python
def configure_claudecode_tool_settings(settings: ClaudeCodeToolSettings) -> None
```

Leader/Evaluator/JudgmentエージェントでClaudeCodeを使用する際のツール設定を登録します。

`patch_core()` の前後どちらで呼び出しても有効です。設定は `patch_core()` によって作成されるClaudeCodeモデルに適用されます。

**引数**

| 名前 | 型 | 説明 |
|------|-----|------|
| `settings` | `ClaudeCodeToolSettings` | ClaudeCode固有のツール設定 |

**ClaudeCodeToolSettings**

| キー | 型 | 説明 |
|------|-----|------|
| `permission_mode` | `str` | パーミッションモード（`"bypassPermissions"` で確認スキップ） |
| `working_directory` | `str` | 作業ディレクトリ |
| `allowed_tools` | `list[str]` | 許可するツールのリスト |
| `disallowed_tools` | `list[str]` | 禁止するツールのリスト |
| `max_turns` | `int` | 最大ターン数 |

**使用例**

```python
import mixseek_plus

# ツール設定を登録
mixseek_plus.configure_claudecode_tool_settings({
    "permission_mode": "bypassPermissions",
    "working_directory": "/workspace",
})

# パッチを適用（設定が反映される）
mixseek_plus.patch_core()
```

### get_claudecode_tool_settings

```python
def get_claudecode_tool_settings() -> ClaudeCodeToolSettings | None
```

現在登録されているClaudeCodeツール設定を取得します。

**戻り値**

- 設定が登録されている場合: `ClaudeCodeToolSettings`
- 設定が登録されていない場合: `None`

**使用例**

```python
import mixseek_plus

settings = mixseek_plus.get_claudecode_tool_settings()
if settings:
    print(settings.get("permission_mode"))
```

### clear_claudecode_tool_settings

```python
def clear_claudecode_tool_settings() -> None
```

登録されているClaudeCodeツール設定をクリアします。

クリア後はデフォルトのClaudeCode動作に戻ります。

**使用例**

```python
import mixseek_plus

# 設定をクリア
mixseek_plus.clear_claudecode_tool_settings()
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

### register_claudecode_agents

```python
def register_claudecode_agents() -> None
```

ClaudeCodeエージェントを `MemberAgentFactory` に登録します。
TOML設定で `claudecode_plain` タイプを使用する前に呼び出す必要があります。

この関数はべき等であり、複数回呼び出しても安全です。

**使用例**

```python
from mixseek_plus import register_claudecode_agents

register_claudecode_agents()

# これでTOML設定でclaudecode_plainが使用可能
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

### ClaudeCodePlainAgent

```python
class ClaudeCodePlainAgent(BaseClaudeCodeAgent)
```

Claude Code CLIの組み込みツールを使用するMemberエージェントです。
Bash、Read/Write/Edit、Glob/Grep、WebFetch/WebSearchなどの機能が統合されています。

APIキーは不要です。Claude Code CLIのセッション認証を使用します。

**コンストラクタ**

```python
def __init__(self, config: MemberAgentConfig) -> None
```

| 引数 | 型 | 説明 |
|------|-----|------|
| `config` | `MemberAgentConfig` | エージェント設定 |

**例外**

- `ValueError`: モデル作成に失敗した場合（Claude Code CLI未インストールなど）

**tool_settings.claudecode設定**

TOML設定の `[members.tool_settings.claudecode]` セクションで以下の設定が可能です：

| 設定 | 型 | 説明 |
|------|-----|------|
| `allowed_tools` | `list[str]` | 許可するツールのリスト |
| `disallowed_tools` | `list[str]` | 禁止するツールのリスト |
| `permission_mode` | `str` | パーミッションモード |
| `working_directory` | `str` | 作業ディレクトリ |
| `max_turns` | `int` | 最大ターン数 |

**使用例**

```toml
[[members]]
name = "code-analyst"
type = "claudecode_plain"
model = "claudecode:claude-sonnet-4-5"
system_instruction = "あなたはコード分析のスペシャリストです。"

[members.tool_settings.claudecode]
allowed_tools = ["Read", "Glob", "Grep"]
permission_mode = "bypassPermissions"
```

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

### ClaudeCodeNotPatchedError

```python
class ClaudeCodeNotPatchedError(Exception)
```

`patch_core()` を呼び出さずにLeader/EvaluatorでClaudeCodeモデルを使用しようとした場合に発生する例外です。

**コンストラクタ**

```python
def __init__(self, message: str | None = None) -> None
```

`message` を省略すると、解決方法を含むデフォルトメッセージが使用されます。

**使用例**

```python
from mixseek_plus import ClaudeCodeNotPatchedError

try:
    # ClaudeCodeモデルを使用
    pass
except ClaudeCodeNotPatchedError:
    import mixseek_plus
    mixseek_plus.patch_core()
```

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
