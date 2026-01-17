# mixseek-plus

mixseek-coreの拡張パッケージ。Groqモデルサポート、Playwrightフェッチ機能強化などの追加機能を提供。

## インストール

```bash
pip install mixseek-plus
```

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `GROQ_API_KEY` | 必須 | Groq APIキー |
| `TAVILY_API_KEY` | オプション | Web検索機能を使用する場合に必要 |

## クイックスタート

### Python API

```python
import mixseek_plus

# Groqモデルの作成
model = mixseek_plus.create_model("groq:llama-3.3-70b-versatile")

# Leader/Evaluatorでの使用（patch_core が必要）
mixseek_plus.patch_core()

# TOMLファイルでgroq_plain/groq_web_searchを使う場合
mixseek_plus.register_groq_agents()
```

### TOML設定

```toml
# team.toml

# Leaderの設定（patch_core()が必要）
[leader]
model = "groq:llama-3.3-70b-versatile"

# Memberエージェントの設定
[[members]]
name = "groq-assistant"
type = "groq_plain"
model = "groq:llama-3.3-70b-versatile"

[[members]]
name = "web-searcher"
type = "groq_web_search"
model = "groq:llama-3.3-70b-versatile"
```

### CLIの使用

```bash
# チーム実行
mixseek team "タスク" --config team.toml
```

## 主要機能

- mixseek-coreの全機能を継承
- Groqモデルサポート（`create_model()`）
- Groq Memberエージェント（`groq_plain`, `groq_web_search`）
- Leader/EvaluatorへのGroq統合（`patch_core()`）
- Playwrightによるweb_fetch強化

## ドキュメント

- [Getting Started](./docs/getting-started.md) - 導入ガイド
- [User Guide](./docs/user-guide.md) - 使用方法の詳細
- [API Reference](./docs/api-reference.md) - API仕様

## ライセンス

TBD
