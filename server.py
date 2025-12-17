"""
LINEスタンプ丸投げちゃん - Flask サーバー

ローカル環境専用のWebサーバー。
Gemini APIを使った画像生成とLINE仕様への変換を行います。
"""

import os
import io
import json
import base64
import re
import unicodedata
import zipfile
from functools import wraps
from pathlib import Path
from urllib.parse import unquote
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Core モジュール
from core.gemini_client import GeminiClient
from core.stamp_processor import StampProcessor

# ========================================
# Flask アプリ設定
# ========================================

app = Flask(__name__, static_folder='static')

# CORS設定（ローカル環境のみ許可）
CORS(app, origins=[
    'http://localhost:5000',
    'http://127.0.0.1:5000'
])

# ファイルサイズ制限
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_PER_REQUEST = 20
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE * MAX_FILES_PER_REQUEST

# 許可する拡張子
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

# ディレクトリ設定
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "output"
CONFIG_FILE = DATA_DIR / "mcp_config.json"

# ディレクトリ作成
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ========================================
# セキュリティ関数
# ========================================

def safe_filename(filename):
    """日本語対応の安全なファイル名変換"""
    filename = unquote(filename)
    filename = unicodedata.normalize('NFC', filename)
    filename = filename.replace('/', '_').replace('\\', '_')
    filename = filename.replace('..', '_')
    filename = re.sub(r'[\x00-\x1f\x7f<>:"|?*]', '', filename)
    filename = filename.strip(' .')
    if '/' in filename or '\\' in filename or '..' in filename:
        filename = re.sub(r'[/\\]', '_', filename).replace('..', '_')
    if not filename:
        filename = 'unnamed_file'
    return filename


def validate_extension(filename):
    """ファイル拡張子を検証"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def get_api_key():
    """設定ファイルからAPIキーを取得"""
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
            return config.get('gemini_api_key')
        except:
            pass
    return None


def save_api_key(api_key):
    """APIキーを設定ファイルに保存"""
    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
        except:
            pass
    config['gemini_api_key'] = api_key
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding='utf-8')


def require_api_key(f):
    """APIキーが必要なエンドポイント用デコレータ"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = get_api_key()
        if not api_key:
            return jsonify({'success': False, 'error': 'APIキーが設定されていません'}), 400
        return f(api_key, *args, **kwargs)
    return decorated


# ========================================
# 静的ファイル配信
# ========================================

@app.route('/')
def index():
    """メインページ"""
    return send_file('index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """静的ファイル配信"""
    return send_from_directory('static', filename)


@app.route('/output/<path:filename>')
def serve_output(filename):
    """出力ファイル配信"""
    return send_from_directory(OUTPUT_DIR, filename)


# ========================================
# API エンドポイント
# ========================================

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """API設定の取得・保存"""
    if request.method == 'GET':
        api_key = get_api_key()
        return jsonify({
            'success': True,
            'has_api_key': bool(api_key),
            'api_key_preview': f"{api_key[:8]}..." if api_key else None
        })

    elif request.method == 'POST':
        data = request.get_json()
        api_key = data.get('api_key', '').strip()

        if not api_key:
            return jsonify({'success': False, 'error': 'APIキーが空です'}), 400

        save_api_key(api_key)
        return jsonify({'success': True, 'message': 'APIキーを保存しました'})


@app.route('/api/upload', methods=['POST'])
def api_upload():
    """画像アップロード"""
    if 'files' not in request.files:
        return jsonify({'success': False, 'error': 'ファイルがありません'}), 400

    files = request.files.getlist('files')
    uploaded = []

    for file in files:
        if file.filename and validate_extension(file.filename):
            filename = safe_filename(file.filename)
            # タイムスタンプ付きで保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_name = f"{timestamp}_{filename}"
            save_path = UPLOAD_DIR / save_name
            file.save(save_path)
            uploaded.append({
                'original': file.filename,
                'saved': save_name,
                'path': str(save_path)
            })

    return jsonify({
        'success': True,
        'uploaded_count': len(uploaded),
        'files': uploaded
    })


@app.route('/api/generate', methods=['POST'])
@require_api_key
def api_generate(api_key):
    """Gemini APIで画像生成"""
    data = request.get_json()
    prompt = data.get('prompt', '')
    style = data.get('style', 'kawaii')

    if not prompt:
        return jsonify({'success': False, 'error': 'プロンプトが空です'}), 400

    try:
        client = GeminiClient(api_key)
        image = client.generate_stamp_image(prompt, style)

        # 一時保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = UPLOAD_DIR / f"generated_{timestamp}.png"
        image.save(save_path, 'PNG')

        return jsonify({
            'success': True,
            'path': str(save_path),
            'filename': save_path.name
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/suggest-prompts', methods=['POST'])
@require_api_key
def api_suggest_prompts(api_key):
    """テーマからプロンプトを提案"""
    data = request.get_json()
    theme = data.get('theme', '')
    count = data.get('count', 16)

    if not theme:
        return jsonify({'success': False, 'error': 'テーマが空です'}), 400

    try:
        client = GeminiClient(api_key)
        prompts = client.suggest_stamp_prompts(theme, count)

        return jsonify({
            'success': True,
            'theme': theme,
            'prompts': prompts
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/verify-connection', methods=['POST'])
@require_api_key
def api_verify_connection(api_key):
    """API接続を確認し、実際に使用されるモデルを返す"""
    try:
        client = GeminiClient(api_key)
        result = client.verify_connection()

        # サーバーログに出力
        print("=" * 50)
        print("API接続確認")
        print(f"  テキストモデル: {result['text_model']}")
        print(f"  画像モデル: {result['image_model']}")
        print(f"  ステータス: {'OK' if result['connected'] else 'ERROR'}")
        print("=" * 50)

        return jsonify({
            'success': True,
            **result
        })

    except Exception as e:
        print(f"API接続エラー: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/propose-characters', methods=['POST'])
@require_api_key
def api_propose_characters(api_key):
    """売れそうなキャラクターを5案提案"""
    # リクエストからユーザーの希望を取得
    data = request.get_json() or {}
    user_request = data.get('request', '')

    try:
        client = GeminiClient(api_key)
        characters, model_info = client.propose_characters(user_request)

        # サーバーログに使用モデルを出力
        if user_request:
            print(f"[キャラ提案] リクエスト: {user_request}")
        print(f"[キャラ提案] 使用モデル: {model_info.get('model_version', 'unknown')}")

        return jsonify({
            'success': True,
            'characters': characters,
            'model_info': model_info
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-grid', methods=['POST'])
@require_api_key
def api_generate_grid(api_key):
    """キャラクターから6x3グリッド画像を生成"""
    data = request.get_json()
    character = data.get('character')

    if not character:
        return jsonify({'success': False, 'error': 'キャラクターが指定されていません'}), 400

    try:
        client = GeminiClient(api_key)

        # キャラクター情報から英語プロンプトを生成
        prompt, prompt_model_info = client.create_grid_prompt(character)
        print(f"[プロンプト生成] 使用モデル: {prompt_model_info.get('model_version', 'unknown')}")

        # 画像生成
        image, image_model_info = client.generate_image(prompt)
        print(f"[画像生成] 使用モデル: {image_model_info.get('model_version', 'unknown')}")

        # 保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"grid_{timestamp}.png"
        save_path = OUTPUT_DIR / filename
        image.save(save_path, 'PNG')

        # 英語登録情報を生成
        try:
            en_info = client.generate_registration_info(character)
            print(f"[英語登録情報] 生成完了")
        except Exception as e:
            print(f"[英語登録情報] 生成失敗: {e}")
            en_info = {'title_en': '', 'description_en': ''}

        # 登録情報を生成
        registration = {
            'title_ja': character.get('name', ''),
            'title_en': en_info.get('title_en', ''),
            'description_ja': character.get('concept', ''),
            'description_en': en_info.get('description_en', ''),
            'copyright': '© 2025 Your Name'
        }

        return jsonify({
            'success': True,
            'image_path': str(save_path),
            'image_url': f'/output/{filename}',
            'registration': registration,
            'model_info': {
                'prompt_model': prompt_model_info.get('model_version', 'unknown'),
                'image_model': image_model_info.get('model_version', 'unknown')
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/process', methods=['POST'])
def api_process():
    """画像をLINE仕様に変換"""
    data = request.get_json()
    files = data.get('files', [])
    remove_bg = data.get('remove_bg', False)

    if not files:
        return jsonify({'success': False, 'error': 'ファイルが指定されていません'}), 400

    try:
        # 出力ディレクトリを新規作成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = OUTPUT_DIR / f"stamps_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        processor = StampProcessor(str(output_dir))
        images = [str(UPLOAD_DIR / f) if not Path(f).is_absolute() else f for f in files]

        result = processor.process_batch(images, remove_bg)

        return jsonify({
            'success': True,
            **result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/process-grid', methods=['POST'])
def api_process_grid():
    """グリッド画像を分割して処理"""
    data = request.get_json()
    file_path = data.get('file')
    rows = data.get('rows', 4)
    cols = data.get('cols', 4)
    remove_bg = data.get('remove_bg', False)

    if not file_path:
        return jsonify({'success': False, 'error': 'ファイルが指定されていません'}), 400

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = OUTPUT_DIR / f"stamps_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        processor = StampProcessor(str(output_dir))

        # パスの解決
        if not Path(file_path).is_absolute():
            file_path = str(UPLOAD_DIR / file_path)

        result = processor.process_grid_image(file_path, rows, cols, remove_bg)

        return jsonify({
            'success': True,
            **result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
@require_api_key
def api_analyze(api_key):
    """画像を解析してスタンプ情報を提案"""
    data = request.get_json()
    file_path = data.get('file')

    if not file_path:
        return jsonify({'success': False, 'error': 'ファイルが指定されていません'}), 400

    try:
        client = GeminiClient(api_key)

        if not Path(file_path).is_absolute():
            file_path = str(UPLOAD_DIR / file_path)

        result = client.analyze_image_for_stamp(file_path)

        return jsonify({
            'success': True,
            'analysis': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/files', methods=['GET'])
def api_files():
    """アップロード済みファイル一覧"""
    files = []

    for f in UPLOAD_DIR.glob('*'):
        if f.is_file() and validate_extension(f.name):
            files.append({
                'name': f.name,
                'size': f.stat().st_size,
                'modified': f.stat().st_mtime
            })

    files.sort(key=lambda x: x['modified'], reverse=True)

    return jsonify({
        'success': True,
        'files': files
    })


@app.route('/api/outputs', methods=['GET'])
def api_outputs():
    """出力フォルダ一覧"""
    outputs = []

    for d in OUTPUT_DIR.glob('stamps_*'):
        if d.is_dir():
            files = list(d.glob('*.png'))
            outputs.append({
                'name': d.name,
                'path': str(d),
                'file_count': len(files),
                'has_main': (d / 'main.png').exists(),
                'has_tab': (d / 'tab.png').exists()
            })

    outputs.sort(key=lambda x: x['name'], reverse=True)

    return jsonify({
        'success': True,
        'outputs': outputs
    })


@app.route('/api/download/<folder>', methods=['GET'])
def api_download(folder):
    """出力フォルダをZIPでダウンロード"""
    folder_path = OUTPUT_DIR / folder
    if not folder_path.exists() or not folder_path.is_dir():
        return jsonify({'success': False, 'error': 'フォルダが見つかりません'}), 404

    # ZIPを作成
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in folder_path.glob('*.png'):
            zf.write(f, f.name)

    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{folder}.zip'
    )


@app.route('/api/resize-stamps', methods=['POST'])
def api_resize_stamps():
    """
    切り抜き画像をアップロードしてLINE仕様（370x320px）にリサイズ
    ZIPファイルとしてダウンロードできる形で返す
    """
    if 'files' not in request.files:
        return jsonify({'success': False, 'error': 'ファイルがありません'}), 400

    files = request.files.getlist('files')
    if not files or len(files) == 0:
        return jsonify({'success': False, 'error': 'ファイルがありません'}), 400

    try:
        # 出力ディレクトリを新規作成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = OUTPUT_DIR / f"stamps_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        processor = StampProcessor(str(output_dir))
        results = []

        for i, file in enumerate(files, start=1):
            if file.filename and validate_extension(file.filename):
                try:
                    # ファイルを読み込んでPIL Imageに変換
                    image_bytes = file.read()
                    result = processor.process_single_image(image_bytes, i, remove_bg=False)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'success': False,
                        'filename': file.filename,
                        'error': str(e)
                    })

        # 成功した数をカウント
        success_count = sum(1 for r in results if r.get('success'))

        # main.png と tab.png も生成（最初の画像から）
        if success_count > 0:
            first_stamp = output_dir / "01.png"
            if first_stamp.exists():
                processor._generate_main_and_tab(str(first_stamp))

        return jsonify({
            'success': True,
            'folder': f"stamps_{timestamp}",
            'output_dir': str(output_dir),
            'processed_count': success_count,
            'total_count': len(files),
            'results': results,
            'download_url': f'/api/download/stamps_{timestamp}'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# エラーハンドリング
# ========================================

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'success': False,
        'error': 'ファイルサイズが大きすぎます（上限: 50MB）'
    }), 413


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': '不正なリクエストです'
    }), 400


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'サーバーエラーが発生しました'
    }), 500


# ========================================
# サーバー起動
# ========================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'

    print("=" * 60)
    print("  LINEスタンプ丸投げちゃん")
    print("=" * 60)
    print()
    print(f"  ブラウザで http://localhost:{port} を開いてください")
    print()
    print("  終了: Ctrl+C")
    print("=" * 60)

    # 重要: host='127.0.0.1' でローカルホストのみに制限
    app.run(host='127.0.0.1', port=port, debug=debug_mode)


# ========================================
# ライセンス
# ========================================
# LINEスタンプ丸投げちゃん
# Copyright (c) 2025 株式会社CLAN
# Licensed under MIT License
# ========================================
