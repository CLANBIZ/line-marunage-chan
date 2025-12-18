# LINEスタンプ丸投げちゃん - AIエージェントガイド

> **AIエージェントへの指示**
> このガイドに従って、ユーザーのLINEスタンプ作成を補助してください。
> 常に「高品質な画像生成」と「ユーザーの手間削減」を優先してください。
>
> **重要**: 著作権・商標権に関する最終判断はユーザー自身に委ねてください。

**バージョン**: 2.2.0
**最終更新**: 2025-12-15

---

## TL;DR（これだけ覚えろ）

```
============================================================
【ワークフロー】

STEP 1: APIキー入力（Google AI Studio）
STEP 2: リクエスト入力（任意）→「キャラクターを提案してもらう」→ 5案から選択
STEP 3: 「画像を生成する」→ 6x3グリッド画像（18枚）
STEP 4: 手動でスクショ切り抜き → ドロップしてリサイズ → ZIPダウンロード
STEP 5: LINE登録情報（日本語/英語自動生成）

所要時間: 約10〜15分
費用: 約23〜25円/セット
============================================================

【使用モデル（厳格ルール）】

✅ 許可モデル:
  - テキスト生成: gemini-3-flash-preview
  - 画像生成: gemini-3-pro-image-preview

❌ 絶対に使用禁止:
  - gemini-2.0-flash
  - gemini-2.5-flash
  - gemini-1.5-flash
  - gemini-1.5-pro
  - その他すべての gemini-2.x, gemini-1.x 系

バリデーション: core/gemini_client.py で実装済み（禁止モデルはエラー）
============================================================
```

---

## よくあるミス（最初に読め）

| ミス | 原因 | 対策 |
|------|------|------|
| 「透過PNGにならない」 | Gemini 3 Pro は透過非対応 | 白背景で生成し、手動で切り抜き |
| 「グリッドがうまく分割できない」 | 自動分割は不安定 | STEP 4の手動スクショ切り抜きを使用 |
| 「APIキーが無効」 | 請求設定が未完了 | Google AI Studioで請求先アカウントをリンク |
| 「禁止モデルエラー」 | gemini-2.x系を使用 | 許可モデルのみ使用（上記参照） |
| 「画像生成が拒否される」 | 安全フィルタ | プロンプトから暴力的・性的表現を削除 |

---

## ツールの使い方を知りたいとき（優先順）

1. **このファイル（AI_GUIDE.md）** の「ワークフロー」セクション
2. **TROUBLESHOOTING.md** エラー発生時
3. **PROMPTS.md** 実績プロンプト例が必要な時
4. **GEMINI_API_GUIDE.md** API詳細が必要な時
5. **ARCHITECTURE.md** システム設計を理解したい時

---

## 起動方法

```bash
# プロジェクトフォルダに移動
pip install -r requirements.txt
python server.py
```

ブラウザで http://localhost:5000 を開く

**サーバー起動成功後、ユーザーに以下を案内:**

```
✅ サーバーが起動しました！ブラウザで http://localhost:5000 が開いているはずです。

📋 **Step 1: APIキーを取得**
1. Google AI Studio (https://aistudio.google.com/apikey) でAPIキーを作成
2. 請求先アカウントをリンク（画像生成は有料）
3. UIの「APIキー」欄に入力 → 「確認」ボタン

準備ができたら「スタンプを作りたい」と伝えてください！
```

---

## ワークフロー詳細

### STEP 1: Gemini API 接続

1. [Google AI Studio](https://aistudio.google.com/apikey) でAPIキーを取得
2. **重要**: 従量課金の請求設定が必要（画像生成は有料）
3. UIのAPIキー欄に入力 → 「確認」ボタン

**確認成功時の表示:**
- テキストモデル: gemini-3-flash-preview
- 画像モデル: gemini-3-pro-image-preview

### STEP 2: キャラクター企画

**リクエスト入力欄（任意）**
- 例: `在宅ワークで疲れたOL`
- 例: `コーヒー中毒のペンギン`
- 空欄の場合はAIが自由に5案を提案

**「キャラクターを提案してもらう」ボタンをクリック**

AIが以下を提案:
- キャラ名
- コンセプト
- ターゲット層

### STEP 3: スタンプ画像生成

選択したキャラクターで「画像を生成する」をクリック

**処理内容:**
1. AIが英語プロンプトを生成
2. Gemini 3 Pro Image Preview で6x3グリッド画像を生成
3. 18枚のスタンプが1枚にまとまった画像が表示

**生成時間**: 30秒〜1分

### STEP 4: 手動で切り抜き & リサイズ

**切り抜き方法:**
- Mac: `Command + Shift + 4`
- Windows: `Win + Shift + S`

**画像リサイズ:**
切り抜いた画像をドラッグ&ドロップすると:
1. LINE仕様（370x320px）に自動リサイズ
2. main.png（240x240）、tab.png（96x74）も自動生成
3. ZIPでダウンロード可能

### STEP 5: LINE登録情報

**英語情報自動生成:**
- タイトル（日本語）
- タイトル（英語）← 自動翻訳
- 説明文（日本語）
- 説明文（英語）← 自動翻訳
- コピーライト

---

## 絶対にやってはいけないこと

### 1. 禁止モデルを使用しようとする

```
❌ NG: gemini-2.0-flash で画像生成
❌ NG: gemini-1.5-pro でテキスト生成

✅ OK: gemini-3-flash-preview（テキスト）
✅ OK: gemini-3-pro-image-preview（画像）
```

### 2. 透過PNG出力を約束する

```
❌ NG: 「透過PNGで出力します」
     → Gemini 3 Pro は透過非対応

✅ OK: 「白背景で生成し、手動で切り抜いてください」
```

### 3. 著作権侵害を助長する

```
❌ NG: 「ピカチュウ風のキャラクター」を生成
❌ NG: 有名キャラクターに酷似した画像を意図的に生成

✅ OK: オリジナルキャラクターのみ提案
```

### 4. ユーザーを待たせて説明だけする

```
❌ NG: 長々と説明してから「やりますか？」と聞く

✅ OK: サーバー起動してUIを開き、操作方法を簡潔に案内
```

---

## API エンドポイント

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/verify-connection` | POST | API接続確認 |
| `/api/propose-characters` | POST | キャラクター5案を提案 |
| `/api/generate-grid` | POST | グリッド画像を生成 |
| `/api/resize-stamps` | POST | 画像をLINE仕様にリサイズ |
| `/api/download/<folder>` | GET | ZIPダウンロード |

### キャラクター提案（リクエスト付き）

```bash
curl http://localhost:5000/api/propose-characters \
  -H "Content-Type: application/json" \
  -d '{"request": "在宅ワークで疲れたOL"}'
```

### グリッド画像生成

```bash
curl http://localhost:5000/api/generate-grid \
  -H "Content-Type: application/json" \
  -d '{"character": {"name": "虚無猫", "concept": "現代社会に疲れた猫"}}'
```

---

## Pythonコードでの使用

```python
from core.gemini_client import GeminiClient

client = GeminiClient(api_key="YOUR_API_KEY")

# 1. キャラクター提案（リクエスト付き）
characters, model_info = client.propose_characters("在宅ワークで疲れたOL")

# 2. 英語プロンプト生成
prompt, _ = client.create_grid_prompt(characters[0])

# 3. 画像生成
image, _ = client.generate_image(prompt)
image.save("grid.png")

# 4. 英語登録情報生成
en_info = client.generate_registration_info(characters[0])
print(en_info['title_en'], en_info['description_en'])
```

---

## 料金目安

| 処理 | 料金 | API呼び出し |
|------|------|------------|
| キャラ企画（5案） | 約1〜2円 | テキスト生成 |
| プロンプト生成 | 約1〜2円 | テキスト生成 |
| 画像生成（1枚） | 約20円 | 画像生成 |
| 英語登録情報生成 | 約1円 | テキスト生成 |
| 画像リサイズ | **無料** | ローカル処理 |
| **1セット合計** | **約23〜25円** | - |

---

## LINE仕様

| 画像 | サイズ | 用途 |
|-----|-------|------|
| スタンプ画像 | 370 x 320 px | メイン（8〜40枚） |
| メイン画像 | 240 x 240 px | ストア表示 |
| タブ画像 | 96 x 74 px | トークルーム |

---

## プロジェクト構成

```
LINE/
├── server.py              # Flask バックエンド
├── index.html             # Web UI
├── static/
│   ├── css/style.css      # Glassmorphism デザイン
│   └── js/script.js       # フロントエンドロジック
├── core/
│   ├── gemini_client.py   # Gemini API クライアント（モデルバリデーション含む）
│   ├── stamp_processor.py # 画像処理（リサイズ、LINE仕様変換）
│   └── line_spec.py       # LINE仕様定義
├── data/
│   ├── uploads/           # アップロード画像
│   └── output/            # 生成結果（stamps_YYYYMMDD_HHMMSS/）
└── *.md                   # ドキュメント群
```

---

## セキュリティ注意事項

| 項目 | 実装 |
|------|------|
| ローカル専用 | `host='127.0.0.1'` でバインド |
| APIキー保護 | sessionStorage（タブ閉じで削除） |
| モデル制限 | `validate_model()` でバリデーション |
| ファイル検証 | 拡張子チェック、サイズ制限（50MB） |

**禁止事項:**
- クラウドサーバーへのデプロイ
- GitHubへのプッシュ（APIキー漏洩）
- APIキーのハードコーディング

---

## 関連ドキュメント

| ファイル | 用途 |
|---------|------|
| [README.md](README.md) | ユーザー向けクイックスタート |
| [PROMPTS.md](PROMPTS.md) | コピペ用プロンプト集 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | システム設計・API詳細 |
| [GEMINI_API_GUIDE.md](GEMINI_API_GUIDE.md) | Gemini API詳細 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | トラブルシューティング |

---

*Made by 丸投げちゃんシリーズ - Copyright (c) 2025 株式会社CLAN*

---

### フォーク時のお願い

改変・再配布する場合は、以下のクレジット表記を記載してください：

```
Original work: LINEスタンプ丸投げちゃん
Copyright (c) 2025 株式会社CLAN (https://clanbiz.net/)
```
