# mixseek-plus

mixseek-coreの拡張パッケージ。Groqモデルサポートやweb_fetch強化などの追加機能を提供します。

## 概要

mixseek-plusは、mixseek-coreのMember/Leader/Evaluatorフレームワークを拡張し、追加プロバイダーのサポートを提供します。

主な機能:
- Model Factory: `create_model()` によるGroq/ClaudeCodeモデルインスタンスの作成
- Memberエージェント: `groq_plain`、`groq_web_search`、`claudecode_plain`、`playwright_markdown_fetch` タイプのエージェント
- Core統合: `patch_core()` によるLeader/EvaluatorへのGroq/ClaudeCodeサポート追加
- Playwright Web Fetcher: ボット対策サイトからもコンテンツを取得できるWebフェッチャー

## 目次

```{toctree}
:caption: 'ドキュメント'
:maxdepth: 2

getting-started
user-guide
api-reference
```
