# Research: Playwright + MarkItDown統合Webフェッチャー

**Feature Branch**: `031-playwright-markdown-fetch`
**Created**: 2026-01-19
**Status**: Complete

## 調査項目

### 1. MarkItDown ライブラリ

**Decision**: Microsoft MarkItDown (`markitdown` パッケージ) を使用

**Rationale**:
- HTML含む多様な形式をMarkdownに変換可能
- LLM処理に最適化された出力
- 文書構造（見出し、リスト、テーブル）を保持
- Microsoft製でメンテナンスが安定
- Python 3.10+ 対応

**Alternatives Considered**:
- `markdownify`: 軽量だがHTML特化、構造保持が限定的
- `html-to-markdown`: 高性能Rust実装だが、外部ランタイム依存

**Key API**:
```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False)  # プラグイン無効で軽量
result = md.convert("page.html")  # またはファイルパス
print(result.text_content)  # Markdown文字列
```

**Note**: バージョン0.1.0+では `convert()` にバイナリファイルオブジェクトまたはパスを渡す

**Source**: [GitHub - microsoft/markitdown](https://github.com/microsoft/markitdown)

---

### 2. Playwright ブラウザライフサイクル管理

**Decision**: エージェント単位でPlaywrightインスタンスを管理（`__init__`で起動、`close()`で終了）

**Rationale**:
- spec.mdで「エージェント単位で保持」と明記
- ブラウザ再利用でパフォーマンス向上
- リクエスト毎の起動/終了オーバーヘッド回避
- BrowserContextで分離可能

**Implementation Pattern**:
```python
from playwright.async_api import async_playwright, Browser, Playwright

class PlaywrightMarkdownFetchAgent:
    _playwright: Playwright | None = None
    _browser: Browser | None = None

    async def _ensure_browser(self) -> Browser:
        """ブラウザを遅延初期化"""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.config.headless
            )
        return self._browser

    async def close(self) -> None:
        """リソースを解放"""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
```

**Cleanup Best Practice**:
1. BrowserContextを明示的にclose
2. Browserをclose
3. Playwrightをstop

**Source**: [Playwright Python - Browser API](https://playwright.dev/python/docs/api/class-browser)

---

### 3. 既存エージェントパターン（mixseek-plus）

**Decision**: `BaseGroqAgent` パターンに従い `BasePlaywrightAgent` を作成

**Rationale**:
- 一貫したアーキテクチャ
- DRY原則遵守
- MemberAgentFactory登録パターン再利用
- テスト容易性確保

**Implementation Reference**:
- `base_groq_agent.py`: 共通基底クラス実装
- `groq_agent.py`: プレーンエージェント実装
- `agents/__init__.py`: Factory登録関数

**Key Differences from Groq Agents**:
| 項目 | Groqエージェント | Playwrightエージェント |
|------|-----------------|----------------------|
| 外部依存 | pydantic-ai + Groq API | Playwright + MarkItDown |
| ライフサイクル | ステートレス | ブラウザ保持（ステートフル） |
| モデル | groq:* プレフィックス | 任意（model設定で指定） |
| ツール | なし / Web検索 | fetch_page |

---

### 4. オプション依存関係の管理

**Decision**: `[playwright]` オプショナル依存関係として追加

**Rationale**:
- Playwrightはサイズが大きい（ブラウザバイナリ含む）
- 全ユーザーが必要とするわけではない
- 明示的なインストールで意図を明確化

**pyproject.toml 追加**:
```toml
[project.optional-dependencies]
playwright = [
    "playwright>=1.57.0",
    "markitdown>=0.1.4",
]
```

**Installation**:
```bash
pip install mixseek-plus[playwright]
playwright install chromium
```

---

### 5. 任意モデル対応の設計

**Decision**: 新しい基底クラス `BaseDynamicModelAgent` を作成し、model設定で任意のプロバイダーを指定可能にする

**Rationale**:
- spec.md FR-006: 任意のモデルプロバイダー対応
- `groq:*`, `anthropic:*`, `openai:*` 等を統一的に扱う
- mixseek-plus の `create_model()` を活用

**Implementation**:
```python
class BaseDynamicModelAgent(BaseMemberAgent):
    """任意のモデルプロバイダーに対応する基底クラス"""

    def __init__(self, config: MemberAgentConfig) -> None:
        super().__init__(config)
        # create_model() は groq: と他プロバイダーを統一的に処理
        self._model = create_model(config.model)
```

---

### 6. リトライ機能の実装

**Decision**: 指数バックオフを独自実装（tenacity等の依存追加を避ける）

**Rationale**:
- シンプルな要件（リトライ回数と初期遅延のみ）
- 依存関係の最小化
- Playwright固有のエラーハンドリングとの統合

**Implementation Pattern**:
```python
async def _fetch_with_retry(self, url: str) -> str:
    """リトライ付きでページを取得"""
    last_error: Exception | None = None

    for attempt in range(self.config.retry_count + 1):
        try:
            return await self._fetch_page(url)
        except RetryableError as e:
            last_error = e
            if attempt < self.config.retry_count:
                delay = self.config.retry_delay_ms * (2 ** attempt) / 1000
                await asyncio.sleep(delay)

    raise FetchError(
        f"All {self.config.retry_count + 1} attempts failed: {last_error}"
    )
```

---

### 7. リソースブロック機能

**Decision**: Playwright の route.abort() を使用

**Rationale**:
- Playwrightのネイティブ機能
- パフォーマンス向上（不要なリソースをダウンロードしない）
- 柔軟な設定（リソースタイプ指定）

**Implementation**:
```python
async def _setup_resource_blocking(self, page: Page) -> None:
    """リソースブロックを設定"""
    if not self.config.block_resources:
        return

    async def block_handler(route: Route) -> None:
        if route.request.resource_type in self.config.block_resources:
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", block_handler)
```

**Supported Resource Types** (Playwright):
- `document`, `stylesheet`, `image`, `media`, `font`, `script`, `texttrack`, `xhr`, `fetch`, `eventsource`, `websocket`, `manifest`, `other`

---

### 8. Playwrightインストール確認

**Decision**: インポート時にPlaywrightの利用可能性をチェックし、明確なエラーメッセージを提供

**Rationale**:
- FR-007: オプション依存関係としてPlaywrightを提供
- Edge Case: Playwrightがインストールされていない場合のエラーハンドリング

**Implementation**:
```python
def _check_playwright_available() -> None:
    """Playwrightの利用可能性をチェック"""
    try:
        import playwright  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "playwright is not installed. Install it with:\n"
            "  pip install mixseek-plus[playwright]\n"
            "  playwright install chromium"
        ) from e
```

---

## 解決された NEEDS CLARIFICATION

| 項目 | 解決策 |
|------|--------|
| モデルプロバイダー | 任意のモデル対応（create_model()使用） |
| エージェント登録 | MemberAgentFactory.register_agent() |
| ツールモード | LLMがfetch_pageツールを呼び出す |
| ブラウザライフサイクル | エージェント単位で保持 |

---

## 参考リンク

- [MarkItDown - GitHub](https://github.com/microsoft/markitdown)
- [Playwright Python - Browser API](https://playwright.dev/python/docs/api/class-browser)
- [Playwright Python - BrowserContext](https://playwright.dev/python/docs/api/class-browsercontext)
- [Real Python - Python MarkItDown](https://realpython.com/python-markitdown/)
