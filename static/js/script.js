/**
 * LINEスタンプ丸投げちゃん フロントエンドスクリプト v2.0
 * ワークフロー: APIキー入力 → キャラ提案 → 選択 → 画像生成 → 手動切り抜き
 */
document.addEventListener('DOMContentLoaded', () => {
    // ========================================
    // Configuration
    // ========================================
    const API_BASE = '/api';

    // ========================================
    // State
    // ========================================
    const state = {
        apiKey: null,
        characters: [],
        selectedCharacter: null,
        generatedImage: null
    };

    // ========================================
    // UI Components
    // ========================================
    const ui = {
        toastContainer: document.getElementById('toastContainer'),
        apiKeyInput: document.getElementById('apiKey'),
        apiStatus: document.getElementById('apiStatus'),
        apiStatusIcon: document.getElementById('apiStatusIcon'),
        apiStatusText: document.getElementById('apiStatusText'),
        verifyBtn: document.getElementById('verifyBtn'),
        modelStatus: document.getElementById('modelStatus'),
        modelStatusError: document.getElementById('modelStatusError'),
        modelStatusErrorText: document.getElementById('modelStatusErrorText'),
        textModelName: document.getElementById('textModelName'),
        imageModelName: document.getElementById('imageModelName'),
        proposeBtn: document.getElementById('proposeBtn'),
        proposalLoading: document.getElementById('proposalLoading'),
        characterOptions: document.getElementById('characterOptions'),
        step3: document.getElementById('step3'),
        selectedCharacter: document.getElementById('selectedCharacter'),
        generateBtn: document.getElementById('generateBtn'),
        generateLoading: document.getElementById('generateLoading'),
        generatedResult: document.getElementById('generatedResult'),
        step4: document.getElementById('step4'),
        step5: document.getElementById('step5'),
        registrationInfo: document.getElementById('registrationInfo')
    };

    // ========================================
    // Toast Notifications
    // ========================================
    function showToast(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('role', 'alert');

        const icons = {
            success: '\u2713',
            error: '\u2715',
            info: '\u2139',
            warning: '\u26A0'
        };

        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <span class="toast-message">${escapeHtml(message)}</span>
        `;

        ui.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-out forwards';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ========================================
    // API Key Management
    // ========================================
    async function saveApiKey() {
        const apiKey = ui.apiKeyInput?.value.trim();

        if (!apiKey) return;

        state.apiKey = apiKey;
        sessionStorage.setItem('gemini_api_key', apiKey);

        try {
            const resp = await fetch(`${API_BASE}/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey })
            });
            const result = await resp.json();

            if (result.success) {
                showToast('APIキーを保存しました', 'success');
                updateApiStatus(true);
            } else {
                showToast(result.error || 'APIキーの保存に失敗しました', 'error');
                updateApiStatus(false);
            }
        } catch (e) {
            console.error('API key save error:', e);
            showToast('サーバーとの通信に失敗しました', 'error');
        }
    }

    function updateApiStatus(connected) {
        if (!ui.apiStatus) return;

        ui.apiStatus.classList.remove('hidden');

        if (connected) {
            ui.apiStatus.className = 'badge badge-success';
            if (ui.apiStatusIcon) ui.apiStatusIcon.textContent = '\u2713';
            if (ui.apiStatusText) ui.apiStatusText.textContent = '接続済み';
        } else {
            ui.apiStatus.className = 'badge badge-warning';
            if (ui.apiStatusIcon) ui.apiStatusIcon.textContent = '\u26A0';
            if (ui.apiStatusText) ui.apiStatusText.textContent = '未設定';
        }
    }

    async function checkApiConnection() {
        try {
            const resp = await fetch(`${API_BASE}/config`);
            const result = await resp.json();
            updateApiStatus(result.has_api_key);
        } catch (e) {
            updateApiStatus(false);
        }
    }

    // ========================================
    // API Connection Verification
    // ========================================
    window.verifyConnection = async function() {
        const apiKey = ui.apiKeyInput?.value.trim();
        if (!apiKey) {
            showToast('APIキーを入力してください', 'warning');
            return;
        }

        // Save API key first
        await saveApiKey();

        // Show loading state
        if (ui.verifyBtn) {
            ui.verifyBtn.disabled = true;
            ui.verifyBtn.textContent = '確認中...';
        }

        // Hide previous status
        if (ui.modelStatus) ui.modelStatus.classList.add('hidden');
        if (ui.modelStatusError) ui.modelStatusError.classList.add('hidden');

        try {
            const resp = await fetch(`${API_BASE}/verify-connection`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const result = await resp.json();

            if (result.success && result.connected) {
                // Show success status
                if (ui.modelStatus) {
                    ui.modelStatus.classList.remove('hidden');
                    if (ui.textModelName) ui.textModelName.textContent = result.text_model;
                    if (ui.imageModelName) ui.imageModelName.textContent = result.image_model;
                }
                showToast('API接続OK！', 'success');

                // Log to console for verification
                console.log('='.repeat(50));
                console.log('API接続確認');
                console.log(`  テキストモデル: ${result.text_model}`);
                console.log(`  画像モデル: ${result.image_model}`);
                console.log(`  モデルバージョン: ${result.text_model_version || 'unknown'}`);
                console.log('='.repeat(50));

                updateApiStatus(true);
            } else {
                // Show error status
                if (ui.modelStatusError) {
                    ui.modelStatusError.classList.remove('hidden');
                    if (ui.modelStatusErrorText) {
                        ui.modelStatusErrorText.textContent = result.error || '接続に失敗しました';
                    }
                }
                showToast('API接続に失敗しました', 'error');
                updateApiStatus(false);
            }
        } catch (e) {
            console.error('Verify connection error:', e);
            if (ui.modelStatusError) {
                ui.modelStatusError.classList.remove('hidden');
                if (ui.modelStatusErrorText) {
                    ui.modelStatusErrorText.textContent = 'サーバーとの通信に失敗しました';
                }
            }
            showToast('サーバーとの通信に失敗しました', 'error');
        } finally {
            if (ui.verifyBtn) {
                ui.verifyBtn.disabled = false;
                ui.verifyBtn.textContent = '確認';
            }
        }
    };

    // ========================================
    // Character Proposal
    // ========================================
    window.proposeCharacters = async function() {
        const apiKey = ui.apiKeyInput?.value.trim();
        if (!apiKey) {
            showToast('APIキーを入力してください', 'warning');
            return;
        }

        // Save API key first
        await saveApiKey();

        // Get user request from textarea
        const requestInput = document.getElementById('characterRequest');
        const userRequest = requestInput?.value.trim() || '';

        // Show loading
        ui.proposeBtn.disabled = true;
        ui.proposalLoading.classList.remove('hidden');
        ui.characterOptions.classList.add('hidden');

        try {
            const resp = await fetch(`${API_BASE}/propose-characters`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request: userRequest })
            });
            const result = await resp.json();

            if (result.success) {
                state.characters = result.characters;
                renderCharacterOptions(result.characters);
                showToast('キャラクター案を生成しました', 'success');

                // Log model info to console
                if (result.model_info) {
                    console.log(`[キャラ提案] 使用モデル: ${result.model_info.model_version || result.model_info.requested_model}`);
                }
            } else {
                showToast(result.error || 'キャラクター提案に失敗しました', 'error');
            }
        } catch (e) {
            console.error('Propose error:', e);
            showToast('サーバーとの通信に失敗しました', 'error');
        } finally {
            ui.proposeBtn.disabled = false;
            ui.proposalLoading.classList.add('hidden');
        }
    };

    function renderCharacterOptions(characters) {
        ui.characterOptions.innerHTML = characters.map((char, index) => `
            <div class="character-option" onclick="selectCharacter(${index})">
                <div class="character-number">${index + 1}</div>
                <div class="character-content">
                    <div class="character-name">${escapeHtml(char.name)}</div>
                    <div class="character-desc">${escapeHtml(char.concept)}</div>
                </div>
            </div>
        `).join('');
        ui.characterOptions.classList.remove('hidden');
    }

    window.selectCharacter = function(index) {
        state.selectedCharacter = state.characters[index];

        // Update UI selection
        document.querySelectorAll('.character-option').forEach((el, i) => {
            el.classList.toggle('selected', i === index);
        });

        // Show Step 3
        ui.step3.classList.remove('hidden');
        ui.selectedCharacter.innerHTML = `
            <h4>${escapeHtml(state.selectedCharacter.name)}</h4>
            <p class="text-sm text-muted">${escapeHtml(state.selectedCharacter.concept)}</p>
        `;

        // Scroll to step 3
        ui.step3.scrollIntoView({ behavior: 'smooth' });

        showToast(`「${state.selectedCharacter.name}」を選択しました`, 'info');
    };

    // ========================================
    // Image Generation
    // ========================================
    window.generateStampGrid = async function() {
        if (!state.selectedCharacter) {
            showToast('キャラクターを選択してください', 'warning');
            return;
        }

        // Show loading
        ui.generateBtn.disabled = true;
        ui.generateLoading.classList.remove('hidden');
        ui.generatedResult.classList.add('hidden');

        try {
            const resp = await fetch(`${API_BASE}/generate-grid`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    character: state.selectedCharacter
                })
            });
            const result = await resp.json();

            if (result.success) {
                state.generatedImage = result.image_path;
                renderGeneratedImage(result);
                showToast('画像を生成しました！', 'success');

                // Log model info to console
                if (result.model_info) {
                    console.log('='.repeat(50));
                    console.log('[画像生成完了]');
                    console.log(`  プロンプト生成モデル: ${result.model_info.prompt_model}`);
                    console.log(`  画像生成モデル: ${result.model_info.image_model}`);
                    console.log('='.repeat(50));
                }

                // Show steps 4 and 5
                ui.step4.classList.remove('hidden');
                ui.step5.classList.remove('hidden');

                // Render registration info
                renderRegistrationInfo(result.registration);
            } else {
                showToast(result.error || '画像生成に失敗しました', 'error');
            }
        } catch (e) {
            console.error('Generate error:', e);
            showToast('画像生成に失敗しました', 'error');
        } finally {
            ui.generateBtn.disabled = false;
            ui.generateLoading.classList.add('hidden');
        }
    };

    function renderGeneratedImage(result) {
        ui.generatedResult.innerHTML = `
            <a href="${result.image_url}" target="_blank">
                <img src="${result.image_url}"
                     alt="Generated stamp grid"
                     class="generated-image"
                     onclick="window.open('${result.image_url}', '_blank')">
            </a>
            <p class="text-sm text-muted mt-2">クリックで拡大表示</p>
        `;
        ui.generatedResult.classList.remove('hidden');
    }

    function renderRegistrationInfo(info) {
        if (!info) {
            info = {
                title_ja: state.selectedCharacter?.name || '',
                title_en: '',
                description_ja: '',
                description_en: '',
                copyright: '\u00A9 2025 Your Name'
            };
        }

        ui.registrationInfo.innerHTML = `
            <table>
                <tr>
                    <th>タイトル（日本語）</th>
                    <td><input type="text" value="${escapeHtml(info.title_ja)}" id="regTitleJa"></td>
                </tr>
                <tr>
                    <th>タイトル（英語）</th>
                    <td><input type="text" value="${escapeHtml(info.title_en)}" id="regTitleEn"></td>
                </tr>
                <tr>
                    <th>説明文（日本語）</th>
                    <td><input type="text" value="${escapeHtml(info.description_ja)}" id="regDescJa"></td>
                </tr>
                <tr>
                    <th>説明文（英語）</th>
                    <td><input type="text" value="${escapeHtml(info.description_en)}" id="regDescEn"></td>
                </tr>
                <tr>
                    <th>コピーライト</th>
                    <td><input type="text" value="${escapeHtml(info.copyright)}" id="regCopyright"></td>
                </tr>
            </table>
        `;
    }

    // ========================================
    // Initialization
    // ========================================
    // Load saved API key
    const savedApiKey = sessionStorage.getItem('gemini_api_key');
    if (savedApiKey && ui.apiKeyInput) {
        ui.apiKeyInput.value = savedApiKey;
        checkApiConnection();
    }

    // Debounced API key save
    let saveTimeout = null;
    if (ui.apiKeyInput) {
        ui.apiKeyInput.addEventListener('input', () => {
            if (saveTimeout) clearTimeout(saveTimeout);
            saveTimeout = setTimeout(saveApiKey, 800);
        });
    }

    // ========================================
    // Drag & Drop Resize
    // ========================================
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    const uploadProgressBar = document.getElementById('uploadProgressBar');
    const uploadStatusText = document.getElementById('uploadStatusText');
    const resizeResult = document.getElementById('resizeResult');
    const resultText = document.getElementById('resultText');
    const resultPreview = document.getElementById('resultPreview');
    const downloadLink = document.getElementById('downloadLink');

    if (dropZone && fileInput) {
        // Drag events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('drop-zone-active');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('drop-zone-active');
            }, false);
        });

        // Handle drop
        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFiles(files);
            }
        });

        // Handle file input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFiles(e.target.files);
            }
        });

        async function handleFiles(files) {
            // Filter image files only
            const imageFiles = Array.from(files).filter(f => f.type.startsWith('image/'));
            if (imageFiles.length === 0) {
                showToast('画像ファイルを選択してください', 'error');
                return;
            }

            // Show upload status
            uploadStatus.classList.remove('hidden');
            resizeResult.classList.add('hidden');
            uploadProgressBar.style.width = '0%';
            uploadStatusText.textContent = `${imageFiles.length}枚の画像をリサイズ中...`;

            // Prepare FormData
            const formData = new FormData();
            imageFiles.forEach(file => {
                formData.append('files', file);
            });

            try {
                // Animate progress bar
                uploadProgressBar.style.width = '30%';

                const response = await fetch('/api/resize-stamps', {
                    method: 'POST',
                    body: formData
                });

                uploadProgressBar.style.width = '80%';

                const data = await response.json();

                uploadProgressBar.style.width = '100%';

                if (data.success) {
                    // Show result
                    setTimeout(() => {
                        uploadStatus.classList.add('hidden');
                        resizeResult.classList.remove('hidden');
                        resultText.textContent = `${data.processed_count}/${data.total_count}枚をLINE仕様（370x320px）にリサイズしました`;
                        downloadLink.href = data.download_url;

                        // Show preview (first few images)
                        resultPreview.innerHTML = '';
                        const successResults = data.results.filter(r => r.success).slice(0, 6);
                        successResults.forEach(r => {
                            const img = document.createElement('img');
                            img.src = `/output/${data.folder}/${r.filename}`;
                            img.alt = r.filename;
                            img.className = 'preview-thumb';
                            resultPreview.appendChild(img);
                        });
                        if (data.processed_count > 6) {
                            const more = document.createElement('span');
                            more.className = 'preview-more';
                            more.textContent = `+${data.processed_count - 6}`;
                            resultPreview.appendChild(more);
                        }

                        showToast(`${data.processed_count}枚のリサイズ完了！`, 'success');
                    }, 300);
                } else {
                    uploadStatus.classList.add('hidden');
                    showToast(data.error || 'リサイズに失敗しました', 'error');
                }
            } catch (error) {
                uploadStatus.classList.add('hidden');
                showToast('エラーが発生しました: ' + error.message, 'error');
            }

            // Reset file input
            fileInput.value = '';
        }
    }

    console.log('LINEスタンプ丸投げちゃん v2.0.0 - initialized');
});

// ========================================
// LINEスタンプ丸投げちゃん
// Copyright (c) 2025 株式会社CLAN
// Licensed under MIT License
// ========================================
