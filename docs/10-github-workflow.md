# GitHub 運用ガイド（イシュー/マイルストン/ラベル）

本プロジェクトでの GitHub 運用の基本手順を示します。組織/リポジトリに合わせて適宜置換してください。

## 認証

```bash
# GitHub CLI 認証
gh auth login
# 状態確認
gh auth status
```

## ラベル初期化（例）

Makefile/スクリプトがある場合:

```bash
make labels-init
```

## マイルストン作成（例）

scriptsがある場合の参考スニペット。`--repo` は自身のリポジトリに置換してください。

```bash
python3 scripts/create_milestones.py \
  --repo ohoriryosuke/patent-searcher \
  --titles M1,M2,M3,M4 \
  --state open \
  --desc "See docs/14-milestones.md"
```

## イシュー一括作成（例）

```bash
python3 scripts/create_issues.py \
  --repo ohoriryosuke/patent-searcher \
  --seeds .github/issue_seeds.json
```

上記は別プロジェクトの例です。本リポジトリでは `--repo <your_org>/<your_repo>` に読み替えて下さい。

## トラブルシュート運用

各開発サイクルで、以下の代表的な事象を docs に毎回起票し、達成したらクローズしてください。

- 8000/5173 未起動: 依存導入後に `make dev` 再実行（必要に応じて）。
- PDF 未生成: WeasyPrint 未導入時は HTML フォールバック（正常）。
- gh 失敗(rc=4): 権限/重複/ネットワークを確認（`gh auth status`）。

「起票→対処→クローズ」の履歴を残すことで、再発時の復旧時間を短縮できます。
