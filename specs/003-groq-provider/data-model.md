# Data Model: Groqプロバイダーのサポート追加

**Branch**: `003-groq-provider` | **Date**: 2026-01-17

## エンティティ一覧

### 1. ModelCreationError（既存）

**説明**: モデル作成時のエラーを表す例外

**属性**:

| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| message | str | ✓ | エラーメッセージ |
| provider | str \| None | - | エラーが発生したプロバイダー |
| suggestion | str | - | ユーザーへの解決策の提案 |

**不変条件**:
- `message`は空文字不可

**実装ファイル**: `src/mixseek_plus/errors.py`

---

### 2. GroqPlainAgent（既存）

**説明**: Groqモデルを使用したPlain Member Agent

**属性**:

| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| config | MemberAgentConfig | ✓ | エージェント設定（mixseek-core） |
| _agent | Agent[GroqAgentDeps, str] | ✓ | pydantic-ai Agentインスタンス |

**継承**: `BaseMemberAgent` (mixseek-core)

**不変条件**:
- `config.model`は`groq:`プレフィックスで始まること
- `GROQ_API_KEY`環境変数が設定されていること

**メソッド**:
- `async execute(task: str, context: dict | None, **kwargs) -> MemberAgentResult`

**実装ファイル**: `src/mixseek_plus/agents/groq_agent.py`

---

### 3. GroqWebSearchAgent（新規）

**説明**: Groqモデルを使用したWeb検索機能付きMember Agent

**属性**:

| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| config | MemberAgentConfig | ✓ | エージェント設定 |
| _agent | Agent[GroqAgentDeps, str] | ✓ | pydantic-ai Agent（WebSearchTool付き） |

**継承**: `BaseMemberAgent` (mixseek-core)

**不変条件**:
- `config.model`は`groq:`プレフィックスで始まること
- `GROQ_API_KEY`環境変数が設定されていること

**メソッド**:
- `async execute(task: str, context: dict | None, **kwargs) -> MemberAgentResult`

**実装ファイル**: `src/mixseek_plus/agents/groq_web_search_agent.py`

---

### 4. GroqAgentDeps（既存）

**説明**: Groqエージェントの依存関係コンテナ

**属性**:

| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| config | MemberAgentConfig | ✓ | エージェント設定 |

**実装ファイル**: `src/mixseek_plus/agents/groq_agent.py`

---

## 定数・設定

### プロバイダー定数（既存）

**ファイル**: `src/mixseek_plus/providers/__init__.py`

```python
GROQ_PROVIDER_PREFIX: str = "groq:"

CORE_PROVIDER_PREFIXES: frozenset[str] = frozenset({
    "google-gla:",
    "google-vertex:",
    "openai:",
    "anthropic:",
    "grok:",
    "grok-responses:",
})

ALL_PROVIDER_PREFIXES: frozenset[str] = CORE_PROVIDER_PREFIXES | {GROQ_PROVIDER_PREFIX}
```

---

## 関数シグネチャ

### create_model（既存）

```python
def create_model(model_id: str) -> GroqModel | Model:
    """モデルIDからLLMモデルインスタンスを作成する.

    Args:
        model_id: プロバイダープレフィックス付きのモデルID

    Returns:
        LLMモデルインスタンス

    Raises:
        ModelCreationError: モデル作成に失敗した場合
    """
```

### create_groq_model（既存）

```python
def create_groq_model(model_name: str) -> GroqModel:
    """Groqモデルインスタンスを作成する.

    Args:
        model_name: モデル名（例: "llama-3.3-70b-versatile"）

    Returns:
        GroqModelインスタンス

    Raises:
        ModelCreationError: APIキーが未設定または形式が不正な場合
    """
```

### validate_groq_credentials（既存）

```python
def validate_groq_credentials() -> None:
    """Groq APIキーの検証を行う.

    Raises:
        ModelCreationError: APIキーが未設定、空、または形式が不正な場合
    """
```

### patch_core（新規）

```python
def patch_core() -> None:
    """mixseek-coreの create_authenticated_model を拡張してGroq対応を追加.

    この関数を呼び出すと、Leader/Evaluatorで groq: プレフィックスの
    モデルが使用可能になる。

    Usage:
        import mixseek_plus
        mixseek_plus.patch_core()

    Note:
        - 明示的に呼び出す必要がある（自動適用されない）
        - 複数回呼び出しても安全（冪等性保証）
    """
```

---

## 状態遷移

### Monkey-patch状態

```
┌──────────────────┐
│  Unpatched       │
│  (初期状態)       │
└────────┬─────────┘
         │ patch_core()
         ▼
┌──────────────────┐
│  Patched         │
│  (Groq対応済み)   │
└──────────────────┘
```

**状態説明**:
- `Unpatched`: mixseek-coreは6プロバイダーのみ対応
- `Patched`: groq:プレフィックスもLeader/Evaluatorで使用可能

---

## 依存関係図

```
┌─────────────────────────────────────────────────────────────┐
│                      mixseek-plus                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐     ┌─────────────────────────────┐   │
│  │  __init__.py    │     │  model_factory.py           │   │
│  │  (exports)      │────▶│  create_model()             │   │
│  └─────────────────┘     └──────────┬──────────────────┘   │
│                                     │                       │
│          ┌──────────────────────────┼───────────────────┐   │
│          ▼                          ▼                   │   │
│  ┌───────────────────┐   ┌──────────────────────────┐   │   │
│  │  providers/groq   │   │  mixseek-core            │   │   │
│  │  create_groq_     │   │  create_authenticated_   │   │   │
│  │  model()          │   │  model()                 │   │   │
│  └─────────┬─────────┘   └──────────────────────────┘   │   │
│            │                                             │   │
│            ▼                                             │   │
│  ┌─────────────────────────────────────────────────┐    │   │
│  │  pydantic-ai.models.groq.GroqModel              │    │   │
│  └─────────────────────────────────────────────────┘    │   │
│                                                          │   │
│  ┌─────────────────────────────────────────────────┐    │   │
│  │  agents/                                         │    │   │
│  │  ┌──────────────────┐ ┌────────────────────┐    │    │   │
│  │  │ GroqPlainAgent   │ │ GroqWebSearchAgent │    │    │   │
│  │  └────────┬─────────┘ └──────────┬─────────┘    │    │   │
│  │           │                       │              │    │   │
│  │           └───────────┬───────────┘              │    │   │
│  │                       ▼                          │    │   │
│  │           ┌──────────────────────────┐          │    │   │
│  │           │  mixseek-core            │          │    │   │
│  │           │  BaseMemberAgent         │          │    │   │
│  │           └──────────────────────────┘          │    │   │
│  └─────────────────────────────────────────────────┘    │   │
└─────────────────────────────────────────────────────────────┘
```

---

## エラーコード

| コード | 発生条件 | メッセージ例 |
|--------|----------|-------------|
| GROQ_API_KEY_MISSING | 環境変数未設定 | GROQ_API_KEY環境変数が設定されていません |
| GROQ_API_KEY_INVALID | 形式不正（gsk_で始まらない） | GROQ_API_KEYの形式が不正です |
| INVALID_MODEL_FORMAT | コロンなし | モデルIDは 'provider:model-name' 形式で指定してください |
| UNSUPPORTED_PROVIDER | 未知のプロバイダー | サポートされていないプロバイダー: xxx |
| EMPTY_TASK | 空タスク | Task cannot be empty or contain only whitespace |
| TOKEN_LIMIT_EXCEEDED | トークン超過 | Tool call generation incomplete due to token limit |
| EXECUTION_ERROR | 実行時エラー | (詳細はAPIレスポンスによる) |
