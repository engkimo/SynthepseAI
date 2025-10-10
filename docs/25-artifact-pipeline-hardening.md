# 成果物パイプラインの不具合と堅牢化（2025-10-10）

本書は「成果物（report.md/画像/summary/slides）が `workspace/artifacts/<plan_id>/` に出力されにくい」問題の調査結果と修正点、検証方法をまとめたものです。

## 症状
- `report.md` や画像（`plot_*.png`）が生成されない、または途中で失敗。
- `debug.log` に `SyntaxError: unmatched '}'` など構文崩壊が記録。
- LLM呼び出しが長時間ブロック（ネット制限下でPOST後に待ち続ける）。
- 生成された `workspace/project_*/task_*.py` に無効な行（例: `import 2024`）や裸の `}` が混在。

## 原因
1. 二重テンプレート化
   - PlanningTool がテンプレ適用済み「フルスクリプト」を生成 → Executor 側で再びテンプレに埋め込み直し、テンプレ断片や壊れたインポートが混入し構文崩壊。
2. サニタイズの不足
   - 非識別子の `import` 行（例: `import 2024`）や裸のブレース行、誤った `ARTIFACTS_BASE` の混入を除去できていない。
3. LLM 呼び出しのタイムアウト未設定
   - オフライン/ネット制限下でリクエストがハングし、実行フローが詰まる。

## 対応（コード修正）
- core/tools/python_project_execute.py
  - 既にテンプレ適用済みか判定する `_looks_like_full_script()` を追加し、該当時は「再テンプレ適用せず保存・実行」に切替。
  - サニタイズ強化：
    - 非識別子 `import` 行を除去。
    - 裸の括弧/ブレース行、Markdownフェンスを除去。
    - `ARTIFACTS_BASE = "./workspace/artifacts"` を、`CWD/..` から `artifacts` を解決する安全実装に差し替え。
  - 保存前に早期 `compile()`（構文チェック）を追加（失敗しても実行続行）。
- core/llm.py
  - 明示タイムアウト `LLM_TIMEOUT_SECONDS`（既定20秒）を導入。
  - `FORCE_MOCK_LLM=1` で完全モックへ即時切替可能に（オフライン検証用）。

## 検証手順
- オフライン/モック検証（推奨）
  - 実行: `FORCE_MOCK_LLM=1 python main.py --goal "2024年のプライム上場企業のデータ分析して可視化" --workspace ./workspace --debug`
  - 期待される成果物（`workspace/artifacts/<plan_id>/`）:
    - プラン直後: `plan.md`, `plan_tasks.json`
    - タスク完了ごと: `report.md` に時系列追記、可能なら `plot_*.png`
    - プラン完了: `plan_summary.txt`、`slides/slides.md`
- オンライン検証（APIキー有り）
  - 同コマンドでOK。ネット不安定時もタイムアウトで詰まりを回避、モックへリカバリ。

## 留意事項
- `venv` 作成時の `black` インストールはネット環境で失敗しうるが、失敗時は警告のみで続行。
- 古い `project_*` ディレクトリのスクリプトが壊れていても、新規 `plan_id` 実行時に影響は限定的（上記修正で再発を抑止）。

## 次アクション（提案）
- CSVオフライン前提テンプレの追加（常にMarkdown表出力、PNGは可能時のみ）。
- サニタイズのルール強化（未知モジュール検知、構文バリデーションの拡張）。
- スライド生成の最小拡張（`##` 見出しが無い場合でも表紙/概要を自動生成）。

