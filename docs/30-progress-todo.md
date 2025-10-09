# プロジェクト進捗・TODO・ネクストアクション

## 概要
本プロジェクトは「常に思考し続けるAI」を目指し、計画→実行→反省/学習→成果物更新を継続的に回すアーキテクチャを採用しています（詳細: `docs/20-continuous-thinking.md`）。

## これまでの進捗（主な変更）
- LLMフォールバック強化（OpenAI/requests/tenacity未導入・ネット不通時もモックで継続）。
- Webツールのフォールバック整備（Tavily未導入時や失敗時にFirecrawl/直叩きへ）。
- 生成スクリプトの自動サニタイズ（壊れたimportや`*_mod`疑似モジュール等を保存前に除去）。
- 成果物の自動出力追加：
  - プラン直後: `workspace/artifacts/<plan_id>/plan.md`, `plan_tasks.json`
  - タスク完了: `report.md`追記、簡易プロット画像（環境対応時）
  - プラン完了: `plan_summary.txt`
- gpt-5対応（温度を自動で1に強制）。
- 依存整合: `numpy==1.26.4`, `tenacity==8.5.0`, `langchain-openai==0.1.19`、`tavily-python`削除。

## 既知の課題
- LLM生成コードの整形/インデント起因の失敗が稀に残存。
- データ取得（例: 上場銘柄/価格）のオンライン前提時、ネット規制環境ではモック結果に留まる。
- 成果物（スライド等）の自動エクスポート未整備（設計方針は策定済）。

## TODO
- [ ] 生成テンプレの強化（安全なimport白/黒リストの拡充、構文検証の追加）。
- [ ] データ取得モードを2系統化（オンライン:yfinance / オフライン: CSV入力）。
- [ ] タスク実行のユニットテスト整備（テンプレ置換/サニタイズ/成果物生成）。
- [ ] スライド自動生成（Marp/Reveal.js/Pandocのいずれか）
- [ ] CIでのモックモード実行と成果物要約の保存。

## ネクストアクション（優先順）
1. オフラインCSV前提テンプレートの追加（必ずPNG/Markdownを出力）。
2. サニタイズ規則の拡張（未知モジュール検出、最低限の構文検証）。
3. スライド生成の最小実装（`report.md`→`slides/`）。
4. 取得データのキャッシュ戦略とリトライ方針の明文化。

## 運用メモ
- 実行: `python main.py --goal "..." --workspace ./workspace --debug`
- 成果物: `workspace/artifacts/<plan_id>/`（報告書/画像/要約）
- ログ: `workspace/debug.log`（進捗監視）、思考ログ: `workspace/persistent_thinking/`
