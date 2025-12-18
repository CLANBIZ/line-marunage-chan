# Gemini API ガイド

> Google AI Studio の Gemini API を使用するための技術ガイド

**バージョン**: 2.2.0
**最終更新**: 2025-12-15

---

## 使用モデル

```
============================================================
!! 重要: モデル使用ルール !!
============================================================
許可されたモデル:
  - テキスト生成: gemini-3-flash-preview
  - 画像生成: gemini-3-pro-image-preview

!! 絶対に使用禁止 !!
  - gemini-2.0-flash
  - gemini-2.5-flash
  - gemini-1.5-flash
  - gemini-1.5-pro
  - その他すべての gemini-2.x, gemini-1.x 系

バリデーション: core/gemini_client.py で実装済み
============================================================
```

---

## APIキーの取得

### 1. Google AI Studio にアクセス

https://aistudio.google.com/apikey

### 2. APIキーを作成

1. 「APIキーを作成」をクリック
2. プロジェクト名を入力（例: `line-stamp`）
3. 「プロジェクトを作成」をクリック

### 3. 請求設定（必須）

**重要**: 画像生成は有料です。

1. 「お支払い情報を設定」をクリック
2. Google Cloud の請求先アカウントをリンク
3. クレジットカードを登録

---

## 料金体系

### API料金（公式）

| 項目 | 料金 |
|------|------|
| テキスト入力 | $2.00 / 1M tokens |
| テキスト出力 | $12.00 / 1M tokens |
| 画像出力（1K/2K） | $0.134 / 枚 |
| 画像出力（4K） | $0.24 / 枚 |

### 1セットあたりの費用

| 処理 | 料金 |
|------|------|
| キャラ企画（5案） | 約1〜2円 |
| プロンプト生成 | 約1〜2円 |
| 画像生成（1枚） | 約20円 |
| 英語登録情報生成 | 約1円 |
| 画像リサイズ | 無料（ローカル処理） |
| **1セット合計** | **約23〜25円** |

※ $1 = ¥150 で計算

---

## SDK インストール

```bash
pip install google-genai
```

**注意**: 旧SDK `google-generativeai` ではなく、新SDK `google-genai` を使用

---

## コード例

### 認証

```python
from google import genai

client = genai.Client(api_key="YOUR_API_KEY")
```

### テキスト生成

```python
# gemini-3-flash-preview のみ使用
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=["LINEスタンプのキャラクターを5案提案して"]
)
print(response.text)
```

### 画像生成

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

# gemini-3-pro-image-preview のみ使用
response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=["cute blue cat, kawaii style, LINE sticker, white background"],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
    )
)

# 画像を取得
for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(part.inline_data.data))
        image.save("output.png")
```

---

## GeminiClient クラス

本プロジェクトでは `core/gemini_client.py` にラッパークラスがあります。

```python
from core.gemini_client import GeminiClient

client = GeminiClient(api_key="YOUR_API_KEY")

# キャラクター5案を提案（リクエスト付き）
characters, model_info = client.propose_characters("在宅ワークで疲れたOL")

# 英語プロンプトを生成
prompt, _ = client.create_grid_prompt(characters[0])

# 画像を生成
image, _ = client.generate_image(prompt)
image.save("grid.png")

# 英語登録情報を生成
en_info = client.generate_registration_info(characters[0])
```

### モデルバリデーション

```python
from core.gemini_client import validate_model, ALLOWED_TEXT_MODEL

# 許可モデルはOK
validate_model(ALLOWED_TEXT_MODEL)  # OK

# 禁止モデルはエラー
validate_model("gemini-2.0-flash")  # ValueError
```

---

## 制限事項

### レート制限

| 項目 | 制限 |
|------|------|
| リクエスト/分 | 60 |
| リクエスト/日 | 1,500（無料枠） |

### コンテンツフィルタ

以下は生成できません:
- 暴力的なコンテンツ
- 性的なコンテンツ
- 実在の人物

### 透過PNG非対応

gemini-3-pro-image-preview は透過PNG（アルファチャンネル）を出力できません。
白背景で生成し、手動で切り抜きしてください。

---

## トラブルシューティング

### 「APIキーが無効です」

1. Google AI Studio でAPIキーの状態を確認
2. 請求先アカウントがリンクされているか確認
3. APIキーをコピーし直す

### 「レート制限に達しました」

1. 少し待ってから再試行
2. 1日の制限に達した場合は翌日まで待つ

### 「画像を生成できません」

1. プロンプトが安全フィルタに引っかかっている可能性
2. プロンプトを修正して再試行
3. 人物を含まないプロンプトに変更

### 「ModuleNotFoundError: google.genai」

```bash
pip install google-genai
```

---

## 参考リンク

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API ドキュメント](https://ai.google.dev/gemini-api/docs)
- [画像生成ドキュメント](https://ai.google.dev/gemini-api/docs/image-generation)
- [料金ページ](https://ai.google.dev/pricing)
