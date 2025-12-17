"""
Gemini API クライアント（画像生成）

Google AI Studio で取得したAPIキーを使用して、
Gemini 3 Pro で LINE スタンプ用画像を生成します。

============================================================
!! 重要: モデル使用ルール !!
============================================================
このプロジェクトでは以下のモデルのみ使用を許可します:

  - テキスト生成: gemini-3-pro
  - 画像生成: gemini-3-pro-image

!! gemini-2.x 系は絶対に使用禁止 !!
!! gemini-2.0-flash 等の低品質モデルは使用禁止 !!

理由: ユーザーは高品質のみを求めています
============================================================
"""

from google import genai
from google.genai import types
import base64
from pathlib import Path
from typing import Optional
import json
import io


# ============================================================
# !! 許可されたモデル定数 !!
# !! これ以外のモデルは絶対に使用しないこと !!
# ============================================================
ALLOWED_TEXT_MODEL = "gemini-3-pro-preview"
ALLOWED_IMAGE_MODEL = "gemini-3-pro-image-preview"

# 禁止モデルパターン（これらを含むモデル名は拒否）
FORBIDDEN_MODEL_PATTERNS = [
    "gemini-2",
    "gemini-1",
    "flash",
]


def _extract_json(text: str):
    """
    APIレスポンスからJSONを抽出

    Args:
        text: APIレスポンステキスト

    Returns:
        パースされたJSONオブジェクト

    Raises:
        ValueError: JSON抽出に失敗した場合
    """
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return json.loads(text.strip())


def validate_model(model_name: str) -> None:
    """
    モデル名が許可されているか検証

    Args:
        model_name: 検証するモデル名

    Raises:
        ValueError: 禁止モデルが指定された場合
    """
    # 許可リストチェック
    if model_name not in [ALLOWED_TEXT_MODEL, ALLOWED_IMAGE_MODEL]:
        raise ValueError(
            f"許可されていないモデルです: {model_name}\n"
            f"許可モデル: {ALLOWED_TEXT_MODEL}, {ALLOWED_IMAGE_MODEL}"
        )

    # 禁止パターンチェック（二重チェック）
    model_lower = model_name.lower()
    for pattern in FORBIDDEN_MODEL_PATTERNS:
        if pattern in model_lower:
            raise ValueError(
                f"禁止されたモデルパターンが検出されました: {model_name}\n"
                f"パターン '{pattern}' は使用禁止です"
            )


class GeminiClient:
    """
    Gemini API を使った画像生成クライアント

    !! 重要 !!
    - テキスト生成: gemini-3-pro のみ使用
    - 画像生成: gemini-3-pro-image のみ使用
    - gemini-2.x 系は絶対に使用禁止
    """

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Google AI Studio で取得した API キー
        """
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

        # ============================================================
        # !! モデル設定 - 変更禁止 !!
        # ============================================================
        # 画像生成用モデル（Gemini 3 Pro Image）
        # !! gemini-2.x は絶対に使わない !!
        self.image_model = ALLOWED_IMAGE_MODEL

        # テキスト生成用モデル（Gemini 3 Pro）
        # !! gemini-2.0-flash 等は絶対に使わない !!
        self.text_model = ALLOWED_TEXT_MODEL

        # ============================================================
        # !! モデルバリデーション !!
        # 禁止モデルが設定されていないかチェック
        # ============================================================
        validate_model(self.text_model)
        validate_model(self.image_model)

    def verify_connection(self) -> dict:
        """
        API接続を確認し、実際に使用されるモデル情報を返す

        Returns:
            {
                'connected': bool,
                'text_model': str,  # 実際に使用されるテキストモデル
                'image_model': str,  # 実際に使用される画像モデル
                'text_model_version': str,  # APIから返されたバージョン
            }
        """
        try:
            # テキストモデルの確認（簡単なテスト）
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=["test"]
            )

            # レスポンスからモデル情報を取得
            text_model_version = getattr(response, 'model_version', self.text_model)

            return {
                'connected': True,
                'text_model': self.text_model,
                'image_model': self.image_model,
                'text_model_version': str(text_model_version),
                'requested_text_model': ALLOWED_TEXT_MODEL,
                'requested_image_model': ALLOWED_IMAGE_MODEL,
            }

        except Exception as e:
            return {
                'connected': False,
                'text_model': self.text_model,
                'image_model': self.image_model,
                'error': str(e)
            }

    def generate_stamp_image(
        self,
        prompt: str,
        style: str = "kawaii",
        negative_prompt: Optional[str] = None
    ):
        """
        LINEスタンプ用の画像を生成（Gemini 3 Pro Image Preview）

        Args:
            prompt: 画像生成プロンプト（日本語OK）
            style: スタイル（kawaii, simple, pop, etc.）
            negative_prompt: 除外したい要素

        Returns:
            生成された画像（PIL Image）
        """
        # LINEスタンプ向けの共通プロンプト
        stamp_prompt = self._build_stamp_prompt(prompt, style)

        try:
            # Gemini 3 Pro Image Preview で画像生成
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=[stamp_prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                )
            )

            # レスポンスから画像を取得
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    # PIL Image として返す
                    from PIL import Image
                    image_bytes = part.inline_data.data
                    return Image.open(io.BytesIO(image_bytes))

            raise Exception("画像の生成に失敗しました")

        except Exception as e:
            raise Exception(f"Gemini API エラー: {str(e)}")

    def generate_stamp_set(
        self,
        theme: str,
        character_description: str,
        emotions: list[str],
        style: str = "kawaii"
    ) -> list[dict]:
        """
        LINEスタンプセット（16枚）を一括生成

        Args:
            theme: テーマ（例: "溶ける猫", "中世の猫"）
            character_description: キャラクター説明
            emotions: 表情/感情リスト（16個推奨）
            style: スタイル

        Returns:
            生成結果のリスト [{index, emotion, image_data}, ...]
        """
        results = []

        for i, emotion in enumerate(emotions[:16], start=1):
            prompt = f"{character_description}, {emotion}, {theme}"

            try:
                image = self.generate_stamp_image(prompt, style)
                results.append({
                    "index": i,
                    "emotion": emotion,
                    "image": image,
                    "success": True
                })
            except Exception as e:
                results.append({
                    "index": i,
                    "emotion": emotion,
                    "error": str(e),
                    "success": False
                })

        return results

    def analyze_image_for_stamp(self, image_path: str) -> dict:
        """
        既存の画像を解析してスタンプ情報を提案

        Args:
            image_path: 画像ファイルパス

        Returns:
            {title, description, emotions, tags}
        """
        image_data = Path(image_path).read_bytes()

        prompt = """
この画像をLINEスタンプとして分析してください。以下をJSON形式で出力:
{
    "title_ja": "日本語タイトル（40文字以内）",
    "title_en": "English Title (40 chars max)",
    "description_ja": "日本語説明文（160文字以内）",
    "description_en": "English description (160 chars max)",
    "emotion": "この画像が表す感情/シチュエーション",
    "tags": ["タグ1", "タグ2", "タグ3"],
    "suggested_text": "スタンプに入れるテキスト案"
}
"""

        response = self.client.models.generate_content(
            model=self.text_model,
            contents=[
                types.Content(
                    parts=[
                        types.Part(text=prompt),
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/png",
                                data=image_data
                            )
                        )
                    ]
                )
            ]
        )

        # JSONを抽出
        try:
            return _extract_json(response.text)
        except:
            return {"raw_response": response.text}

    def suggest_stamp_prompts(self, theme: str, count: int = 16) -> list[str]:
        """
        テーマからスタンプ用プロンプトを提案

        Args:
            theme: テーマ（例: "怠惰な猫", "元気な犬"）
            count: 生成するプロンプト数

        Returns:
            プロンプトのリスト
        """
        prompt = f"""
「{theme}」をテーマにしたLINEスタンプ{count}枚分のプロンプトを考えてください。

要件:
- 日常会話で使いやすい感情・シチュエーション
- バリエーション豊か（喜怒哀楽 + 挨拶 + リアクション）
- 各プロンプトは英語で、画像生成AI向けに具体的に

JSON配列で出力:
["prompt1", "prompt2", ...]
"""

        response = self.client.models.generate_content(
            model=self.text_model,
            contents=[prompt]
        )
        try:
            return _extract_json(response.text)
        except:
            return [f"{theme} - emotion {i}" for i in range(1, count + 1)]

    def _build_stamp_prompt(self, user_prompt: str, style: str) -> str:
        """LINEスタンプ向けのプロンプトを構築"""

        style_modifiers = {
            "kawaii": "cute, kawaii, adorable, soft colors, round shapes",
            "simple": "simple, minimal, clean lines, flat design",
            "pop": "colorful, vibrant, energetic, bold outlines",
            "retro": "vintage, nostalgic, warm colors, classic style",
            "watercolor": "watercolor style, soft edges, artistic, pastel",
        }

        modifier = style_modifiers.get(style, style_modifiers["kawaii"])

        return f"""
{user_prompt},
{modifier},
LINE sticker style,
transparent background,
centered composition,
expressive character,
high quality,
no text unless specified
""".strip()

    def propose_characters(self, user_request: str = "") -> tuple[list[dict], dict]:
        """
        売れそうなLINEスタンプキャラクターを5案提案

        Args:
            user_request: ユーザーからのリクエスト（例: "丸投げちゃんを題材にした猫"）

        Returns:
            (characters, model_info)
            - characters: [{name, concept, target}, ...]
            - model_info: {'model_version': str, 'requested_model': str}
        """
        # リクエストがある場合はプロンプトに組み込む
        if user_request and user_request.strip():
            request_section = f"""
【ユーザーからのリクエスト】
「{user_request.strip()}」
このリクエストを元に、LINEスタンプとして売れそうなキャラクターを5つ提案してください。
リクエストの意図を汲み取り、より具体的で魅力的なキャラクターに発展させてください。
"""
        else:
            request_section = ""

        prompt = f"""
あなたはLINEスタンプのマーケティング専門家です。
現在、クリエイターズマーケットで人気が出そうな
少しニッチでシュールなキャラクターのアイデアを5つ提案してください。
{request_section}
【条件】
1. 「ただ可愛い動物」はNG（レッドオーシャンなので）。
2. 「動物 × 職業」や「動物 × 現代の悩み」など、ギャップや共感性のある設定にすること。
3. ターゲット層（誰がいつ使うか）も明確にすること。

JSON配列で出力（日本語で）:
[
  {{"name": "キャラ名", "concept": "コンセプトとターゲット説明", "target": "ターゲット層"}},
  ...
]
"""

        response = self.client.models.generate_content(
            model=self.text_model,
            contents=[prompt]
        )

        # モデル情報を取得
        model_info = {
            'model_version': getattr(response, 'model_version', 'unknown'),
            'requested_model': self.text_model
        }

        try:
            return _extract_json(response.text), model_info
        except:
            # フォールバック
            return [
                {"name": "会議で寝落ちするカエル", "concept": "リモートワークあるある。会議中に眠くなる社会人向け", "target": "20-30代会社員"},
                {"name": "締め切りに追われるハムスター", "concept": "いつも何かに追われている現代人向け", "target": "学生・社会人"},
                {"name": "副業に疲れたペンギン", "concept": "本業と副業の両立に疲れた人向け", "target": "副業ワーカー"},
                {"name": "推し活に全力なウサギ", "concept": "推しへの愛が止まらないオタク向け", "target": "推し活層"},
                {"name": "節約に目覚めたタヌキ", "concept": "物価高で節約を始めた人向け", "target": "主婦・一人暮らし"}
            ], model_info

    def create_grid_prompt(self, character: dict) -> tuple[str, dict]:
        """
        キャラクター情報から6x3グリッド画像生成用の英語プロンプトを作成

        Args:
            character: {name, concept, target}

        Returns:
            (prompt, model_info)
            - prompt: 英語プロンプト文字列
            - model_info: {'model_version': str, 'requested_model': str}
        """
        char_name = character.get('name', 'Character')
        concept = character.get('concept', '')

        # まず日本語から英語プロンプトを生成
        translate_prompt = f"""
以下のキャラクターでLINEスタンプ18枚分の画像生成プロンプトを英語で作成してください。

キャラクター名: {char_name}
コンセプト: {concept}

【厳守ルール】
1. 構成：横6列 × 縦3行（Total 18 panels）のグリッド画像
2. アスペクト比：Wide (16:9)
3. 背景は「白 (White Background)」
4. 文字は「日本語」でスタンプ内に入れる
5. スタイル: Kawaii, Simple flat illustration

以下の形式で英語プロンプトのみ出力（説明不要）:

Create a character sheet for LINE stickers with 18 variations (6 columns x 3 rows).
Aspect Ratio: Wide (16:9)
Add a Title Text at the top: "[キャラ名英語]"

Character Settings:
Name: [英語名]
Visual: [キャラの見た目を英語で]
Style: Kawaii, Simple flat illustration, Soft colors
Background: White
Text Style: Black text with white outline, Japanese text

Panels Detail (18 Variations):
Row 1: 1. [セリフ] 2. [セリフ] ... 6. [セリフ]
Row 2: 7. [セリフ] ... 12. [セリフ]
Row 3: 13. [セリフ] ... 18. [セリフ]
"""

        response = self.client.models.generate_content(
            model=self.text_model,
            contents=[translate_prompt]
        )

        # モデル情報を取得
        model_info = {
            'model_version': getattr(response, 'model_version', 'unknown'),
            'requested_model': self.text_model
        }

        return response.text.strip(), model_info

    def generate_image(self, prompt: str) -> tuple:
        """
        プロンプトから画像を生成（6x3グリッド）

        Args:
            prompt: 英語プロンプト

        Returns:
            (PIL Image, model_info)
            - image: PIL Image
            - model_info: {'model_version': str, 'requested_model': str}
        """
        try:
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                )
            )

            # モデル情報を取得
            model_info = {
                'model_version': getattr(response, 'model_version', 'unknown'),
                'requested_model': self.image_model
            }

            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    from PIL import Image
                    image_bytes = part.inline_data.data
                    return Image.open(io.BytesIO(image_bytes)), model_info

            raise Exception("画像の生成に失敗しました")

        except Exception as e:
            raise Exception(f"Gemini API エラー: {str(e)}")

    def generate_registration_info(self, character: dict) -> dict:
        """
        キャラクター情報から英語のタイトルと説明文を生成

        Args:
            character: {name, concept, target}

        Returns:
            {title_en, description_en}
        """
        char_name = character.get('name', '')
        concept = character.get('concept', '')
        target = character.get('target', '')

        prompt = f"""
以下のLINEスタンプキャラクター情報を英語に翻訳してください。

キャラクター名（日本語）: {char_name}
コンセプト: {concept}
ターゲット: {target}

【出力形式】JSON形式で出力（説明不要）:
{{
    "title_en": "英語タイトル（40文字以内、キャッチーに）",
    "description_en": "英語説明文（160文字以内、購入意欲を高める説明）"
}}
"""

        response = self.client.models.generate_content(
            model=self.text_model,
            contents=[prompt]
        )

        try:
            return _extract_json(response.text)
        except:
            # フォールバック: シンプルな英語変換
            return {
                'title_en': char_name,
                'description_en': concept
            }


# 使用例
if __name__ == "__main__":
    # テスト用
    import os

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("環境変数 GEMINI_API_KEY を設定してください")
        exit(1)

    client = GeminiClient(api_key)

    # プロンプト提案テスト
    prompts = client.suggest_stamp_prompts("溶ける青い猫", count=8)
    print("提案されたプロンプト:")
    for i, p in enumerate(prompts, 1):
        print(f"  {i}. {p}")
