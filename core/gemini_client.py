"""
Gemini API クライアント（画像生成）

Google AI Studio で取得したAPIキーを使用して、
Gemini API で LINE スタンプ用画像を生成します。

============================================================
!! 重要: モデル使用ルール !!
============================================================
このプロジェクトでは以下のモデルのみ使用を許可します:

  - テキスト生成: gemini-3-flash-preview
  - 画像生成: gemini-3-pro-image-preview

!! gemini-2.x 系は使用禁止（許可リストで制御）!!
============================================================
"""

from google import genai
from google.genai import types
from pathlib import Path
import json
import io

# 生成済みキャラクター保存ファイル（直近100件）
GENERATED_CHARACTERS_FILE = Path(__file__).parent.parent / "data" / "generated_characters.json"
MAX_GENERATED_HISTORY = 100


def load_generated_characters() -> list[str]:
    """生成済みキャラクター名のリストを読み込む"""
    try:
        if GENERATED_CHARACTERS_FILE.exists():
            with open(GENERATED_CHARACTERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('characters', [])
    except:
        pass
    return []


def save_generated_characters(characters: list[str]) -> None:
    """生成済みキャラクター名を保存（直近100件）"""
    try:
        GENERATED_CHARACTERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        # 直近100件に制限
        recent = characters[-MAX_GENERATED_HISTORY:]
        with open(GENERATED_CHARACTERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'characters': recent}, f, ensure_ascii=False, indent=2)
    except:
        pass


def add_generated_characters(new_names: list[str]) -> None:
    """新しいキャラクター名を追加"""
    existing = load_generated_characters()
    existing.extend(new_names)
    save_generated_characters(existing)


# ============================================================
# !! 許可されたモデル定数 !!
# !! これ以外のモデルは絶対に使用しないこと !!
# ============================================================
ALLOWED_TEXT_MODEL = "gemini-3-flash-preview"
ALLOWED_IMAGE_MODEL = "gemini-3-pro-image-preview"


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
    # 許可リストチェック（許可リストにあればOK）
    if model_name in [ALLOWED_TEXT_MODEL, ALLOWED_IMAGE_MODEL]:
        return  # 許可モデルなのでチェック完了

    # 許可リストにない場合はエラー
    raise ValueError(
        f"許可されていないモデルです: {model_name}\n"
        f"許可モデル: {ALLOWED_TEXT_MODEL}, {ALLOWED_IMAGE_MODEL}"
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

        # 生成済みキャラクター除外リスト（直近100件）
        existing_characters = load_generated_characters()
        if existing_characters:
            exclude_section = f"""
【除外リスト】以下のキャラクターは既に生成済みです。これらとは全く異なる新しいアイデアを出してください:
{', '.join(existing_characters)}
"""
        else:
            exclude_section = ""

        prompt = f"""
あなたはLINEスタンプのマーケティング専門家です。
現在、クリエイターズマーケットで人気が出そうな
少しニッチでシュールなキャラクターのアイデアを5つ提案してください。
{request_section}{exclude_section}
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
            characters = _extract_json(response.text)
            # 生成したキャラクター名を保存
            new_names = [c.get('name', '') for c in characters if c.get('name')]
            if new_names:
                add_generated_characters(new_names)
            return characters, model_info
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
6. 上部タイトルは「日本語」で表示（英語禁止）

以下の形式で英語プロンプトのみ出力（説明不要）:

Create a character sheet for LINE stickers with 18 variations (6 columns x 3 rows).
Aspect Ratio: Wide (16:9)
Add a Title Text at the top in JAPANESE: "{char_name}"

Character Settings:
Name: {char_name} (display in Japanese)
Visual: [キャラの見た目を英語で]
Style: Kawaii, Simple flat illustration, Soft colors
Background: White
Text Style: Black text with white outline, Japanese text
Title: Must be in Japanese, not English

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
        キャラクター情報から日英のタイトルと説明文を生成

        ※ 文字数制限はGeminiに指示しない（クオリティ優先）
        ※ ユーザーがLINE登録時に自分で調整する

        Args:
            character: {name, concept, target}

        Returns:
            {title_ja, description_ja, title_en, description_en}
        """
        char_name = character.get('name', '')
        concept = character.get('concept', '')
        target = character.get('target', '')

        prompt = f"""
以下のLINEスタンプキャラクター情報から、日本語と英語の登録情報を作成してください。

キャラクター名（日本語）: {char_name}
コンセプト: {concept}
ターゲット: {target}

【条件】
- 魅力的でキャッチーなタイトルと説明文を作成
- 購入意欲を高める説明文にする
- 「○月○日発売」「○○と検索」等の告知文言はNG

【出力形式】JSON形式で出力（説明不要）:
{{
    "title_ja": "日本語タイトル",
    "description_ja": "日本語説明文",
    "title_en": "English Title",
    "description_en": "English description"
}}
"""

        response = self.client.models.generate_content(
            model=self.text_model,
            contents=[prompt]
        )

        try:
            return _extract_json(response.text)
        except:
            # フォールバック: シンプルな日英変換
            return {
                'title_ja': char_name[:20],  # 全角20文字以内
                'description_ja': concept[:80],  # 全角80文字以内
                'title_en': char_name[:40],
                'description_en': concept[:160]
            }
