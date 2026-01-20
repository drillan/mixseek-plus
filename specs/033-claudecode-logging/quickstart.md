# Quickstart: ClaudeCodeModel ロギング・オブザーバビリティ

## 概要

本ガイドでは、ClaudeCodeModel を使用するエージェントのMCPツール呼び出しをログで確認する方法を説明します。

---

## 基本的な使い方

### 1. Verbose モードでの実行

MCPツール呼び出しの詳細ログを確認するには、`--verbose` オプションを使用します。

```bash
# CLI から実行
mixseek-plus exec "ウェブページを取得してタイトルを抽出" --config team.toml --verbose

# または環境変数で制御
MIXSEEK_VERBOSE=1 mixseek-plus exec "ウェブページを取得してタイトルを抽出" --config team.toml
```

**出力例** (コンソール):

```
[MCP Tool Start] mcp__pydantic_tools__fetch_url: url=https://example.com
[MCP Tool Done] mcp__pydantic_tools__fetch_url: success in 1250ms
```

### 2. ログファイルの確認

ログは `$WORKSPACE/logs/member-agent-YYYY-MM-DD.log` に JSON 形式で記録されます。

```bash
# 最新のログを確認
tail -f $WORKSPACE/logs/member-agent-$(date +%Y-%m-%d).log

# ツール呼び出しのみをフィルタ
cat $WORKSPACE/logs/member-agent-$(date +%Y-%m-%d).log | jq 'select(.event == "tool_invocation")'
```

**ログ出力例** (JSON):

```json
{
  "event": "tool_invocation",
  "execution_id": "exec_abc123",
  "tool_name": "mcp__pydantic_tools__fetch_url",
  "parameters": {"url": "https://example.com", "prompt": "Extract title"},
  "execution_time_ms": 1250,
  "status": "success",
  "timestamp": "2026-01-20T12:34:57.100Z"
}
```

---

## Logfire 統合（オプショナル）

### 1. Logfire のインストール

```bash
# Logfire サポート付きでインストール
uv add mixseek-plus[logfire]

# または pip で
pip install mixseek-plus[logfire]
```

### 2. Logfire の設定

```bash
# Logfire CLI で認証
logfire auth

# プロジェクト設定
logfire projects use your-project
```

### 3. Logfire モードでの実行

```bash
# CLI から実行
mixseek-plus exec "データを分析" --config team.toml --logfire

# または環境変数で制御
MIXSEEK_LOGFIRE=1 mixseek-plus exec "データを分析" --config team.toml
```

### 4. Logfire ダッシュボードで確認

- [Logfire Dashboard](https://logfire.pydantic.dev/) にアクセス
- pydantic-ai の自動インストルメンテーションによるトレースを確認

---

## トラブルシューティング

### ログが出力されない

1. `--verbose` オプションまたは `MIXSEEK_VERBOSE=1` が設定されているか確認
2. ワークスペースディレクトリ（`$WORKSPACE`）への書き込み権限を確認
3. ログレベルが適切に設定されているか確認（`--log-level debug`）

### Logfire が有効にならない

1. `logfire` パッケージがインストールされているか確認
   ```bash
   python -c "import logfire; print(logfire.__version__)"
   ```
2. Logfire の認証が完了しているか確認
   ```bash
   logfire whoami
   ```
3. 警告メッセージを確認（インストールされていない場合は警告が出力される）

### 機密情報がログに含まれる

- 通常、`api_key`, `token`, `secret` などのキーを含むパラメータは自動的にマスクされます
- カスタムフィールドをマスクする必要がある場合は、Issue を作成してください

---

## 設定オプション一覧

| オプション | 環境変数 | デフォルト | 説明 |
|-----------|---------|----------|------|
| `--verbose` / `-v` | `MIXSEEK_VERBOSE` | `false` | 詳細ログ出力を有効化 |
| `--logfire` | `MIXSEEK_LOGFIRE` | `false` | Logfire統合を有効化 |
| `--logfire-metadata` | - | `false` | Logfire（メタデータのみ） |
| `--logfire-http` | - | `false` | Logfire（HTTP キャプチャ付き） |
| `--log-level` | - | `INFO` | ログレベル（DEBUG, INFO, WARNING, ERROR） |

---

## ユースケース

### デバッグ時のツール実行追跡

```bash
# 詳細ログを有効にして実行
mixseek-plus exec "ウェブ検索してレポート作成" --config team.toml --verbose --log-level debug

# ログファイルでツール呼び出しを追跡
grep "tool_invocation" $WORKSPACE/logs/member-agent-*.log | jq .
```

### パフォーマンス分析

```bash
# 実行時間が長いツール呼び出しを特定
cat $WORKSPACE/logs/member-agent-*.log | \
  jq 'select(.event == "tool_invocation" and .execution_time_ms > 1000)'
```

### エラー調査

```bash
# 失敗したツール呼び出しを抽出
cat $WORKSPACE/logs/member-agent-*.log | \
  jq 'select(.event == "tool_invocation" and .status == "error")'
```

---

## 関連ドキュメント

- [spec.md](./spec.md) - 機能仕様
- [plan.md](./plan.md) - 実装計画
- [data-model.md](./data-model.md) - データモデル定義
- [mixseek-core ロギングガイド](https://github.com/mixseek/mixseek-core#logging) - 基盤ロギング機能
