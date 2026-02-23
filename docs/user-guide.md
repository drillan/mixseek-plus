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

### Groqで使用可能なモデル

| モデルID | 種類 | 備考 |
|----------|------|------|
| `groq:llama-3.3-70b-versatile` | Production | 推奨 |
| `groq:llama-3.1-8b-instant` | Production | 高速・低レイテンシ |
| `groq:meta-llama/llama-4-scout-17b-16e-instruct` | Preview | |
| `groq:qwen/qwen3-32b` | Preview | |

> **Note**: モデルリストは変更される可能性があります。最新情報は[Groq公式ドキュメント](https://console.groq.com/docs/models)を参照してください。
>
> *最終更新: 2026年1月*

## Memberエージェント

mixseek-plusは、以下のMemberエージェントを提供します:
- Groq: `groq_plain`、`groq_web_search`
- Tavily検索: `tavily_search`（Groq版）、`claudecode_tavily_search`（ClaudeCode版）
- ClaudeCode: `claudecode_plain`
- Playwright: `playwright_markdown_fetch`（Web Fetcher）

### エージェントの登録

TOML設定でエージェントを使用する前に、登録が必要です。

```python
from mixseek_plus import (
    register_groq_agents,
    register_claudecode_agents,
    register_playwright_agents,
    register_tavily_agents,
)

# Groqエージェントを登録
register_groq_agents()

# ClaudeCodeエージェントを登録
register_claudecode_agents()

# Playwrightエージェントを登録（要: pip install mixseek-plus[playwright]）
register_playwright_agents()

# Tavilyエージェントを登録
register_tavily_agents()
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

### Tavily検索エージェント

Tavily APIを使用したWeb検索、コンテンツ抽出、RAGコンテキスト生成が可能なエージェントです。
Groq版とClaudeCode版の2種類があります。

> **Note**: `TAVILY_API_KEY` 環境変数が必要です。

#### GroqTavilySearchAgent

Groqの高速推論とTavily検索機能を組み合わせたエージェントです。

```toml
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
temperature = 0.3
max_tokens = 4000
```

#### ClaudeCodeTavilySearchAgent

ClaudeCodeの強力な推論能力とTavily検索機能を組み合わせたエージェントです。

```toml
[[members]]
name = "claudecode-tavily-researcher"
type = "claudecode_tavily_search"
model = "claudecode:claude-sonnet-4-5"
system_prompt = "ClaudeCodeとTavily検索を組み合わせたリサーチャーです。"
```

#### Tavilyツール詳細

**tavily_search - Web検索**

| パラメータ | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `query` | `str` | 必須 | 検索クエリ |
| `search_depth` | `str` | `"basic"` | 検索詳細度 (`basic` または `advanced`) |
| `max_results` | `int` | `5` | 結果数 (1-20) |

**tavily_extract - コンテンツ抽出**

| パラメータ | 型 | 説明 |
|-----------|---|------|
| `urls` | `list[str]` | 抽出対象URL群（最大20件） |

**tavily_context - RAGコンテキスト**

| パラメータ | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `query` | `str` | 必須 | 検索クエリ |
| `max_tokens` | `int` | `None` | 最大トークン数 |

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
| `preset` | `str` | プリセット名（`configs/presets/claudecode.toml`から読み込み） |
| `allowed_tools` | `list[str]` | 許可するツールのリスト |
| `disallowed_tools` | `list[str]` | 禁止するツールのリスト |
| `permission_mode` | `str` | パーミッションモード（デフォルト: `"bypassPermissions"`、確認スキップ） |
| `working_directory` | `str` | 作業ディレクトリ |
| `max_turns` | `int` | 最大ターン数 |
| `timeout_seconds` | `int` | CLIセッションのタイムアウト秒数（デフォルト: 3600） |

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

#### プリセットによる設定

よく使う設定をプリセットとして定義し、再利用することができます。プリセットは `configs/presets/claudecode.toml` に定義します。

**プリセットファイルの作成:**

```toml
# configs/presets/claudecode.toml

[delegate_only]
# 委譲専用：直接ツールアクセスを禁止
permission_mode = "bypassPermissions"
disallowed_tools = ["Bash", "Write", "Edit", "Read", "Glob", "Grep", "WebFetch", "WebSearch", "NotebookEdit", "Task"]

[full_access]
# フルアクセス：全ツール利用可能
permission_mode = "bypassPermissions"

[read_only]
# 読み取り専用：書き込み・編集を禁止
permission_mode = "bypassPermissions"
disallowed_tools = ["Write", "Edit", "NotebookEdit"]
```

**プリセットの使用:**

```toml
[[members]]
name = "delegator"
type = "claudecode_plain"
model = "claudecode:claude-sonnet-4-5"
system_instruction = "タスクを適切なメンバーに委譲します。"

[members.tool_settings.claudecode]
preset = "delegate_only"
```

**プリセット + ローカル設定のマージ:**

プリセットの設定をベースに、ローカル設定で上書きすることも可能です。

```toml
[members.tool_settings.claudecode]
preset = "read_only"
max_turns = 50  # プリセットの設定 + 追加設定
```

この場合、`read_only`プリセットの設定に加えて、`max_turns = 50`が追加されます。ローカル設定はプリセットの値を上書きします。

**Memberエージェントでのプリセット解決:**

Memberエージェント（`claudecode_plain`など）でプリセットを使用する場合、`MIXSEEK_WORKSPACE` 環境変数を設定する必要があります。この環境変数はプリセットファイル（`configs/presets/claudecode.toml`）の検索ディレクトリを指定します。

```bash
export MIXSEEK_WORKSPACE="/path/to/your/workspace"
```

**重要:** `MIXSEEK_WORKSPACE` が設定されていない場合、プリセット解決はスキップされ、`disallowed_tools` などのセキュリティ設定が適用されない可能性があります。

Leader/Evaluatorエージェントでは、TOML設定ファイルのパスからワークスペースが自動的に推定されるため、この環境変数は不要です。

### Playwright Memberエージェント

Playwright Web Fetcher機能を使用するには、追加のインストールが必要です:

```bash
pip install mixseek-plus[playwright]
playwright install chromium
```

#### PlaywrightMarkdownFetchAgent

Playwrightを使用してWebページを取得し、Markdown形式に変換するエージェントです。ボット対策サイトからもコンテンツを取得できます。

```toml
[[members]]
name = "web-fetcher"
type = "playwright_markdown_fetch"
model = "groq:llama-3.3-70b-versatile"
system_prompt = """
あなたはWebページを取得してユーザーの質問に答えるアシスタントです。
fetch_pageツールを使用してWebページの内容を取得してください。
"""

[members.playwright]
headless = true
timeout_ms = 30000
wait_for_load_state = "load"
```

**特徴:**

- **Headed/Headless切り替え**: ボット検知を回避するためのheadedモードサポート
- **柔軟な待機条件**: `load`、`domcontentloaded`、`networkidle` から選択
- **リトライ機能**: 指数バックオフによる自動リトライ
- **リソースブロック**: 画像やフォントをブロックして高速化
- **HTML→Markdown変換**: MarkItDownによる高品質な変換

#### Playwright設定オプション

`[members.playwright]` セクションで以下の設定が可能です:

| オプション | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `headless` | `bool` | `true` | ヘッドレスモードで実行 |
| `timeout_ms` | `int` | `30000` | タイムアウト（ミリ秒） |
| `wait_for_load_state` | `string` | `"load"` | 待機条件（`load`/`domcontentloaded`/`networkidle`） |
| `retry_count` | `int` | `0` | リトライ回数（0=リトライなし） |
| `retry_delay_ms` | `int` | `1000` | 初回リトライ遅延（ミリ秒、指数バックオフ適用） |
| `block_resources` | `list[str]` | `null` | ブロックするリソースタイプ |

**block_resourcesで指定可能な値:**

- `"image"` - 画像
- `"font"` - フォント
- `"stylesheet"` - CSS
- `"script"` - JavaScript
- `"media"` - 動画/音声
- `"xhr"` / `"fetch"` - AJAX リクエスト

#### ユースケース別設定例

**ボット対策サイトからの取得:**

```toml
[[members]]
name = "bot-resistant-fetcher"
type = "playwright_markdown_fetch"
model = "anthropic:claude-sonnet-4-5"

[members.playwright]
headless = false  # headed モードでボット検知を回避
timeout_ms = 60000
wait_for_load_state = "networkidle"
```

**ClaudeCodeモデルを使用する場合:**

`claudecode:` プロバイダーを使用する場合は、`type = "custom"` と `plugin` セクションを使用します。

```toml
[[members]]
name = "claudecode-web-fetcher"
type = "custom"
model = "claudecode:claude-haiku-4-5"
system_prompt = "Webページを取得して分析するアシスタントです。"

[members.plugin]
agent_module = "mixseek_plus.agents.playwright_markdown_fetch_agent"
agent_class = "PlaywrightMarkdownFetchAgent"

[members.playwright]
headless = true
timeout_ms = 30000
wait_for_load_state = "networkidle"
```

> **Note:** `type = "playwright_markdown_fetch"` は mixseek-core がサポートするモデルプレフィックス（`groq:`, `anthropic:`, `openai:` 等）でのみ使用可能です。`claudecode:` を使用する場合は上記のように `type = "custom"` を指定してください。

**高速な取得（画像/フォント除外）:**

```toml
[[members]]
name = "fast-fetcher"
type = "playwright_markdown_fetch"
model = "openai:gpt-4o"

[members.playwright]
headless = true
timeout_ms = 15000
block_resources = ["image", "font", "media", "stylesheet"]
```

**リトライ付き取得:**

```toml
[[members]]
name = "resilient-fetcher"
type = "playwright_markdown_fetch"
model = "groq:llama-3.3-70b-versatile"

[members.playwright]
retry_count = 3
retry_delay_ms = 2000  # 2秒 → 4秒 → 8秒（指数バックオフ）
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

### Leader/Evaluator/JudgmentでのClaudeCode tool_settings設定

Leader/Evaluator/JudgmentエージェントでClaudeCodeを使用する際に、`permission_mode`などのツール設定を適用するには、`configure_claudecode_tool_settings()`を使用します。

この設定はLeader/Evaluator/Judgmentにのみ適用され、Memberエージェントには影響しません。Memberエージェントは自身のTOML設定（`[agent.tool_settings.claudecode]`）で個別に制御します。

```python
import mixseek_plus

# 1. ClaudeCode tool_settingsを設定（patch_coreの前後どちらでも可）
mixseek_plus.configure_claudecode_tool_settings({
    "permission_mode": "bypassPermissions",  # パーミッション確認をスキップ
    "working_directory": "/workspace",        # 作業ディレクトリ
})

# 2. パッチを適用
mixseek_plus.patch_core()

# これでLeader/Evaluator/JudgmentがClaudeCodeの
# Bash、Write等のツールを制限なく使用できる
# Memberエージェントは影響を受けない
```

**configure_claudecode_tool_settingsオプション:**

| オプション | 型 | 説明 |
|------------|-----|------|
| `preset` | `str` | プリセット名（`configs/presets/claudecode.toml`から読み込み） |
| `permission_mode` | `str` | パーミッションモード（デフォルト: `"bypassPermissions"`、確認スキップ） |
| `working_directory` | `str` | 作業ディレクトリ |
| `allowed_tools` | `list[str]` | 許可するツールのリスト |
| `disallowed_tools` | `list[str]` | 禁止するツールのリスト |
| `max_turns` | `int` | 最大ターン数 |

**プリセットの使用:**

TOML設定でLeader/Evaluatorにプリセットを適用することもできます。

```toml
[leader]
model = "claudecode:claude-sonnet-4-5"

[leader.tool_settings.claudecode]
preset = "full_access"
```

**設定のクリア:**

```python
# 設定をクリアして、デフォルト動作に戻す
mixseek_plus.clear_claudecode_tool_settings()
```

**現在の設定を取得:**

```python
# 現在の設定を確認
settings = mixseek_plus.get_claudecode_tool_settings()
print(settings)  # {"permission_mode": "bypassPermissions", ...}
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
mixseek-plus team "タスク" --config team.toml
# または短縮形
mskp team "タスク" --config team.toml

# ヘルプ表示
mixseek-plus --help
mskp --help
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

### TavilyAPIError

Tavily API呼び出しでエラーが発生した場合のトラブルシューティング。

#### 認証エラー (AUTH_ERROR)

Tavily APIキーが無効または未設定です。

```bash
export TAVILY_API_KEY="tvly-xxxxxxxxxxxx"
```

#### レート制限エラー (RATE_LIMIT_ERROR)

API呼び出しのレート制限に達しました。エージェントは自動的にリトライ（最大3回、指数バックオフ）を行います。

#### サーバーエラー (SERVER_ERROR, SERVICE_UNAVAILABLE)

Tavily APIサーバーに問題が発生しています。時間をおいて再試行してください。

### プリセットが適用されない

Memberエージェントでプリセットを使用する際に警告ログが出て設定が適用されない場合は、`MIXSEEK_WORKSPACE` 環境変数が設定されていることを確認してください。

```bash
export MIXSEEK_WORKSPACE="/path/to/your/workspace"
```

この環境変数はプリセットファイル（`configs/presets/claudecode.toml`）の検索先ディレクトリを指定します。設定されていない場合、プリセット解決がスキップされ、`disallowed_tools` などのセキュリティ設定が適用されません。

Leader/Evaluatorエージェントでは、TOML設定ファイルのパスから自動的に推定されるため、この環境変数は通常不要です。

### PlaywrightNotInstalledError

Playwrightエージェントを使用しようとしたが、Playwrightがインストールされていません。

```bash
# Playwrightオプションを含めてインストール
pip install mixseek-plus[playwright]
playwright install chromium
```

### ブラウザが見つからないエラー

Playwrightのブラウザがインストールされていません。

```bash
playwright install chromium
```

### Playwrightタイムアウトエラー

ページの読み込みに時間がかかりすぎています。

```toml
[members.playwright]
timeout_ms = 60000  # タイムアウトを延長
wait_for_load_state = "domcontentloaded"  # より早い待機条件
```

### ボット検知でブロックされる

一部のサイトはheadlessモードをブロックします。headedモードに切り替えてください。

```toml
[members.playwright]
headless = false  # headed モードに切り替え
```

> **注意:** `headless = false` を使用する場合、GUIが利用可能な環境で実行する必要があります。CI/CDなど非GUI環境では使用できません。

### PlaywrightでValidationError（Unsupported model）

`type = "playwright_markdown_fetch"` で `claudecode:` モデルを使用すると、以下のエラーが発生します：

```
ValidationError: 1 validation error for MemberAgentConfig
model
  Value error, Unsupported model 'claudecode:claude-haiku-4-5'...
```

これは、mixseek-core の `MemberAgentConfig` が `claudecode:` プレフィックスをネイティブサポートしていないためです。

**解決策:** `type = "custom"` と `plugin` セクションを使用してエージェントを読み込みます。

```toml
[[members]]
name = "web-fetcher"
type = "custom"  # playwright_markdown_fetch ではなく custom を使用
model = "claudecode:claude-haiku-4-5"

# plugin セクションでエージェントクラスを明示的に指定
[members.plugin]
agent_module = "mixseek_plus.agents.playwright_markdown_fetch_agent"
agent_class = "PlaywrightMarkdownFetchAgent"

[members.playwright]
headless = true
timeout_ms = 30000
```

この方法は、mixseek-plus が提供するすべてのカスタムエージェントで使用可能です。`type = "custom"` を使用することで、任意のモデルプレフィックスが許可されます。

**利用可能なエージェントモジュール:**

| エージェント | agent_module | agent_class |
|-------------|--------------|-------------|
| Playwright Web Fetcher | `mixseek_plus.agents.playwright_markdown_fetch_agent` | `PlaywrightMarkdownFetchAgent` |
| Groq Plain | `mixseek_plus.agents.groq_agent` | `GroqPlainAgent` |
| Groq Web Search | `mixseek_plus.agents.groq_web_search_agent` | `GroqWebSearchAgent` |
| ClaudeCode Plain | `mixseek_plus.agents.claudecode_agent` | `ClaudeCodePlainAgent` |
