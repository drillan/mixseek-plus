# User Guide

mixseek-plusの詳細な使用方法を説明します。

## Model Factory

`create_model()` 関数を使用して、Groq、ClaudeCode、またはmixseek-core対応モデルのインスタンスを作成します。

### 基本的な使用方法

```python
from mixseek_plus import create_model

# Groqモデル
model = create_model("groq:llama-3.3-70b-versatile")
model = create_model("groq:qwen/qwen3-32b")

# ClaudeCodeモデル（APIキー不要）
model = create_model("claudecode:claude-sonnet-4-5")
model = create_model("claudecode:claude-haiku-4-5")
model = create_model("claudecode:claude-opus-4-5")

# mixseek-coreモデル（OpenAI、Anthropicなど）
model = create_model("openai:gpt-4o")
model = create_model("anthropic:claude-sonnet-4-5-20250929")
```

### モデルID形式

モデルIDは `provider:model-name` の形式で指定します。

| プロバイダー | 例 | 備考 |
|--------------|-----|------|
| `claudecode` | `claudecode:claude-sonnet-4-5` | Claude Code CLI経由（APIキー不要） |
| `groq` | `groq:llama-3.3-70b-versatile` | Groq API |
| `openai` | `openai:gpt-4o` | mixseek-core委譲 |
| `anthropic` | `anthropic:claude-sonnet-4-5-20250929` | mixseek-core委譲 |
| `google-gla` | `google-gla:gemini-2.0-flash` | mixseek-core委譲 |
| `google-vertex` | `google-vertex:gemini-2.0-flash` | mixseek-core委譲 |
| `grok` | `grok:grok-2` | mixseek-core委譲 |
| `grok-responses` | `grok-responses:grok-2` | mixseek-core委譲 |

## Memberエージェント

mixseek-plusは、Groq Memberエージェント（2種類）とClaudeCode Memberエージェント（1種類）を提供します。

### エージェントの登録

TOML設定でエージェントを使用する前に、登録が必要です。

```python
from mixseek_plus import register_groq_agents, register_claudecode_agents

# Groqエージェントを登録
register_groq_agents()

# ClaudeCodeエージェントを登録
register_claudecode_agents()
```

### Groq Memberエージェント

#### GroqPlainAgent

シンプルなテキスト応答エージェントです。

```toml
[[members]]
name = "groq-assistant"
type = "groq_plain"
model = "groq:llama-3.3-70b-versatile"
system_instruction = "あなたは親切なアシスタントです。"
```

#### GroqWebSearchAgent

Web検索機能を持つエージェントです。`TAVILY_API_KEY` が必要です。

```toml
[[members]]
name = "web-researcher"
type = "groq_web_search"
model = "groq:llama-3.3-70b-versatile"
system_instruction = "あなたは情報収集のスペシャリストです。"
```

### ClaudeCode Memberエージェント

#### ClaudeCodePlainAgent

Claude Code CLIの組み込みツールを活用する多機能エージェントです。Bash実行、ファイル操作、Web検索などの機能が統合されており、単一のエージェントで複数の機能を実行できます。

```toml
[[members]]
name = "claudecode-assistant"
type = "claudecode_plain"
model = "claudecode:claude-sonnet-4-5"
system_instruction = "あなたはコード分析とファイル操作が得意なアシスタントです。"
```

**利用可能な組み込みツール:**

| ツール | 機能 |
|--------|------|
| `Bash` | コマンド・コード実行 |
| `Read` | ファイル読み取り |
| `Write` | ファイル書き込み |
| `Edit` | ファイル編集 |
| `Glob` | ファイル検索（パターン） |
| `Grep` | ファイル検索（内容） |
| `WebFetch` | Webページ取得 |
| `WebSearch` | Web検索 |

#### tool_settings設定オプション

ClaudeCodePlainAgentでは、`tool_settings.claudecode`セクションでツールの動作をカスタマイズできます。

```toml
[[members]]
name = "claudecode-readonly"
type = "claudecode_plain"
model = "claudecode:claude-sonnet-4-5"
system_instruction = "ファイルの読み取りと検索のみを行うエージェント"

[members.tool_settings.claudecode]
allowed_tools = ["Read", "Glob", "Grep"]
```

**tool_settings.claudecodeオプション:**

| オプション | 型 | 説明 |
|------------|-----|------|
| `allowed_tools` | `list[str]` | 許可するツールのリスト |
| `disallowed_tools` | `list[str]` | 禁止するツールのリスト |
| `permission_mode` | `str` | パーミッションモード（`"bypassPermissions"` で確認スキップ） |
| `working_directory` | `str` | 作業ディレクトリ |
| `max_turns` | `int` | 最大ターン数 |

**設定例:**

```toml
# 読み取り専用設定
[members.tool_settings.claudecode]
allowed_tools = ["Read", "Glob", "Grep"]

# 書き込み禁止設定
[members.tool_settings.claudecode]
disallowed_tools = ["Write", "Edit", "Bash"]

# 全自動実行（パーミッション確認スキップ）
[members.tool_settings.claudecode]
permission_mode = "bypassPermissions"
```

### 共通の設定オプション

すべてのMemberエージェントで使用可能な設定オプションです。

```toml
[[members]]
name = "custom-agent"
type = "groq_plain"  # または claudecode_plain
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

Leader/EvaluatorエージェントでGroqまたはClaudeCodeモデルを使用するには、`patch_core()` を呼び出す必要があります。

### patch_coreの使用

```python
import mixseek_plus

# アプリケーション起動時に一度だけ呼び出す
mixseek_plus.patch_core()
```

### TOML設定例（Groq）

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

### TOML設定例（ClaudeCode）

```toml
[leader]
model = "claudecode:claude-sonnet-4-5"
system_instruction = "あなたはチームリーダーです。"
max_rounds = 5

[evaluator]
model = "claudecode:claude-sonnet-4-5"

[[members]]
name = "code-analyst"
type = "claudecode_plain"
model = "claudecode:claude-sonnet-4-5"
system_instruction = "あなたはコード分析のスペシャリストです。"

# オプション: ツール設定のカスタマイズ
[members.tool_settings.claudecode]
allowed_tools = ["Read", "Glob", "Grep", "WebSearch", "WebFetch"]
permission_mode = "bypassPermissions"
```

### 完全なセットアップ例

```python
import mixseek_plus

# 1. Core patchを適用（Groq/ClaudeCodeサポートを有効化）
mixseek_plus.patch_core()

# 2. エージェントを登録
mixseek_plus.register_groq_agents()        # groq_plain, groq_web_search
mixseek_plus.register_claudecode_agents()  # claudecode_plain

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

### ClaudeCodeNotPatchedError

Leader/EvaluatorでClaudeCodeモデルを使用する前に `patch_core()` を呼び出してください。

```python
import mixseek_plus
mixseek_plus.patch_core()
```

CLI経由での使用時は自動的にパッチが適用されるため、この操作は不要です。

### Claude Code CLIが見つからない

ClaudeCodeモデルを使用するには、Claude Code CLIがインストールされている必要があります。

```bash
# macOS / Linux / WSL
curl -fsSL https://claude.ai/install.sh | bash

# Homebrew (macOS)
brew install --cask claude-code

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex

# インストール確認
claude --version
```

### セッションが無効です

Claude Code CLIのセッションが無効になっている場合は、再認証が必要です。

```bash
claude
```

初回起動時または再認証時に、ブラウザで認証フローが開始されます。

### TAVILY_API_KEY...

GroqでWeb検索エージェントを使用する場合は、Tavily APIキーが必要です。

```bash
export TAVILY_API_KEY="your-tavily-api-key"
```

ClaudeCodeはWebSearch/WebFetchツールが組み込まれているため、Tavily APIキーは不要です。
