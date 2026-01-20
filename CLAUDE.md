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

## Recent Changes
- 003-groq-provider: Added Python 3.13+ + pydantic-ai (GroqModel), mixseek-core (create_authenticated_model)
