# Feature Specification: ClaudeCodeModel固有のロギング・オブザーバビリティ

**Feature Branch**: `033-claudecode-logging`
**Created**: 2026-01-20
**Status**: Draft
**Parent Spec**: [008-claudecode-provider](../008-claudecode-provider/spec.md) - ClaudeCodeプロバイダーの基盤仕様
**Input**: User description: "ClaudeCodeModelはClaude Code CLIをラップしたpydantic-aiモデル実装であり、MCP経由のツール呼び出しがpydantic-aiのインストルメンテーションの外側にあるため、ロギングとオブザーバビリティに問題が発生している。この課題を解決する。"

## Clarifications

### Session 2026-01-20

- Q: verboseモードの制御方法は環境変数か、CLIオプションか？ → A: `mixseek-plus exec`コマンドの`--verbose`オプションで制御。オプション指定時に内部で`MIXSEEK_VERBOSE=1`相当の動作となる。
- Q: Logfire統合の制御方法は環境変数か、CLIオプションか？ → A: `mixseek-plus exec`コマンドの`--logfire`オプションで制御。オプション指定時に内部で`MIXSEEK_LOGFIRE=1`相当の動作となる。
- Q: ログ形式は既存のロギング機構と統一するか？ → A: はい。既存の`MemberAgentLogger.log_tool_invocation()`を使用してログ形式を統一する。これにより他モデル（Gemini、OpenAI等）と同一のJSON形式でログ出力され、機密情報マスキングも自動適用される。
- Q: 親仕様は何か？ → A: `specs/008-claudecode-provider/spec.md`が親仕様。本仕様はClaudeCodeプロバイダー（Issue #8）で実装されたClaudeCodeModelに対するロギング・オブザーバビリティ拡張である。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - MCPツール呼び出しのログ確認 (Priority: P1)

開発者として、ClaudeCodeModelを使用するエージェントがMCPツールを呼び出した際に、何が実行されたかをログで確認したい。現在はMCP経由のツール呼び出しがブラックボックスとなっており、デバッグや問題調査が困難である。

**Why this priority**: MCPツール呼び出しの可視化は本機能の核心であり、これがなければオブザーバビリティの改善は達成できない。最もユーザー価値が高く、他の機能の基盤となる。

**Independent Test**: 単体でテスト可能。ClaudeCodeModelを使用してMCPツールを呼び出し、ログファイルに適切な情報が記録されることを確認する。

**Acceptance Scenarios**:

1. **Given** ClaudeCodeModelを使用するエージェントが実行されている, **When** MCPツール呼び出しが発生する, **Then** ツール名、引数概要、成功/失敗ステータス、実行時間がログに記録される
2. **Given** MCPツール呼び出しが失敗した, **When** ログを確認する, **Then** エラー内容と実行時間が記録されている
3. **Given** ログが出力されている, **When** ログ内容を確認する, **Then** 機密情報（APIキー、トークン等）は含まれていない

---

### User Story 2 - Verboseモードでの詳細ログ確認 (Priority: P2)

開発者として、詳細なデバッグが必要な場合に`mixseek-plus exec --verbose`オプションを指定して、より詳細なログ情報を確認したい。通常時は必要最小限のログのみ出力し、トラブルシューティング時に詳細情報を得られるようにしたい。

**Why this priority**: P1の基本ログ機能の上に構築される拡張機能。デバッグ効率を大幅に向上させるが、P1がなければ成り立たない。

**Independent Test**: `mixseek-plus exec --verbose`でエージェントを実行し、詳細ログがコンソールとファイルに出力されることを確認する。

**Acceptance Scenarios**:

1. **Given** `mixseek-plus exec --verbose`で実行されている, **When** MCPツール呼び出しが発生する, **Then** 詳細なログがコンソールとファイルの両方に出力される
2. **Given** `--verbose`オプションなしで実行されている（デフォルト）, **When** MCPツール呼び出しが発生する, **Then** 基本情報のみがログファイルに記録され、コンソールには出力されない
3. **Given** verboseモードが有効, **When** 長い引数や結果がある, **Then** 適切に切り詰められて可読性が保たれる

---

### User Story 3 - Logfireによるオブザーバビリティ統合 (Priority: P3)

開発者として、`mixseek-plus exec --logfire`オプションを指定してLogfireを使用し、pydantic-aiの自動インストルメンテーションを有効にしたい。分散トレーシングやメトリクス収集を行いたい。オプショナルな機能として、必要な場合のみ有効化できるようにしたい。

**Why this priority**: 高度なオブザーバビリティ機能であり、すべてのユーザーが必要とするわけではない。P1、P2が機能している前提で、追加の価値を提供する。

**Independent Test**: `mixseek-plus exec --logfire`と`logfire`パッケージがインストールされた状態でエージェントを実行し、Logfireにデータが送信されることを確認する。

**Acceptance Scenarios**:

1. **Given** `mixseek-plus exec --logfire`で実行され、logfireパッケージがインストールされている, **When** エージェントが実行される, **Then** pydantic-aiの自動インストルメンテーションが有効になる
2. **Given** `mixseek-plus exec --logfire`で実行されているが、logfireパッケージがインストールされていない, **When** エージェントが起動する, **Then** 警告メッセージが表示され、処理は正常に継続する
3. **Given** `--logfire`オプションなしで実行されている, **When** エージェントが実行される, **Then** Logfire統合は有効化されない

---

### Edge Cases

- ログ出力先ディレクトリ（`$WORKSPACE/logs/`）が存在しない場合、自動で作成される
- 非常に長いツール引数や結果が渡された場合、適切に切り詰められる
- 複数のエージェントが同時にログを出力する場合、競合なく記録される
- ログファイルが大きくなりすぎないよう、ローテーションまたは制限が考慮される

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムMUST MCPツール呼び出し時にツール名、引数概要、成功/失敗ステータス、実行時間（ミリ秒）をログに記録する
- **FR-002**: システムMUST `mixseek-plus exec --verbose`オプションでログの詳細度を制御可能にする（デフォルト: false）
- **FR-003**: システムMUST `mixseek-plus exec --logfire`オプションでLogfire統合の有効/無効を制御可能にする（デフォルト: false）
- **FR-004**: システムMUST ログを`$WORKSPACE/logs/member-agent-YYYY-MM-DD.log`に記録する（既存の`MemberAgentLogger`の出力先と同一）
- **FR-005**: システムMUST 機密情報（APIキー、認証トークン等）をログに含めない（`MemberAgentLogger._sanitize_parameters()`による自動マスキングを活用）
- **FR-006**: システムMUST 長い引数や結果を適切に切り詰める（引数: 100文字、結果: 200文字）
- **FR-007**: システムMUST `--logfire`オプション指定時にlogfireパッケージがインストールされていない場合、警告を出して正常に処理を継続する
- **FR-008**: ユーザーMUST be able to `mixseek-plus exec --verbose`オプションでverboseモードを有効/無効にできる
- **FR-009**: システムMUST 既存のmixseek-coreの`MemberAgentLogger.log_tool_invocation()`を使用してMCPツール呼び出しを記録し、他モデル（Gemini、OpenAI等）と同一のJSON形式でログを出力する

### Key Entities

- **ToolCallLog**: MCPツール呼び出しのログ情報を表現（`MemberAgentLogger.log_tool_invocation()`の出力形式に準拠）
  - event: "tool_invocation"（固定）
  - execution_id: 実行ID
  - tool_name: ツール名
  - parameters: 引数（自動サニタイズ済み）
  - execution_time_ms: 実行時間（ミリ秒）
  - status: success/error
  - timestamp: ISO8601形式タイムスタンプ

- **LogConfiguration**: ログ設定の状態
  - verboseモード有効/無効
  - Logfire有効/無効
  - ログ出力先パス（`$WORKSPACE/logs/member-agent-YYYY-MM-DD.log`）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 開発者はMCPツール呼び出しのログを100%確認できる（見落としゼロ）
- **SC-002**: verboseモード無効時のログ出力によるパフォーマンス影響は5%未満
- **SC-003**: ログから問題の原因特定に必要な情報が80%以上の場合で得られる
- **SC-004**: 新規開発者がログを活用してデバッグを開始できるまで5分以内

## Scope

### In Scope

- **短期対応**: エージェント内での明示的なログ出力（`mixseek-plus exec --verbose`時）
- **中期対応**: Logfireインストルメンテーション（`mixseek-plus exec --logfire`時）、MCP呼び出しログ記録、メッセージ履歴統合

### Out of Scope

- カスタムログフォーマットの設定機能
- ログの外部サービスへの自動送信（Logfire以外）
- リアルタイムログストリーミング
- ログの暗号化

## Assumptions

- mixseek-coreの`MemberAgentLogger`が利用可能で、`log_tool_invocation()`メソッドが存在する
- `mixseek-plus exec`コマンドが既に存在し、`--verbose`および`--logfire`オプションを追加可能である
- ログファイルへの書き込み権限がある
- pydantic-aiのメッセージ履歴からツール呼び出し情報を抽出可能である

## Dependencies

### Parent Specification

- **Issue #8 - ClaudeCodeプロバイダー** (`specs/008-claudecode-provider/spec.md`)
  - `ClaudeCodeModel`: Claude Code CLIをラップしたpydantic-aiモデル実装
  - `BaseClaudeCodeAgent`: ClaudeCodeベースのエージェント基底クラス
  - `create_claudecode_model()`: モデル作成関数

### External Dependencies

- mixseek-core（`MemberAgentLogger`、`BaseMemberAgent`）
- pydantic-ai（メッセージ履歴、`ToolCallPart`、`ToolReturnPart`）
- logfire（オプショナル依存）
- Python標準ライブラリ logging, time, os
