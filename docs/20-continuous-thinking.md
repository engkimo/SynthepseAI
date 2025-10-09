# 継続的思考アーキテクチャ（Continuous Thinking）

本プロジェクトは「常に思考し続けるAI」を中核に据え、計画→実行→反省/学習→アーティファクト更新を継続的に回す設計です。停止条件を設けず、最新の知見を成果物へ反映し続けます。

## コア概念と流れ
- 計画（Planning）：`main.py` → `PlanningFlow` → `AutoPlanAgent` → タスク分解/依存管理。
- 実行（Execution）：各タスクはテンプレート（`core/script_templates.py`）に基づきコード生成→実行。
- 反省/学習（Reflection/Learning）：`EnhancedPersistentThinkingAI` が結果を分析・知識更新・自己反省（COAT）・知識グラフ更新（R-GCN）。
- 継続思考（Continuous Thinking）：バックグラウンドスレッドで`start_continuous_thinking()`を起動し、タスクの合間/後も思考を継続。

## アーティファクト戦略
- 出力先: `workspace/artifacts/<plan_id>/`
  - `plan.md` / `plan_tasks.json`: プラン作成直後に出力。
  - `report.md`: 各タスク完了時に結果プレビューを追記（時系列で蓄積）。
  - 画像（例: `plot_YYYYMMDD_HHMMSS.png`）: 可視化が可能な環境では自動生成（プレースホルダー含む）。
  - `plan_summary.txt`: プラン完了時の概要。
- 更新ポリシー: 追記方式（append）で破壊的変更を避け、履歴を保持。タイムスタンプ付きで「今の最善」を上書きし続ける思想。

## いつ更新されるか
- タスク成功時: `report.md` と画像を追記。
- プラン生成直後: `plan.md` と `plan_tasks.json` を作成。
- プラン完了時: `plan_summary.txt` を出力。
- 継続思考中: 新たな知見に応じた将来タスク/改善提案が思考ログ（`workspace/persistent_thinking/`）へ蓄積され、次回実行で反映。

## スライド/ドキュメントの自動生成
- 方針: `report.md` をソースとして将来的にスライド（例: Marp/Reveal.js/Pandoc）を生成し、`workspace/artifacts/<plan_id>/slides/` に配置。
- 依存導入が不要な範囲でまずはMarkdown集約を継続し、必要に応じてエクスポート機構を追加します。

## 運用メモ
- 実行: `python main.py --goal "..." --workspace ./workspace --debug`
- マルチエージェント: `config.json` の `enable_multi_agent` を切替（デフォルトで有効/無効を調整）。
- 秘密情報は`.env`にのみ。`workspace/`配下はコミット禁止（成果物はレビュー用の一時生成物）。
