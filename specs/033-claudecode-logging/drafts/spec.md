# Issue #33: ClaudeCodeModel固有のロギング・オブザーバビリティ

## 概要

ClaudeCodeModelはClaude Code CLIをラップしたpydantic-aiモデル実装であり、標準のpydantic-aiモデルとは異なる動作をする。MCP経由のツール呼び出しがpydantic-aiのインストルメンテーションの外側にあるため、ロギングとオブザーバビリティに問題が発生している。

### 根本原因

```
標準モデル:     Python → pydantic-ai → Provider API → ログ記録 ✅
ClaudeCodeModel: Python → pydantic-ai → Claude Code CLI → MCP → Anthropic API
                              ↑
                        ブラックボックス（ログ記録されない）
```

## スコープ

- **短期**: エージェント内での明示的なログ出力（`--verbose`時）
- **中期**: Logfireインストルメンテーション、MCP呼び出しログ記録、メッセージ履歴統合

## 要件

### ログレベル
- **基本情報のみ**: ツール名、URL/引数の概要、成功/失敗、実行時間

### 保存先
- **ファイルログ優先**: `$WORKSPACE/logs/`に別ファイルで記録

### 環境変数

| 変数名 | 用途 | デフォルト |
|-------|------|-----------|
| `MIXSEEK_VERBOSE` | 詳細ツールログ出力 | `false` |
| `MIXSEEK_LOGFIRE` | Logfire統合有効化 | `false` |

## ユーザーストーリー

### US-1: 開発者としてMCPツール呼び出しをログで確認したい

**Given**: ClaudeCodeModelを使用するエージェントが実行されている
**When**: MCPツール呼び出しが発生する
**Then**: ツール名、引数概要、成功/失敗、実行時間がログに記録される

### US-2: 開発者としてverboseモードで詳細情報を確認したい

**Given**: `MIXSEEK_VERBOSE=1`が設定されている
**When**: MCPツール呼び出しが発生する
**Then**: 詳細なログがコンソールとファイルに出力される

### US-3: 開発者としてLogfireでオブザーバビリティを確認したい

**Given**: `MIXSEEK_LOGFIRE=1`が設定されている
**When**: エージェントが実行される
**Then**: pydantic-aiの自動インストルメンテーションが有効になる

## 既に対処済みの項目（#031）

- MCPツール名をシステムプロンプトに明示
- `_register_toolsets_if_claudecode()` で `allowed_tools` 自動設定
- `_wrap_tool_for_mcp()` でコンテキスト注入
- `FixedTokenClaudeCodeModel` でトークン計算補正
