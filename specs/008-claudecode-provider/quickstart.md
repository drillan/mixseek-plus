# Quickstart: ClaudeCodeプロバイダー

## 前提条件

1. **Claude Code CLIがインストール済み**

   **macOS / Linux / WSL:**
   ```bash
   curl -fsSL https://claude.ai/install.sh | bash
   ```

   **Windows PowerShell:**
   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```

   **Homebrew (macOS):**
   ```bash
   brew install --cask claude-code
   ```

   **インストール確認:**
   ```bash
   claude --version
   ```

2. **Claudeサブスクリプションまたはアカウント**
   - Claude Pro、Max、Teams、Enterprise サブスクリプション
   - または Claude Console アカウント

3. **mixseek-plusがインストール済み**
   ```bash
   pip install mixseek-plus
   ```

## 基本的な使い方

### Python APIでモデル作成

```python
import mixseek_plus

# ClaudeCodeモデルを作成
model = mixseek_plus.create_model("claudecode:claude-sonnet-4-5")

# 他のサポートモデル
model_haiku = mixseek_plus.create_model("claudecode:claude-haiku-4-5")
model_opus = mixseek_plus.create_model("claudecode:claude-opus-4-5")

# フルバージョン指定
model_versioned = mixseek_plus.create_model("claudecode:claude-sonnet-4-5-20250929")
```

### Member Agentとして使用

```python
import asyncio
from mixseek.models.member_agent import MemberAgentConfig
from mixseek_plus import ClaudeCodePlainAgent

# 設定を作成
config = MemberAgentConfig(
    name="my-claudecode-agent",
    type="custom",  # custom タイプで claudecode: プレフィックスを許可
    model="claudecode:claude-sonnet-4-5",
    system_instruction="You are a helpful assistant.",
)

# エージェントを作成
agent = ClaudeCodePlainAgent(config)

# タスクを実行
async def main():
    result = await agent.execute("What is 2 + 2?")
    print(result.content)

asyncio.run(main())
```

### TOML設定での使用

```toml
# claudecode-config.toml

[leader]
model = "claudecode:claude-sonnet-4-5"
system_instruction = "You are a team leader."

[[members]]
name = "claudecode-analyst"
type = "claudecode_plain"
model = "claudecode:claude-sonnet-4-5"
system_instruction = "You are a code analyst with access to file operations and web search."

# オプション: ツール設定のカスタマイズ
[members.tool_settings.claudecode]
allowed_tools = ["Read", "Glob", "Grep", "WebSearch", "WebFetch"]
permission_mode = "bypassPermissions"
max_turns = 10
```

### CLI経由での実行

```bash
# mixseek-plusをインストールすると、mixseekコマンドが自動的にClaudeCode対応

# チーム実行
mixseek exec --config claudecode-config.toml "Analyze the codebase structure"

# バージョン確認（mixseek-coreと互換）
mixseek --version
```

### Leader/Evaluatorでの使用

```python
import mixseek_plus

# パッチを適用（Leader/Evaluatorで claudecode: を使用する場合に必要）
mixseek_plus.patch_core()

# 以降、Leader/Evaluatorで claudecode: モデルが使用可能
from mixseek.agents.leader import LeaderConfig

config = LeaderConfig(
    model="claudecode:claude-sonnet-4-5",
    system_instruction="You are a team leader.",
)
```

## ツール設定のカスタマイズ

ClaudeCodePlainAgentは、Claude Code CLIの組み込みツールを使用します：

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

### ツール制限の例

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

## エラーハンドリング

```python
from mixseek_plus.errors import ModelCreationError

try:
    model = mixseek_plus.create_model("claudecode:claude-sonnet-4-5")
except ModelCreationError as e:
    print(f"モデル作成エラー: {e}")
    # Claude Code CLIがインストールされていない場合など
```

## トラブルシューティング

### "Claude Code CLIがインストールされていません"

```bash
# Claude Code CLIをインストール（macOS / Linux / WSL）
curl -fsSL https://claude.ai/install.sh | bash

# Homebrew (macOS)
brew install --cask claude-code

# 最新版に更新
claude update
```

### "セッションが無効です"

Claude Code CLIを起動して認証を完了してください：
```bash
claude
```
初回起動時に認証フローが開始されます。

### "mixseek_plus.patch_core() を呼び出してください"

Leader/Evaluatorで `claudecode:` モデルを使用する場合、最初にパッチを適用する必要があります：

```python
import mixseek_plus
mixseek_plus.patch_core()  # これを追加
```

CLI経由での使用時は自動的にパッチが適用されます。
