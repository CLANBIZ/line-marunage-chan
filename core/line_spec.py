"""
LINE Creators Market スタンプ仕様

公式ガイドライン:
https://creator.line.me/ja/guideline/sticker/
"""

# スタンプ画像サイズ（最大）
STAMP_WIDTH = 370
STAMP_HEIGHT = 320

# メイン画像サイズ
MAIN_WIDTH = 240
MAIN_HEIGHT = 240

# タブ画像サイズ
TAB_WIDTH = 96
TAB_HEIGHT = 74

# 余白（透過部分）
PADDING = 10

# 最大コンテンツサイズ（余白を除いた部分）
MAX_CONTENT_WIDTH = STAMP_WIDTH - (PADDING * 2)
MAX_CONTENT_HEIGHT = STAMP_HEIGHT - (PADDING * 2)

# スタンプ枚数
MIN_STAMPS = 8
MAX_STAMPS = 40
COMMON_STAMPS = 16  # よく使われる枚数

# ファイル形式
FILE_FORMAT = "PNG"
COLOR_MODE = "RGBA"  # 透過必須

# ファイル名規則
def get_stamp_filename(index: int) -> str:
    """スタンプファイル名を取得（01.png〜）"""
    return f"{index:02d}.png"

MAIN_FILENAME = "main.png"
TAB_FILENAME = "tab.png"
