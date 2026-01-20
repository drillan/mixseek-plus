# Quickstart: Playwright + MarkItDown統合Webフェッチャー

**Feature Branch**: `031-playwright-markdown-fetch`
**Created**: 2026-01-19

## インストール

### 1. パッケージインストール

```bash
# playwright オプションを含めてインストール
pip install mixseek-plus[playwright]
```

### 2. Chromiumブラウザインストール

```bash
# Playwrightのブラウザをインストール
playwright install chromium
```

## 基本的な使い方

### TOML設定ファイル

`config.toml`:

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
```

### Pythonコード

```python
import asyncio
from mixseek.config.toml_loader import load_config
from mixseek_plus import patch_core
from mixseek_plus.agents import register_playwright_agents

# 1. mixseek-coreにパッチを適用
patch_core()

# 2. Playwrightエージェントを登録
register_playwright_agents()

# 3. 設定をロード
config = load_config("config.toml")

# 4. エージェントを取得して実行
async def main():
    agent = config.get_member("web-fetcher")
    result = await agent.execute("https://docs.python.org/3/ の内容を要約してください")
    print(result.content)

    # 5. リソースを解放
    await agent.close()

asyncio.run(main())
```

## 設定オプション

### Playwright設定

| オプション | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `headless` | bool | `true` | ヘッドレスモードで実行 |
| `timeout_ms` | int | `30000` | タイムアウト（ミリ秒） |
| `wait_for_load_state` | string | `"load"` | 待機条件 |
| `retry_count` | int | `0` | リトライ回数 |
| `retry_delay_ms` | int | `1000` | リトライ遅延（ミリ秒） |
| `block_resources` | list | `null` | ブロックするリソース |

### wait_for_load_state オプション

| 値 | 説明 |
|---|------|
| `"load"` | `load`イベント発火時（デフォルト） |
| `"domcontentloaded"` | DOMロード完了時 |
| `"networkidle"` | ネットワークアクティビティ終了時 |

### block_resources オプション

ブロック可能なリソースタイプ:
- `"image"` - 画像
- `"font"` - フォント
- `"stylesheet"` - CSS
- `"script"` - JavaScript
- `"media"` - 動画/音声
- `"xhr"` / `"fetch"` - AJAX リクエスト

## ユースケース別設定例

### ボット対策サイトからの取得

```toml
[[members]]
name = "web-fetcher"
type = "playwright_markdown_fetch"
model = "anthropic:claude-sonnet-4-5"

[members.playwright]
headless = false  # headed モードでボット検知を回避
timeout_ms = 60000
wait_for_load_state = "networkidle"
```

### 高速な取得（画像/フォント除外）

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

### リトライ付き取得

```toml
[[members]]
name = "resilient-fetcher"
type = "playwright_markdown_fetch"
model = "groq:llama-3.3-70b-versatile"

[members.playwright]
retry_count = 3
retry_delay_ms = 2000  # 2秒 → 4秒 → 8秒（指数バックオフ）
```

## トラブルシューティング

### "playwright is not installed" エラー

```bash
# パッケージを再インストール
pip install mixseek-plus[playwright]
```

### ブラウザが見つからないエラー

```bash
# Chromiumをインストール
playwright install chromium
```

### タイムアウトエラー

```toml
[members.playwright]
timeout_ms = 60000  # タイムアウトを延長
wait_for_load_state = "domcontentloaded"  # より早い待機条件
```

### ボット検知でブロックされる

```toml
[members.playwright]
headless = false  # headed モードに切り替え
```

## 注意事項

- `headless = false` を使用する場合、GUIが利用可能な環境で実行する必要があります
- CI/CDなど非GUI環境では `headless = true` を使用してください
- 大量のページを取得する場合は、`retry_delay_ms` を適切に設定してサーバーへの負荷を軽減してください
