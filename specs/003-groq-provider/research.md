# Research: Groqプロバイダーのサポート追加

**Branch**: `003-groq-provider` | **Date**: 2026-01-17

## 1. pydantic-ai GroqModel

### 初期化パターン

**パターンA: シンプルな文字列指定**
```python
from pydantic_ai import Agent
agent = Agent('groq:llama-3.3-70b-versatile')
```

**パターンB: 直接インスタンス化**（本プロジェクトで採用）
```python
from pydantic_ai.models.groq import GroqModel
model = GroqModel('llama-3.3-70b-versatile')
agent = Agent(model)
```

**パターンC: カスタムプロバイダー設定**
```python
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

model = GroqModel(
    'llama-3.3-70b-versatile',
    provider=GroqProvider(api_key='your-api-key')
)
```

### GroqModel.__init__()パラメータ

- `model_name` (GroqModelName): モデル識別子
- `provider` (Literal["groq", "gateway"] | Provider[AsyncGroq]): デフォルト "groq"
- `profile` (ModelProfileSpec | None): オプション設定
- `settings` (ModelSettings | None): オプション設定

**環境設定**: `GROQ_API_KEY` 環境変数

### 決定事項

- **Decision**: パターンBを採用（`GroqModel`直接インスタンス化）
- **Rationale**: mixseek-plusの`create_model()`で統一的にモデルインスタンスを作成するため
- **Alternatives**: パターンAは文字列パース依存、パターンCはプロジェクト要件を超える設定が必要

---

## 2. Web検索ツール対応

### pydantic-aiでのWeb検索対応

| 機能 | 対応状況 | 詳細 |
|------|---------|------|
| WebSearchTool | ✅ サポート | pydantic-ai組み込みツール |
| GroqModel互換 | ✅ サポート | 標準的なtool定義で利用可能 |

### Groqのツール実装パターン

1. **ビルトイン・ツール**: Groq インフラ上で実行（`groq/compound`等の特定モデルのみ）
2. **MCP統合**: Model Context Protocolによる遠隔ツール呼び出し
3. **ローカルツール呼び出し**（カスタム）: 開発者定義ツール

### 決定事項

- **Decision**: pydantic-aiの`WebSearchTool`を使用したローカルツールパターンを採用
- **Rationale**: すべてのGroqモデルで動作し、mixseek-coreの`WebSearchMemberAgent`と同等の機能を提供
- **Alternatives**: ビルトインツールは`groq/compound`等の特定モデル限定

---

## 3. mixseek-core統合

### MemberAgentFactory

```python
@classmethod
def register_agent(cls, agent_type: str, agent_class: type[BaseMemberAgent]) -> None:
    """Register an agent class for a specific agent type."""
    cls._agent_classes[agent_type] = agent_class
```

- **登録方法**: `MemberAgentFactory.register_agent("groq_plain", GroqPlainAgent)`
- **TOML設定**: `type = "groq_plain"` で自動選択

### create_authenticated_model（Monkey-patch対象）

```python
# mixseek/core/auth.py
def create_authenticated_model(model_id: str) -> GoogleModel | OpenAIModel | AnthropicModel | TestModel:
    auth_provider = detect_auth_provider(model_id)
    # 6プロバイダーのみ対応: google-gla, google-vertex, openai, anthropic, grok, grok-responses
```

### 決定事項

- **Decision**: `create_authenticated_model`をmonkey-patchして`groq:`対応を追加
- **Rationale**: Leader/Evaluatorは内部で`create_authenticated_model`を呼び出すため
- **Alternatives**: mixseek-coreへPR提出（将来的対応、暫定としてpatch）

---

## 4. エージェント別制約（Issue #5より）

### プロバイダー対応マトリクス

| エージェント | Groq対応 | 対応方針 |
|-------------|:--------:|---------|
| Leader | ✅ | patch_core()でGroq対応 |
| Evaluator | ✅ | patch_core()でGroq対応 |
| Member - Plain | ✅ | Custom Agent (`GroqPlainAgent`) |
| Member - Web Search | ✅ | Custom Agent (`GroqWebSearchAgent`) |
| Member - Web Fetch | ❌ | mixseek-core側でAnthropic/Googleのみ許可 |
| Member - Code Execution | ❌ | mixseek-core側でAnthropicのみ許可 |
| Member - Custom | ✅ | 制約なし |

### 決定事項

- **Decision**: Web Fetch/Code Executionは対応不可を明示
- **Rationale**: mixseek-core側の明示的制約（プロバイダー固有ツール依存）
- **Alternatives**: なし（上流の制約）

---

## 5. patch_core()設計

### 実装方針

```python
def patch_core() -> None:
    """mixseek-coreの create_authenticated_model を拡張してGroq対応を追加."""
    from mixseek.core import auth

    original_create_authenticated_model = auth.create_authenticated_model

    def patched_create_authenticated_model(model_id: str):
        if model_id.startswith("groq:"):
            from mixseek_plus.providers.groq import create_groq_model
            model_name = model_id[len("groq:"):]
            return create_groq_model(model_name)
        return original_create_authenticated_model(model_id)

    auth.create_authenticated_model = patched_create_authenticated_model
```

### 決定事項

- **Decision**: 明示的呼び出し必須（暗黙的パッチ禁止）
- **Rationale**: Constitution Article 6（Data Accuracy Mandate）に準拠
- **Alternatives**: インポート時自動パッチ（明示性の原則に反する）

---

## 6. エラーハンドリング戦略

### API呼び出しエラー

| HTTPステータス | エラー種別 | 対応 |
|---------------|-----------|------|
| 401 | 認証エラー | `ModelCreationError` + APIキー確認提案 |
| 429 | レート制限 | `ModelCreationError` + 待機提案 |
| 503 | サービス障害 | `ModelCreationError` + 再試行提案 |
| その他 | 一般エラー | Groq APIメッセージをラップ |

### 決定事項

- **Decision**: GR-032の詳細なエラーラップは`execute()`メソッド内で実装
- **Rationale**: モデル作成時点ではAPIは呼び出されないため
- **Alternatives**: モデル作成時に事前検証（API呼び出しコスト発生）

---

## 7. パフォーマンス特性

### Groq API

- **推論速度**: 300〜1,000+ tokens/秒（従来モデルの10〜100倍）
- **並列ツール実行**: 複数ツール同時実行で遅延最適化
- **レート制限**: RPM/TPMベース（プラン依存）

### 決定事項

- **Decision**: パフォーマンス最適化は初期実装では対象外
- **Rationale**: API呼び出しが主要な遅延要因、クライアント側最適化の効果は限定的
- **Alternatives**: バッチ処理、コネクションプーリング（将来的検討）

---

## 参考資料

- [pydantic-ai GroqModel API Reference](https://ai.pydantic.dev/api/models/groq/)
- [pydantic-ai Groq統合ガイド](https://ai.pydantic.dev/models/groq/)
- [Groq Tool Use Documentation](https://console.groq.com/docs/tool-use)
- [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs)
- Issue #5: エージェント別モデルプロバイダー制約の文書化
