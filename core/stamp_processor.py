"""
LINE スタンプ画像処理モジュール

画像のリサイズ、背景削除、LINE仕様への変換を行います。
"""

import os
from pathlib import Path
from PIL import Image
from typing import Optional, Union
import io

from .line_spec import (
    STAMP_WIDTH, STAMP_HEIGHT,
    MAIN_WIDTH, MAIN_HEIGHT,
    TAB_WIDTH, TAB_HEIGHT,
    PADDING, MAX_CONTENT_WIDTH, MAX_CONTENT_HEIGHT,
    COLOR_MODE, FILE_FORMAT,
    get_stamp_filename, MAIN_FILENAME, TAB_FILENAME
)

# 背景削除（オプション）
try:
    from rembg import remove as remove_background
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False


class StampProcessor:
    """LINE スタンプ画像処理クラス"""

    def __init__(self, output_dir: str = "data/output"):
        """
        Args:
            output_dir: 出力先ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_single_image(
        self,
        image: Union[Image.Image, bytes, str],
        index: int,
        remove_bg: bool = False
    ) -> dict:
        """
        単一画像をLINEスタンプ仕様に変換

        Args:
            image: PIL Image, バイトデータ, またはファイルパス
            index: スタンプ番号（1〜）
            remove_bg: 背景を削除するか

        Returns:
            {success, filename, path, size, error}
        """
        try:
            # 画像を読み込み
            pil_image = self._load_image(image)

            # 背景削除（オプション）
            if remove_bg and REMBG_AVAILABLE:
                pil_image = self._remove_background(pil_image)

            # LINE仕様にリサイズ
            processed = self._resize_to_stamp_spec(pil_image)

            # 保存
            filename = get_stamp_filename(index)
            save_path = self.output_dir / filename
            processed.save(save_path, FILE_FORMAT)

            return {
                "success": True,
                "filename": filename,
                "path": str(save_path),
                "size": processed.size
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "index": index
            }

    def process_batch(
        self,
        images: list,
        remove_bg: bool = False,
        progress_callback=None
    ) -> dict:
        """
        複数画像を一括処理

        Args:
            images: 画像リスト
            remove_bg: 背景削除するか
            progress_callback: 進捗コールバック fn(current, total, status)

        Returns:
            {success_count, failed_count, results, main_path, tab_path}
        """
        results = []
        success_count = 0
        failed_count = 0

        for i, img in enumerate(images, start=1):
            if progress_callback:
                progress_callback(i, len(images), f"処理中: {i}/{len(images)}")

            result = self.process_single_image(img, i, remove_bg)
            results.append(result)

            if result["success"]:
                success_count += 1
            else:
                failed_count += 1

        # main.png と tab.png を生成
        main_path = None
        tab_path = None

        if success_count > 0:
            first_stamp = self.output_dir / get_stamp_filename(1)
            if first_stamp.exists():
                main_path, tab_path = self._generate_main_and_tab(first_stamp)

        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "total": len(images),
            "results": results,
            "main_path": main_path,
            "tab_path": tab_path,
            "output_dir": str(self.output_dir)
        }

    def process_grid_image(
        self,
        grid_image: Union[Image.Image, str],
        rows: int = 4,
        cols: int = 4,
        remove_bg: bool = False
    ) -> dict:
        """
        グリッド画像（4x4等）を分割して処理

        Args:
            grid_image: グリッド画像
            rows: 行数
            cols: 列数
            remove_bg: 背景削除するか

        Returns:
            処理結果
        """
        pil_image = self._load_image(grid_image)
        width, height = pil_image.size

        cell_w = width // cols
        cell_h = height // rows

        images = []
        for row in range(rows):
            for col in range(cols):
                left = col * cell_w
                upper = row * cell_h
                right = left + cell_w
                lower = upper + cell_h

                crop = pil_image.crop((left, upper, right, lower))
                images.append(crop)

        return self.process_batch(images, remove_bg)

    def resize_existing_stamps(self, input_dir: str) -> dict:
        """
        既存のスタンプ画像をLINE仕様にリサイズ

        Args:
            input_dir: 入力ディレクトリ

        Returns:
            処理結果
        """
        input_path = Path(input_dir)
        images = []

        # 01.png〜16.png を探す
        for i in range(1, 17):
            filename = get_stamp_filename(i)
            filepath = input_path / filename
            if filepath.exists():
                images.append(str(filepath))

        if not images:
            # PNGファイルを連番として扱う
            png_files = sorted(input_path.glob("*.png"))
            images = [str(f) for f in png_files if f.name not in [MAIN_FILENAME, TAB_FILENAME]]

        return self.process_batch(images, remove_bg=False)

    def _load_image(self, image: Union[Image.Image, bytes, str]) -> Image.Image:
        """様々な形式の画像を PIL Image に変換"""
        if isinstance(image, Image.Image):
            return image.convert(COLOR_MODE)
        elif isinstance(image, bytes):
            return Image.open(io.BytesIO(image)).convert(COLOR_MODE)
        elif isinstance(image, str):
            return Image.open(image).convert(COLOR_MODE)
        else:
            raise ValueError(f"サポートされていない画像形式: {type(image)}")

    def _remove_background(self, image: Image.Image) -> Image.Image:
        """背景を削除して透過PNGに"""
        if not REMBG_AVAILABLE:
            raise ImportError("rembg がインストールされていません: pip install rembg")

        # PIL -> bytes -> rembg -> PIL
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        result = remove_background(buffer.getvalue())
        return Image.open(io.BytesIO(result)).convert(COLOR_MODE)

    def _resize_to_stamp_spec(self, image: Image.Image) -> Image.Image:
        """画像をLINEスタンプ仕様にリサイズ"""
        # バウンディングボックスで余白をトリミング
        bbox = image.getbbox()
        if bbox:
            image = image.crop(bbox)

        # アスペクト比を維持してリサイズ
        image.thumbnail((MAX_CONTENT_WIDTH, MAX_CONTENT_HEIGHT), Image.Resampling.LANCZOS)

        # 370x320 キャンバスに中央配置
        canvas = Image.new(COLOR_MODE, (STAMP_WIDTH, STAMP_HEIGHT), (0, 0, 0, 0))
        paste_x = (STAMP_WIDTH - image.width) // 2
        paste_y = (STAMP_HEIGHT - image.height) // 2
        canvas.paste(image, (paste_x, paste_y))

        return canvas

    def _resize_fit_center(self, image: Image.Image, target_size: tuple) -> Image.Image:
        """指定サイズに収めて中央配置"""
        img = image.copy()

        # バウンディングボックスで余白をトリミング
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)

        img.thumbnail(target_size, Image.Resampling.LANCZOS)

        canvas = Image.new(COLOR_MODE, target_size, (0, 0, 0, 0))
        paste_x = (target_size[0] - img.width) // 2
        paste_y = (target_size[1] - img.height) // 2
        canvas.paste(img, (paste_x, paste_y))

        return canvas

    def _generate_main_and_tab(self, base_image_path: Path) -> tuple:
        """main.png と tab.png を生成"""
        base_img = Image.open(base_image_path).convert(COLOR_MODE)

        # main.png (240x240)
        main_img = self._resize_fit_center(base_img, (MAIN_WIDTH, MAIN_HEIGHT))
        main_path = self.output_dir / MAIN_FILENAME
        main_img.save(main_path, FILE_FORMAT)

        # tab.png (96x74)
        tab_img = self._resize_fit_center(base_img, (TAB_WIDTH, TAB_HEIGHT))
        tab_path = self.output_dir / TAB_FILENAME
        tab_img.save(tab_path, FILE_FORMAT)

        return str(main_path), str(tab_path)


# CLI用
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python -m core.stamp_processor <input_dir>")
        print("  python -m core.stamp_processor <grid_image.png> --grid 4x4")
        sys.exit(1)

    processor = StampProcessor()
    input_path = sys.argv[1]

    if "--grid" in sys.argv:
        # グリッド処理
        grid_idx = sys.argv.index("--grid")
        grid_spec = sys.argv[grid_idx + 1] if grid_idx + 1 < len(sys.argv) else "4x4"
        rows, cols = map(int, grid_spec.split("x"))

        print(f"グリッド画像を処理中: {input_path} ({rows}x{cols})")
        result = processor.process_grid_image(input_path, rows, cols, remove_bg=True)
    else:
        # ディレクトリ処理
        print(f"ディレクトリを処理中: {input_path}")
        result = processor.resize_existing_stamps(input_path)

    print(f"\n完了: {result['success_count']}/{result['total']} 成功")
    print(f"出力先: {result['output_dir']}")
