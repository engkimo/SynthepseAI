# OpenRouter 統合ガイド

SynthepseAIは、OpenRouterを通じてClaude 3.7などの高性能モデルを使用できるようになりました。この機能を使用するには、以下の手順に従ってください。

## 1. OpenRouter APIキーの取得

1. [OpenRouter](https://openrouter.ai/)にアクセスし、アカウントを作成します。
2. APIキーを取得します。

## 2. APIキーの設定

以下のいずれかの方法でAPIキーを設定します：

### 環境変数を使用する場合

```bash
export OPENROUTER_API_KEY=your_api_key_here
```

### .envファイルを使用する場合

プロジェクトのルートディレクトリに`.env`ファイルを作成し、以下の内容を追加します：

```
OPENROUTER_API_KEY=your_api_key_here
```

### config.jsonファイルを使用する場合

`config.json`ファイルに以下のように追加します：

```json
{
  "openrouter_api_key": "your_api_key_here",
  "llm_provider": "openrouter",
  "model": "anthropic/claude-3-7-sonnet"
}
```

## 3. 設定の変更

`config.json`ファイルで以下の設定を行います：

```json
{
  "llm_provider": "openrouter",
  "model": "anthropic/claude-3-7-sonnet",
  "temperature": 0.5,
  "enable_multi_agent": true,
  "specialized_agents": [
    {
      "name": "コードエキスパート",
      "role": "プログラミング専門家",
      "expertise": ["コード生成", "デバッグ", "最適化"],
      "model_name": "anthropic/claude-3-7-sonnet",
      "temperature": 0.3,
      "provider": "openrouter"
    },
    {
      "name": "リサーチャー",
      "role": "研究者",
      "expertise": ["データ分析", "情報検索", "文献調査"],
      "model_name": "anthropic/claude-3-7-sonnet",
      "temperature": 0.5,
      "provider": "openrouter"
    }
  ]
}
```

## 4. 利用可能なモデル

OpenRouterでは以下のモデルが利用可能です：

- `anthropic/claude-3-7-sonnet` - Claude 3.7 Sonnet
- `anthropic/claude-3-5-sonnet` - Claude 3.5 Sonnet
- `anthropic/claude-3-opus` - Claude 3 Opus
- `anthropic/claude-3-haiku` - Claude 3 Haiku
- `google/gemini-1.5-pro` - Gemini 1.5 Pro
- `meta-llama/llama-3-70b-instruct` - Llama 3 70B Instruct

詳細なモデルリストは[OpenRouterのドキュメント](https://openrouter.ai/docs)を参照してください。

## 5. 使用例

```bash
python main.py --goal "データ分析タスクを実行して結果をグラフ化する" --config ./config.json
```

## 注意事項

- OpenRouterの利用には料金が発生します。詳細は[OpenRouterの料金ページ](https://openrouter.ai/pricing)を確認してください。
- 一部のモデルは応答速度が遅い場合があります。特にClaude 3 Opusなどの大規模モデルを使用する場合は注意してください。
- APIキーは安全に管理し、公開リポジトリにコミットしないでください。
