/* ── 状态 ── */
let currentFileId = null;
let currentFilePath = null;
let currentMetadata = null;

/* ── DOM 引用 ── */
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const selectFileBtn = document.getElementById('selectFileBtn');
const uploadProgress = document.getElementById('uploadProgress');
const stepPreview = document.getElementById('step-preview');
const stepExtract = document.getElementById('step-extract');
const stepResult = document.getElementById('step-result');

const videoInfo = document.getElementById('videoInfo');
const videoPlayer = document.getElementById('videoPlayer');
const filePathInput = document.getElementById('filePath');
const modeSelect = document.getElementById('modeSelect');
const intervalSettings = document.getElementById('intervalSettings');
const customSettings = document.getElementById('customSettings');
const startTimeInput = document.getElementById('startTime');
const endTimeInput = document.getElementById('endTime');
const extractForm = document.getElementById('extractForm');
const extractBtn = document.getElementById('extractBtn');
const resultTitle = document.getElementById('resultTitle');
const extractProgressFill = document.getElementById('extractProgressFill');
const extractStatus = document.getElementById('extractStatus');
const resultActions = document.getElementById('resultActions');
const downloadLink = document.getElementById('downloadLink');
const resultError = document.getElementById('resultError');
const qualitySlider = document.querySelector('input[name="quality"]');
const qualityValue = document.getElementById('qualityValue');

/* ── 上传 ── */

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) uploadFile(files[0]);
});

selectFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) uploadFile(fileInput.files[0]);
});

async function uploadFile(file) {
    // 验证格式
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    const supported = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'];
    if (!supported.includes(ext)) {
        showError('不支持的文件格式: ' + ext);
        return;
    }

    // 显示进度
    uploadProgress.classList.remove('hidden');
    uploadProgress.querySelector('.progress-fill').style.width = '10%';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        uploadProgress.querySelector('.progress-fill').style.width = '100%';
        setTimeout(() => uploadProgress.classList.add('hidden'), 500);

        if (!resp.ok) {
            const err = await resp.json();
            showError(err.detail || '上传失败');
            return;
        }

        const data = await resp.json();
        currentFileId = data.file_id;
        currentFilePath = data.path;
        currentMetadata = data.metadata;

        showVideoInfo(data);
        showVideoPreview(data.path);
        setupExtractForm(data.metadata);

        stepPreview.classList.remove('hidden');
        stepExtract.classList.remove('hidden');
        stepResult.classList.add('hidden');
        resultActions.classList.add('hidden');
        resultError.classList.add('hidden');

        // 滚动到预览
        stepPreview.scrollIntoView({ behavior: 'smooth' });

    } catch (e) {
        showError('网络错误: ' + e.message);
    }
}

/* ── 显示视频信息 ── */

function showVideoInfo(data) {
    const m = data.metadata;
    const sizeMB = (m.size / 1024 / 1024).toFixed(1);

    videoInfo.innerHTML = `
        <div class="info-item">
            <div class="label">文件名</div>
            <div class="value">${escapeHtml(data.filename)}</div>
        </div>
        <div class="info-item">
            <div class="label">时长</div>
            <div class="value">${formatTime(m.duration)}</div>
        </div>
        <div class="info-item">
            <div class="label">分辨率</div>
            <div class="value">${m.width}×${m.height}</div>
        </div>
        <div class="info-item">
            <div class="label">帧率</div>
            <div class="value">${m.fps} fps</div>
        </div>
        <div class="info-item">
            <div class="label">总帧数</div>
            <div class="value">${m.total_frames.toLocaleString()}</div>
        </div>
        <div class="info-item">
            <div class="label">编码</div>
            <div class="value">${m.codec}</div>
        </div>
        <div class="info-item">
            <div class="label">文件大小</div>
            <div class="value">${sizeMB} MB</div>
        </div>
    `;
}

function showVideoPreview(path) {
    videoPlayer.src = '/api/video/' + path;
    videoPlayer.load();
}

/* ── 提取设置 ── */

function setupExtractForm(metadata) {
    filePathInput.value = currentFilePath;
    startTimeInput.value = 0;
    endTimeInput.value = metadata.duration;
    endTimeInput.max = metadata.duration;
    startTimeInput.max = metadata.duration;
}

/* ── 模式切换 ── */

modeSelect.addEventListener('change', () => {
    if (modeSelect.value === 'interval') {
        intervalSettings.classList.remove('hidden');
        customSettings.classList.add('hidden');
    } else {
        intervalSettings.classList.add('hidden');
        customSettings.classList.remove('hidden');
    }
});

/* ── 质量滑块 ── */

qualitySlider.addEventListener('input', () => {
    qualityValue.textContent = qualitySlider.value;
});

/* ── 提取 ── */

extractForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await startExtract();
});

async function startExtract() {
    extractBtn.disabled = true;
    extractBtn.textContent = '⏳ 提取中...';

    stepResult.classList.remove('hidden');
    resultTitle.textContent = '⏳ 正在提取帧...';
    resultActions.classList.add('hidden');
    resultError.classList.add('hidden');
    extractProgressFill.style.width = '0%';
    extractStatus.textContent = '正在提取...';

    const formData = new FormData(extractForm);

    // 如果是自定义时间戳模式，把文本转 JSON
    if (modeSelect.value === 'custom') {
        const textarea = document.querySelector('textarea[name="timestamps_input"]');
        const lines = textarea.value.split('\n').map(s => s.trim()).filter(Boolean);
        formData.set('mode', 'custom');
        formData.set('timestamps', JSON.stringify(lines));
    }

    try {
        const resp = await fetch('/api/extract', {
            method: 'POST',
            body: formData,
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: '提取失败' }));
            showResultError(err.detail || '提取失败');
            return;
        }

        // 下载文件
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.download = 'frames.zip';

        const frameCount = formData.get('mode') === 'custom'
            ? document.querySelector('textarea[name="timestamps_input"]').value.split('\n').filter(Boolean).length
            : Math.floor((parseFloat(endTimeInput.value || currentMetadata.duration) - parseFloat(startTimeInput.value)) / parseFloat(formData.get('interval') || 1));

        const totalFrames = Math.min(frameCount, 9999); // upper bound

        resultTitle.textContent = '✅ 提取完成';
        extractProgressFill.style.width = '100%';
        extractStatus.textContent = `成功提取 ${totalFrames}+ 帧`;
        resultActions.classList.remove('hidden');

    } catch (e) {
        showResultError('网络错误: ' + e.message);
    } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = '🔄 提取帧';
    }
}

/* ── 错误提示 ── */

function showError(msg) {
    resultError.textContent = msg;
    resultError.classList.remove('hidden');
    setTimeout(() => resultError.classList.add('hidden'), 5000);
}

function showResultError(msg) {
    resultTitle.textContent = '❌ 提取失败';
    resultError.textContent = msg;
    resultError.classList.remove('hidden');
    extractProgressFill.style.width = '0%';
    extractStatus.textContent = '';
}

/* ── 重置 ── */

function resetAll() {
    stepPreview.classList.add('hidden');
    stepExtract.classList.add('hidden');
    stepResult.classList.add('hidden');
    videoPlayer.src = '';
    currentFileId = null;
    currentFilePath = null;
    currentMetadata = null;
    fileInput.value = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ── 工具函数 ── */

function formatTime(sec) {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = Math.floor(sec % 60);
    return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

function pad(n) {
    return String(n).padStart(2, '0');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
