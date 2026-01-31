# CLAUDE.md

## プロジェクト概要

**mixseek-plus**はmixseek-coreの拡張パッケージ。

**参照ドキュメント**:
- `.specify/memory/constitution.md` - プロジェクト憲法
- `.claude/docs.md` - ドキュメント作成標準
- `.claude/git-conventions.md` - Git命名規則

## 開発ワークフロー

### DDD（ドキュメント駆動開発）

**原則**: 実装前にドキュメント影響を確認し、必要に応じて更新

**ワークフロー開始時のチェック**:
- README.mdに更新すべき情報がないか
- docs/に更新すべきドキュメントがないか
- specs/に関連する仕様がないか

**開始方法**（状況に応じて選択）:

**A. 仕様定義から始める場合（speckit）**:
1. `/speckit.specify` → `specs/<issue>-<name>/spec.md`
2. `/speckit.plan` → `plan.md`, `research.md`, `data-model.md`
3. `/speckit.tasks` → `tasks.md`
4. `/speckit.implement` → TDDに従って実装

**B. Issueから始める場合（issue-workflow）**:
1. `/start-issue <number>` → Issue開始、ブランチ作成
2. TDDに従って実装
3. `/commit-push-pr` → コミット・プッシュ・PR作成
4. `/review-pr-comments` → レビュー対応
5. `/merge-pr <number>` → PR統合

**必須チェック**:
- 実装前にドキュメント影響を確認
- 仕様が曖昧な場合は明確化要求
- 品質ゲート通過後にコミット

#### doc-updaterスキル発動条件

以下の状況でdoc-updaterスキル（`/doc-updater`）を起動:

1. **API/インターフェース変更**: 公開クラス・関数・メソッドのシグネチャ変更時
2. **新機能追加**: 新しいクラス、モジュール、重要な機能の追加時
3. **アーキテクチャ変更**: システム設計・構造に影響する変更時
4. ユーザーからの明示的なドキュメント更新依頼時
5. コードとドキュメントの乖離を検出した時

**参照**: `.claude/skills/doc-updater/SKILL.md`

### TDD必須

- 実装前にテスト作成 → ユーザー承認 → Red確認
- 1機能 = 1テストファイル（例: `test_auth.py` ← `auth.py`）

## 非交渉的ルール（例外なし）

### 仕様優先

- 実装前に仕様確認必須
- 曖昧な仕様は実装停止 → 明確化要求

### 品質チェック

- コミット前: `uv run ruff check --fix . && uv run ruff format . && uv run mypy .`
- テスト実行: `uv run pytest`
- 全エラー解消まで次工程禁止

### 型安全

- 全関数・メソッドに型注釈必須
- `Any`型禁止、`| None`推奨

## 禁止事項

- マジックナンバー・ハードコード値
- 暗黙的フォールバック・デフォルト値
- コード重複（3回以上は抽出）
- V2/V3クラス作成（既存を修正）
- 不要なラッパー・過剰抽象化

## 命名規則

- 詳細: `.claude/git-conventions.md`
- specs/: `<3桁issue番号>-<name>`（例: `001-auth`）
- ブランチ: ゼロパディングなし

## Python

- システムの`python3`を使用しないこと
- `uv run` または `.venv/bin/python` を使用

## CLIコマンド

- **コマンド名**: `mixseek-plus` または `mskp`（短縮形）
- **チーム実行**: `mskp team "タスク" --config <config.toml>`

## 技術スタック

- **言語**: Python 3.13+
- **CLIフレームワーク**: Typer 0.15+
- **データバリデーション**: Pydantic 2.10+
- **UI**: Rich 13.9+
- **ブラウザ自動化**: Playwright
- **LLM**: Groq
- **パッケージ管理**: uv
- **品質ツール**: ruff, mypy, pytest
- **ドキュメント**: Sphinx + MyST-Parser + Mermaid

## Active Technologies
- Python 3.13+ + pydantic-ai (GroqModel), mixseek-core (create_authenticated_model) (003-groq-provider)
- Python 3.13+ + pydantic-ai (GroqModel), mixseek-core (create_authenticated_model, BaseMemberAgent, MemberAgentConfig) (003-groq-provider)
- Python 3.13+ + claudecode-model, pydantic-ai, mixseek-core (create_authenticated_model, BaseMemberAgent, MemberAgentConfig) (008-claudecode-provider)
- Python 3.13+ + Playwright, MarkItDown, pydantic-ai, mixseek-core (BaseMemberAgent, MemberAgentConfig, MemberAgentFactory) (031-playwright-markdown-fetch)
- File-based logging (`$WORKSPACE/logs/member-agent-YYYY-MM-DD.log`) (033-claudecode-logging)
- Python 3.13+ + pydantic-ai, mixseek-core (BaseMemberAgent, MemberAgentConfig, MemberAgentFactory), tavily-python, claudecode-model (039-tavily-search-agent)

## Agent Skills

MixSeek-Plusは`skills/`ディレクトリにAgent Skills（agentskills.io仕様準拠）を提供しています。

### 使用方法（重要）

**ユーザーのリクエストが以下のキーワードに該当する場合、対応するSKILL.mdを読み込み、その手順に従って実行してください。**

| トリガーキーワード | 実行するスキル | 読み込むファイル |
|-------------------|---------------|-----------------|
| 「ワークスペースを初期化」「mixseekのセットアップ」「ワークスペースを作成」「プリセットを作成」「claudecode.tomlを生成」 | workspace-init | `skills/mixseek-workspace-init/SKILL.md` |
| 「チームを作成」「エージェント設定を生成」「チーム設定」 | team-config | `skills/mixseek-team-config/SKILL.md` |
| 「オーケストレーターを設定」「チーム競合設定」「複数チームで競わせる」 | orchestrator-config | `skills/mixseek-orchestrator-config/SKILL.md` |
| 「評価設定を作成」「スコアリング設定」「メトリクスを設定」 | evaluator-config | `skills/mixseek-evaluator-config/SKILL.md` |
| 「設定を検証」「TOMLをチェック」「バリデーション」「ワークスペースの検証」 | config-validate | `skills/mixseek-config-validate/SKILL.md` |
| 「使えるモデル」「モデル一覧」「どのモデルがある」「モデルを取得」「APIからモデル」 | model-list | `skills/mixseek-model-list/SKILL.md` |
| 「プロンプトを設定」「プロンプトビルダーを作成」「ラウンド別プロンプト」「プロンプトテンプレート」 | prompt-builder | `skills/mixseek-prompt-builder/SKILL.md` |
| 「デバッグ」「ログを有効化」「verbose」「ログレベル」「デバッグモード」 | debug | `skills/mixseek-debug/SKILL.md` |
| 「ワークスペースの設定を調査」「設定の問題を調べて」「なぜ○○モデルが使われた」「設定が反映されない」「デフォルト値が使われる」 | 複数スキル参照 | `skills/mixseek-orchestrator-config/SKILL.md`, `skills/mixseek-evaluator-config/SKILL.md`, `skills/mixseek-team-config/SKILL.md` |

### 実行手順

1. ユーザーのリクエストからトリガーキーワードを検出
2. 対応する`SKILL.md`ファイルを**必ず読み込む**
3. SKILL.md内の「使用方法」セクションに従ってステップバイステップで実行
4. 必要に応じて`scripts/`や`references/`ディレクトリ内のファイルも参照

### スキル一覧

| スキル名 | 説明 |
|---------|------|
| `mixseek-workspace-init` | ワークスペース初期化（ディレクトリ構造・プリセットファイル作成） |
| `mixseek-team-config` | チーム設定TOML生成（Leader/Member Agent） |
| `mixseek-orchestrator-config` | オーケストレーター設定生成（複数チーム競合） |
| `mixseek-evaluator-config` | 評価・判定設定生成（メトリクス、重み付け） |
| `mixseek-config-validate` | TOML設定ファイルの検証 |
| `mixseek-model-list` | API経由でLLMモデル一覧を動的取得（フォールバック対応） |
| `mixseek-prompt-builder` | プロンプトビルダー設定生成（Team/Evaluator/Judgmentテンプレート） |
| `mixseek-debug` | デバッグ機能の有効化・ログ出力制御 |

### mixseek-plus拡張機能

mixseek-plusでは以下の拡張プロバイダーとエージェントタイプが利用可能です:

**拡張プロバイダー**:
- `groq:*` - Groq高速推論（`GROQ_API_KEY`必要）
- `claudecode:*` - ClaudeCode組み込みツール統合（CLI認証）

**拡張エージェントタイプ**:
- `groq_plain` - Groq基本テキスト生成
- `groq_web_search` - Groq + Tavily Web検索
- `tavily_search` - Tavily検索（3ツール: search, extract, qna）
- `claudecode_plain` - ClaudeCode基本エージェント
- `claudecode_tavily_search` - ClaudeCode + Tavily検索
- `playwright_markdown_fetch` - Playwright + MarkItDown

詳細は `skills/mixseek-model-list/SKILL.md` および `skills/mixseek-team-config/references/TOML-SCHEMA.md` を参照。

## Recent Changes
- 003-groq-provider: Added Python 3.13+ + pydantic-ai (GroqModel), mixseek-core (create_authenticated_model)
