# Troubleshooting

## 依存やサーバの起動
- 8000/5173 未起動: 依存導入後に `make dev` を再実行（プロジェクトに応じて）。
- Weaviate (8080): `docker-compose up -d` で起動し、`docker ps` で稼働確認。

## PDF 生成
- WeasyPrint 未導入時は HTML フォールバックが正常挙動。WeasyPrint を使う場合は依存を導入してください。

## GitHub CLI
- `gh` 失敗(rc=4): 権限/重複/ネットワークを確認。`gh auth status` で状態確認、必要に応じて `gh auth login`。

## DGL 互換モード（Python 3.12）
- `export DGL_COMPATIBILITY_MODE=1` または `source set_env.sh` を実行。

## 依存導入で失敗する
- 本リポジトリでは仮想環境への導入先を動的検出するよう修正済み。ネットワーク遮断環境では最小依存のタスク実行を推奨します。
