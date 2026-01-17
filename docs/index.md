# mixseek-plus

mixseek-coreの拡張パッケージ。Groqモデルサポートやweb_fetch強化などの追加機能を提供します。

## 概要

mixseek-plusは、mixseek-coreのMember/Leader/Evaluatorフレームワークを拡張し、Groqプロバイダーのサポートを追加します。

主な機能:
- Model Factory: `create_model()` によるGroqモデルインスタンスの作成
- Memberエージェント: `groq_plain`、`groq_web_search` タイプのエージェント
- Core統合: `patch_core()` によるLeader/EvaluatorへのGroqサポート追加

## 目次

```{toctree}
:caption: 'ドキュメント'
:maxdepth: 2

getting-started
user-guide
api-reference
```
