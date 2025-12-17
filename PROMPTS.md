# プロンプト集

> AIエージェント（Claude Code等）にコピペして使えるプロンプト集

**バージョン**: 2.2.0
**最終更新**: 2025-12-15

---

## 内部使用プロンプト

以下はシステム内部（`core/gemini_client.py`）で使用されているプロンプトです。

### キャラクター提案プロンプト

```
あなたはLINEスタンプのマーケティング専門家です。
現在、クリエイターズマーケットで人気が出そうな
少しニッチでシュールなキャラクターのアイデアを5つ提案してください。

【ユーザーからのリクエスト】  ← リクエストがある場合のみ追加
「{user_request}」
このリクエストを元に、LINEスタンプとして売れそうなキャラクターを5つ提案してください。

【条件】
1. 「ただ可愛い動物」はNG（レッドオーシャンなので）。
2. 「動物 × 職業」や「動物 × 現代の悩み」など、ギャップや共感性のある設定にすること。
3. ターゲット層（誰がいつ使うか）も明確にすること。

JSON配列で出力（日本語で）:
[
  {"name": "キャラ名", "concept": "コンセプトとターゲット説明", "target": "ターゲット層"},
  ...
]
```

### 6x3グリッド英語プロンプト生成

```
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
...
```

### 英語登録情報生成プロンプト

```
以下のLINEスタンプキャラクター情報を英語に翻訳してください。

キャラクター名（日本語）: {char_name}
コンセプト: {concept}
ターゲット: {target}

【出力形式】JSON形式で出力（説明不要）:
{
    "title_en": "英語タイトル（40文字以内、キャッチーに）",
    "description_en": "英語説明文（160文字以内、購入意欲を高める説明）"
}
```

---

## 実績プロンプト例

### キーボード・クラッシャー猫（18枚版）

```
Create a character sheet for LINE stickers with 18 variations (6 columns x 3 rows).
Aspect Ratio: Wide (16:9) --ar 16:9
Concept: "Keyboard Crasher Cat" (A cat interfering with PC work and typing gibberish).

Character Settings:
Name: Keyboard Cat
Visual: A cat sitting, sleeping, or walking on a Laptop/Keyboard.
Style: Modern Flat Vector Art. Digital & Pop.
Text Style: Monospace font (Console style), Green or Black text.

Layout:
Grid: 6 columns x 3 rows (Total 18 panels).
Text: Japanese text and "Gibberish" strings (e.g., "nnnnuuu").

Panels Detail (18 Variations):

Row 1 (Gibberish & Typing)
1. Visual: Cat sliding across keys. / Text: nnnnnnuuu...
2. Visual: Face-planting (sleeping) on keys. / Text: ddddddd;;;;;
3. Visual: Stepping with paw. / Text: ＠「：ｌｐ；
4. Visual: Sitting on "Delete" key. / Text: データ消失
5. Visual: Cat typing furiously (Hacker). / Text: カタカタ
6. Visual: Hitting "Enter" hard. / Text: ッターン！

Row 2 (Interference)
7. Visual: Sitting in front of monitor (Blocking). / Text: 邪魔
8. Visual: Biting the screen corner. / Text: 破壊
9. Visual: Catching mouse cursor. / Text: 作業妨害
10. Visual: Sleeping on power adapter (Warm). / Text: 暖
11. Visual: Tangled in mouse cord. / Text: 詰んだ
12. Visual: Pulling the power plug. / Text: 強制終了

Row 3 (Emotions & System)
13. Visual: "Typing..." chat bubble dots. / Text: 入力中...
14. Visual: Pressing Ctrl+Z. / Text: なかったことに
15. Visual: Closing the laptop lid. / Text: 閉店
16. Visual: 404 Error on cat's face. / Text: エラー
17. Visual: Staring with dead eyes (Blue light). / Text: …
18. Visual: Sending a weird stamp/gibberish. / Text: 誤送信
```

---

## ユーザー向けプロンプト

### サーバー起動

```
LINEスタンプ丸投げちゃんを起動して。

pip install -r requirements.txt
python server.py

ブラウザで http://localhost:5000 を開いて。
```

### 登録情報の一括生成

```
完成したスタンプセットを見て、LINE Creators Market 登録用の情報を作って:
- タイトル（日本語/英語）
- 説明文（日本語/英語）
- コピーライト
- 推奨カテゴリ
- 推奨タグ
```

### タイトル案を複数提案

```
「{キャラ名}」スタンプのタイトルを5案考えて。
キャッチーで検索されやすいものを。日本語と英語それぞれ。
```

### 説明文のリライト

```
この説明文を160文字以内でもっと魅力的にリライトして:
「{現在の説明文}」
```

---

## トラブルシューティング用

### 生成エラーの診断

```
画像生成でエラーが出た。以下のログを見て原因を特定して:
[エラーログをペースト]
```

### APIキーエラーの対処

```
「APIキーが無効です」エラーが出る。
Google AI Studio でAPIキーの状態を確認する方法を教えて。
```

---

## 関連ドキュメント

| ファイル | 用途 |
|---------|------|
| [AI_GUIDE.md](AI_GUIDE.md) | AIエージェント向けメインガイド |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | トラブルシューティング |
