<div align="center">

# LINEスタンプ丸投げちゃん

**Gemini 3 Pro で LINEスタンプを量産するローカル専用ツール**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Gemini API](https://img.shields.io/badge/Gemini_3_Pro-API連携-4285F4.svg)](https://ai.google.dev/)
[![Claude Code](https://img.shields.io/badge/Claude_Code-推奨-FF6B35.svg)](https://claude.ai/)

---

</div>

## 🚨 AIエージェント向け必読事項

> **Claude Code や他のAIエージェントがこのプロジェクトを扱う場合、必ずこのセクションを読むこと**

### 許可されたモデル（これ以外は使用禁止）

| 用途 | モデル名 |
|------|---------|
| テキスト生成 | `gemini-3-flash-preview` |
| 画像生成 | `gemini-3-pro-image-preview` |

### ❌ 禁止モデル（絶対に使うな）

```
gemini-2.0-flash-exp   ← 使用禁止
gemini-2.0-flash       ← 使用禁止
gemini-2.5-flash       ← 使用禁止
gemini-1.x 系          ← 使用禁止
"flash" を含む全て     ← 使用禁止
```

### ❌ やってはいけないこと

```python
# ダメな例：自分でプロンプトを書いて直接画像生成
prompt = "cute cat LINE sticker..."
client.models.generate_content(model='gemini-2.0-flash-exp', ...)
```

### ✅ 正しいワークフロー

```python
# Step 1: gemini-3-flash-preview でキャラクター提案
# Step 2: gemini-3-flash-preview で英語プロンプト生成
# Step 3: gemini-3-pro-image-preview で画像生成
```

詳細は `core/gemini_client.py` と `AI_GUIDE.md` を参照。

---

## これは何？

ボタンを押すだけで、AIがLINEスタンプ用の画像を自動生成してくれるツールです。

**できること：**
- AIがキャラクターを5案提案
- 選んだキャラでスタンプ画像を自動生成
- LINE規格（370x320px）に自動リサイズ
- ZIPでまとめてダウンロード

---

## 必要なもの

| 必要なもの | 入手方法 |
|-----------|---------|
| **Python 3.10以上** | https://www.python.org/downloads/ からダウンロード |
| **Gemini APIキー** | 下の「APIキーの取得方法」を参照 |
| **Claude Code**（推奨） | https://claude.ai/download |

---

## クイックスタート（3ステップ）

### Step 1: Claude Codeで以下をコピペ

```
cd ~/Desktop/line-marunage-chan && pip install -r requirements.txt && python server.py
```

> **Claude Codeがない場合：** ターミナル（Mac）またはコマンドプロンプト（Windows）で上記を実行

### Step 2: ブラウザで開く

```
http://localhost:5000
```

### Step 3: APIキーを入力してスタンプ作成

1. 画面の「APIキー」欄にGemini APIキーを貼り付け
2. 「確認」ボタンを押す
3. 「キャラクターを提案してもらう」ボタンを押す
4. 気に入ったキャラを選んで「画像を生成する」

---

## APIキーの取得方法（図解）

### 手順1: Google AI Studioにアクセス

```
https://aistudio.google.com/apikey
```

### 手順2: Googleアカウントでログイン

### 手順3: 「APIキーを作成」をクリック

### 手順4: 表示されたキーをコピー

キーは `AIzaSy...` で始まる文字列です。

### 手順5: 【重要】課金設定を有効化

画像生成には課金設定が必要です：

1. https://console.cloud.google.com/billing にアクセス
2. 請求先アカウントを作成またはリンク
3. クレジットカードを登録

> **注意：** 無料枠では画像生成できません。1画像あたり約2〜5円程度かかります。

---

## 使い方（詳細）

### スタンプ作成の流れ

```
Step 1: APIキー入力
    ↓
Step 2: キャラクター提案（5案）
    ↓
Step 3: キャラ選択 → 画像生成
    ↓
Step 4: 生成された画像をスクショで切り抜き
    ↓
Step 5: 切り抜き画像をドロップ → 自動リサイズ
    ↓
Step 6: ZIPダウンロード
    ↓
Step 7: LINE Creators Marketに登録
```

### LINE Creators Marketへの登録

1. https://creator.line.me/ にアクセス
2. LINEアカウントでログイン
3. 「スタンプを作る」を選択
4. ZIPを解凍した画像をアップロード
5. タイトル・説明文を入力（ツールが英語版も生成します）

---

## トラブルシューティング

### 「APIキーが無効です」と表示される

**原因：** APIキーが間違っているか、課金設定がされていない

**解決策：**
1. APIキーをもう一度コピーし直す
2. https://console.cloud.google.com/billing で課金設定を確認

### 「画像生成に失敗しました」と表示される

**原因：** APIの利用制限に達した

**解決策：**
1. 数分待ってから再試行
2. Google Cloud Consoleで利用状況を確認

### サーバーが起動しない

**原因：** Pythonがインストールされていないか、パスが通っていない

**解決策：**
```bash
# Pythonのバージョン確認
python --version

# 3.10以上でない場合はPythonを再インストール
```

### ポート5000が使用中

**解決策：**
```bash
# 別のポートで起動
python server.py --port 5001
```

---

## ファイル構成

```
line-marunage-chan/
├── server.py           # メインサーバー（これを実行）
├── index.html          # Web UI
├── requirements.txt    # 必要なライブラリ一覧
├── core/
│   ├── gemini_client.py    # Gemini API連携
│   └── stamp_processor.py  # 画像処理
├── static/             # CSS/JavaScript
└── data/
    ├── uploads/        # アップロード画像
    └── output/         # 生成された画像
```

---

## よくある質問

### Q: 無料で使えますか？

A: ツール自体は無料ですが、Gemini APIの利用料金（1画像2〜5円程度）がかかります。

### Q: 生成した画像の著作権は？

A: AI生成画像の著作権は利用者に帰属します。ただし、LINE Creators Marketのガイドラインを必ず確認してください。

### Q: 1日何枚まで生成できますか？

A: Gemini APIの利用制限内であれば無制限です。詳細はGoogle Cloud Consoleで確認できます。

---

## ライセンス

MIT License - Copyright (c) 2025 株式会社CLAN

### 免責事項

- このソフトウェアは「現状のまま」提供されます
- 生成画像の著作権・商標権に関する最終判断はユーザー自身の責任です
- LINE Creators Marketのガイドラインを必ず確認してください
