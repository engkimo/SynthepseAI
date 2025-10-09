# 要件定義サマリ

本ドキュメントは、REQUIREMENTS_DEFINITION.md の要点を短く整理したものです。詳細は元ファイルも参照してください。

## 目的
- 目標を与えるだけで、計画→コード生成→隔離環境での実行→自己修復→学習を自動化する自律エージェントを実現。

## コア機能
- 自動計画・実行: タスク分解・コード生成・依存自動解決・隔離実行。
- 自己修復: 失敗時の原因分析と修正コード適用（リトライ上限あり）。
- 学習/再利用: GraphRAG によるエラーパターン・テンプレート学習、モジュール抽出/再利用。
- 持続的思考: 実行結果を `knowledge_db.json` / `thinking_log.jsonl` へ統合。
- Web知識統合: Tavily → レガシー → 直接API → Firecrawl → モックの多段フォールバック。

## 非機能
- パフォーマンス: 実行開始 ≤ 5s、並行実行、スケール可能。
- 信頼性: 自動エラー回復 ≥ 95%、SQLite 永続化、モックフォールバック。
- セキュリティ: プロジェクト毎 venv 分離、API キー環境変数管理、サンドボックス実行。
- 互換性: Python 3.9+（3.12 は DGL 互換モード）、Windows/macOS/Linux。
- 使用性: CLI中心、JSON 設定、README/設計ドキュメント整備。

## システム構成（ハイライト）
- エージェント: `BaseAgent` → `ToolAgent` → `AutoPlanAgent`
- フロー: `BaseFlow` → `PlanningFlow`
- ツール: `python_project_execute`, `planning`, `file`, `docker`, `system`, `web_crawler`
- 学習: `graph_rag_manager`, `modular_code_manager`, `enhanced_persistent_thinking_ai`, `rgcn_processor`, `rome_model_editor`, `coat_reasoner`
- データ: `TaskDatabase`(SQLite), `knowledge_db.json`, `thinking_log.jsonl`, `knowledge_graph.json`

## 実行・設定
- 実行: `python main.py --goal "..."`、作業ディレクトリは `--workspace`。
- モデル: 既定は OpenAI `gpt-5`（OpenRouter は `claude-3-7-sonnet` 推奨）。
- Weaviate: GraphRAG 利用時のみ Docker で 8080 起動。

## 既知の制約
- ネットワーク遮断環境では外部パッケージ導入が失敗しうるため、stdlib優先のコード生成が望ましい。
- 大規模依存（torch/dgl など）は用途限定での導入を推奨。
