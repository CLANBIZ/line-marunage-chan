# トラブルシューティング

> よくある問題と解決方法

**バージョン**: 2.2.0
**最終更新**: 2025-12-15

---

## 起動時のエラー

### 「ModuleNotFoundError: No module named 'flask'」

**原因**: 依存パッケージがインストールされていない

**解決**:
```bash
pip install -r requirements.txt
```

### 「ModuleNotFoundError: No module named 'google.genai'」

**原因**: 新SDKがインストールされていない

**解決**:
```bash
pip install google-genai
```

### 「Address already in use」

**原因**: ポート5000が既に使用されている

**解決**:
1. 別のターミナルで動いているserver.pyを終了
2. タスクマネージャーでPythonプロセスを終了

### 「Permission denied」

**原因**: ファイルへのアクセス権限がない

**解決**:
1. 管理者権限でターミナルを開く
2. またはフォルダのアクセス権限を確認

---

## API関連のエラー

### 「APIキーが無効です」

**原因**: APIキーが正しくない、または無効化されている

**解決**:
1. [Google AI Studio](https://aistudio.google.com/apikey) でAPIキーを確認
2. 新しいAPIキーを生成
3. **重要**: 請求先アカウントがリンクされているか確認

### 「レート制限に達しました」

**原因**: APIの呼び出し回数が制限を超えた

**レート制限（目安）:**
| 項目 | 制限 |
|------|------|
| リクエスト/分 | 60 |
| リクエスト/日 | 1,500（無料枠） |

**解決**:
1. 数分待ってから再試行
2. 1日の制限に達した場合は翌日まで待つ

### 「画像を生成できません」

**原因**: プロンプトが安全フィルタに引っかかった

**解決**:
1. プロンプトを修正（暴力的・性的な表現を避ける）
2. 人物を含まないプロンプトに変更
3. よりシンプルなプロンプトで試す

### 「ValueError: 許可されていないモデルです」

**原因**: 禁止モデル（gemini-2.x等）を使用しようとした

**解決**:
- コードを変更せず、許可モデルのみを使用
- 許可モデル: `gemini-3-flash-preview`, `gemini-3-pro-image-preview`

---

## 画像生成のエラー

### 「透過PNGが出力されない」

**原因**: nano banana pro は透過PNG非対応

**解決**:
- これは仕様です
- 白背景で生成し、手動でスクショ切り抜きしてください
- 切り抜き方法:
  - Mac: `Command + Shift + 4`
  - Windows: `Win + Shift + S`

### 「グリッド画像がうまく分割できない」

**原因**: 自動分割は不安定

**解決**:
- STEP 4の手動スクショ切り抜きを使用
- 切り抜いた画像をドロップエリアにドロップしてリサイズ

---

## UI関連の問題

### 「画面が真っ白」

**原因**: 静的ファイルが読み込めていない

**解決**:
1. ブラウザのキャッシュをクリア（`Ctrl+Shift+R`）
2. `static/css/style.css` が存在するか確認
3. サーバーを再起動

### 「ボタンが反応しない」

**原因**: JavaScriptエラー

**解決**:
1. ブラウザの開発者ツール（`F12`）でConsoleを確認
2. エラーメッセージを確認
3. `static/js/script.js` が正しく読み込まれているか確認

### 「キャラクター提案が表示されない」

**原因**: APIキーが入力されていない、またはAPI呼び出しエラー

**解決**:
1. APIキーが入力されているか確認
2. 「確認」ボタンでAPI接続をテスト
3. 開発者ツールでネットワークタブを確認

### 「画像リサイズでエラー」

**原因**: 画像形式が非対応、またはファイルが破損

**解決**:
1. PNG, JPG, JPEG, GIF, WEBP のみ対応
2. ファイルサイズは50MB以下
3. 再度スクショを撮り直す

### 「ZIPダウンロードが失敗」

**原因**: 出力フォルダが存在しない

**解決**:
1. まず画像をドロップしてリサイズを実行
2. `data/output/` フォルダを確認

---

## デバッグ方法

### サーバーログを確認

ターミナルに表示されるログを確認してください。

```bash
python server.py
```

エラー発生時のログ例:
```
[キャラ提案] リクエスト: 在宅ワークで疲れたOL
[キャラ提案] 使用モデル: gemini-3-flash-preview
[プロンプト生成] 使用モデル: gemini-3-flash-preview
[画像生成] 使用モデル: gemini-3-pro-image-preview
[英語登録情報] 生成完了
```

### ブラウザの開発者ツール

1. `F12` キーを押す
2. **Console** タブでエラーを確認
3. **Network** タブでリクエストを確認

### APIエンドポイントをテスト

```bash
# API接続確認
curl http://localhost:5000/api/verify-connection \
  -H "Content-Type: application/json"

# キャラクター提案
curl http://localhost:5000/api/propose-characters \
  -H "Content-Type: application/json" \
  -d '{"request": "テスト"}'
```

---

## よくある質問

### Q: 無料で使えますか？

A: Gemini API の画像生成は有料です。
- 1セット: およそ30円（状況により変動）
- 1枚作ってみて24時間後の料金反映を確かめてから量産してください

### Q: 透過PNGは作れますか？

A: nano banana pro は透過PNG非対応です。
白背景で生成し、手動で切り抜いてください。

### Q: 何枚のスタンプを作れますか？

A: 1回の生成で18枚（6x3グリッド）。
LINE申請には8〜40枚が必要です。

### Q: 生成した画像の著作権は？

A: AI生成画像の著作権はグレーゾーンです。
LINE Creators Market のガイドラインを確認し、自己責任でご利用ください。

### Q: gemini-2.x系は使えないの？

A: 使えません。コード内でバリデーションが実装されており、
禁止モデルを使用しようとするとエラーになります。
高品質を維持するため、gemini-3-pro系のみを使用してください。

---

## サポート

解決しない場合は:

1. エラーメッセージとログを確認
2. このドキュメントを再確認
3. [AI_GUIDE.md](AI_GUIDE.md) を確認

---

## 参考リンク

- [Google AI Studio](https://aistudio.google.com/) - APIキー管理
- [Google Cloud Billing](https://console.cloud.google.com/billing) - 請求確認
- [Gemini API ドキュメント](https://ai.google.dev/gemini-api/docs)
- [料金ページ](https://ai.google.dev/pricing)

---

## 関連ドキュメント

| ファイル | 用途 |
|---------|------|
| [AI_GUIDE.md](AI_GUIDE.md) | AIエージェント向けメインガイド |
| [README.md](README.md) | ユーザー向けクイックスタート |

---

## ライセンス

**MIT License** - Copyright (c) 2025 株式会社CLAN (https://clanbiz.net/line-stamp-marunage-chan-LP/)

### 免責事項

このソフトウェアは「現状のまま」提供されます。開発者は一切の責任を負いません。
生成画像の著作権・商標権に関する最終判断はユーザー自身の責任です。

### フォーク時のお願い

改変・再配布する場合は、以下のクレジット表記を記載してください：

```
Original work: LINEスタンプ丸投げちゃん
https://github.com/CLANBIZ/line-marunage-chan
Copyright (c) 2025 株式会社CLAN (https://clanbiz.net/line-stamp-marunage-chan-LP/)
```
