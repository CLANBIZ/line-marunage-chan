# アーキテクチャガイド

> **対象読者**: 開発者、コントリビューター、AIエージェント（技術詳細が必要な場合）

**バージョン**: 2.2.0
**最終更新**: 2025-12-15

---

## 設計思想

```
シンプル・高品質・セキュア

- Web UIでボタンを押すだけ
- Gemini 3 Pro のみ使用（低品質モデルは禁止）
- ローカル専用（127.0.0.1）でAPIキーを保護
```

---

## システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                        ユーザー                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Web UI (index.html + script.js)                            │
│  - STEP 1: APIキー入力                                       │
│  - STEP 2: リクエスト入力 → キャラ提案                        │
│  - STEP 3: 画像生成                                          │
│  - STEP 4: 切り抜き → ドロップ → リサイズ                     │
│  - STEP 5: 登録情報（日英）                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Flask Backend (server.py)                                  │
│  - /api/verify-connection    API接続確認                     │
│  - /api/propose-characters   キャラ提案（リクエスト対応）      │
│  - /api/generate-grid        グリッド画像生成                 │
│  - /api/resize-stamps        画像リサイズ                     │
│  - /api/download/<folder>    ZIPダウンロード                  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  GeminiClient    │ │  StampProcessor  │ │  line_spec.py    │
│  (API通信)        │ │  (画像処理)       │ │  (LINE仕様)       │
│                  │ │                  │ │                  │
│  - テキスト生成   │ │  - リサイズ       │ │  - 370x320px     │
│  - 画像生成       │ │  - main.png生成   │ │  - 240x240px     │
│  - モデル検証     │ │  - tab.png生成    │ │  - 96x74px       │
└──────────────────┘ └──────────────────┘ └──────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  Gemini API (Google AI Studio)                              │
│  - gemini-3-flash-preview (テキスト)                           │
│  - gemini-3-pro-image-preview (画像)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## プロジェクト構成

```
LINE/
├── server.py              # Flask バックエンド（メインエントリポイント）
├── index.html             # Web UI
├── static/
│   ├── css/style.css      # Glassmorphism デザイン
│   └── js/script.js       # フロントエンドロジック
├── core/
│   ├── __init__.py
│   ├── gemini_client.py   # Gemini API クライアント
│   ├── stamp_processor.py # 画像処理
│   └── line_spec.py       # LINE仕様定義
├── data/                  # ランタイムデータ（.gitignore）
│   ├── uploads/           # アップロード画像
│   └── output/            # 生成結果
│       └── stamps_YYYYMMDD_HHMMSS/
├── AI_GUIDE.md            # AIエージェント向けメインガイド
├── ARCHITECTURE.md        # このファイル
├── PROMPTS.md             # プロンプト集
├── GEMINI_API_GUIDE.md    # API詳細
├── TROUBLESHOOTING.md     # トラブルシューティング
└── requirements.txt       # 依存パッケージ
```

---

## コアモジュール詳細

### 1. GeminiClient (core/gemini_client.py)

**責務**: Gemini API との通信、モデルバリデーション

```python
# 許可モデル（定数）
ALLOWED_TEXT_MODEL = "gemini-3-flash-preview"
ALLOWED_IMAGE_MODEL = "gemini-3-pro-image-preview"

# 禁止パターン（バリデーション用）
FORBIDDEN_MODEL_PATTERNS = ["gemini-2", "gemini-1", "flash"]

class GeminiClient:
    def __init__(self, api_key: str)
        # モデルバリデーション実行（禁止モデルはValueError）

    def verify_connection(self) -> dict
        # API接続確認、モデル情報を返す

    def propose_characters(self, user_request: str = "") -> tuple[list, dict]
        # キャラクター5案を提案（リクエスト対応）

    def create_grid_prompt(self, character: dict) -> tuple[str, dict]
        # 6x3グリッド用の英語プロンプトを生成

    def generate_image(self, prompt: str) -> tuple[PIL.Image, dict]
        # 画像を生成

    def generate_registration_info(self, character: dict) -> dict
        # 英語タイトル・説明を生成
```

### 2. StampProcessor (core/stamp_processor.py)

**責務**: 画像のリサイズ、LINE仕様への変換

```python
class StampProcessor:
    def process_single_image(self, image, index, remove_bg=False) -> dict
        # 単一画像を370x320pxにリサイズ

    def process_batch(self, images, remove_bg=False) -> dict
        # 複数画像を一括処理

    def _generate_main_and_tab(self, base_image_path) -> tuple
        # main.png (240x240) と tab.png (96x74) を生成
```

### 3. line_spec.py

**責務**: LINE Creators Market の仕様定義

```python
STAMP_WIDTH = 370
STAMP_HEIGHT = 320
MAIN_WIDTH = 240
MAIN_HEIGHT = 240
TAB_WIDTH = 96
TAB_HEIGHT = 74
```

---

## API エンドポイント詳細

### POST /api/verify-connection

API接続を確認し、モデル情報を返す

**レスポンス:**
```json
{
  "success": true,
  "text_model": "gemini-3-flash-preview",
  "image_model": "gemini-3-pro-image-preview"
}
```

### POST /api/propose-characters

キャラクター5案を提案

**リクエスト:**
```json
{
  "request": "在宅ワークで疲れたOL"  // 任意
}
```

**レスポンス:**
```json
{
  "success": true,
  "characters": [
    {"name": "虚無OL", "concept": "...", "target": "20-30代女性"}
  ],
  "model_info": {"model_version": "..."}
}
```

### POST /api/generate-grid

6x3グリッド画像を生成

**リクエスト:**
```json
{
  "character": {"name": "虚無OL", "concept": "..."}
}
```

**レスポンス:**
```json
{
  "success": true,
  "image_url": "/output/grid_20251214_123456.png",
  "registration": {
    "title_ja": "虚無OL",
    "title_en": "Nihilistic Office Lady",
    "description_ja": "...",
    "description_en": "..."
  }
}
```

### POST /api/resize-stamps

画像をLINE仕様にリサイズ

**リクエスト:** `multipart/form-data` で `files` フィールドに画像

**レスポンス:**
```json
{
  "success": true,
  "folder": "stamps_20251214_123456",
  "processed_count": 16,
  "download_url": "/api/download/stamps_20251214_123456"
}
```

### GET /api/download/<folder>

出力フォルダをZIPでダウンロード

---

## セキュリティ設計

| 項目 | 実装 |
|------|------|
| ローカル専用 | `host='127.0.0.1'` でバインド |
| APIキー保護 | sessionStorage（タブ閉じで削除） |
| モデル制限 | `validate_model()` でバリデーション |
| ファイル検証 | 拡張子チェック、サイズ制限（50MB） |
| CORS | localhost/127.0.0.1 のみ許可 |

**禁止事項:**
- クラウドサーバーへのデプロイ
- GitHubへのプッシュ（APIキー漏洩）
- APIキーのハードコーディング

---

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | Vanilla JS, CSS (Glassmorphism) |
| バックエンド | Python 3.10+, Flask 3.0+ |
| AI API | Gemini 3 Pro (google-genai SDK) |
| 画像処理 | Pillow 10.0+ |

### 依存パッケージ (requirements.txt)

```
flask>=3.0.0
flask-cors>=4.0.0
google-genai>=1.0.0
Pillow>=10.0.0
python-dotenv>=1.0.0
```

---

## 拡張ガイド

### 新しいAPIエンドポイントを追加

```python
# server.py
@app.route('/api/new-feature', methods=['POST'])
def api_new_feature():
    data = request.get_json()
    # 処理
    return jsonify({'success': True, 'data': result})
```

### GeminiClientにメソッドを追加

```python
# core/gemini_client.py
def new_method(self, param: str) -> dict:
    response = self.client.models.generate_content(
        model=self.text_model,
        contents=[prompt]
    )
    return response.text
```

---

## 関連ドキュメント

| ファイル | 用途 |
|---------|------|
| [AI_GUIDE.md](AI_GUIDE.md) | AIエージェント向けメインガイド |
| [GEMINI_API_GUIDE.md](GEMINI_API_GUIDE.md) | Gemini API詳細 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 問題解決ガイド |
