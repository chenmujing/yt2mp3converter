// Global variables
let conversionHistory = JSON.parse(localStorage.getItem('conversionHistory')) || [];
let currentConversion = null;
let batchQueue = [];
let isConverting = false;
let autoConvertTimeout;
let currentTaskId = null;
let statusCheckInterval = null;
let selectedFormat = 'mp3'; // 默认选择MP3格式

// API配置 - 动态检测环境
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:5000/api' 
    : 'https://yt2mp3converter-production.up.railway.app/api';

// 添加请求拦截器处理CORS
const fetchWithCORS = async (url, options = {}) => {
    const defaultOptions = {
        mode: 'cors',
        credentials: 'omit',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    return fetch(url, { ...defaultOptions, ...options });
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Check theme setting
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    // Load conversion history
    loadConversionHistory();
    
    // Add event listeners
    addEventListeners();
    
    // Check clipboard permission
    checkClipboardPermission();
}

function addEventListeners() {
    // URL input events
    const urlInput = document.getElementById('youtube-url');
    urlInput.addEventListener('paste', handleUrlPaste);
    urlInput.addEventListener('input', handleUrlInput);
    urlInput.addEventListener('keydown', handleKeyDown);
    
    // Format selection events
    const formatBtns = document.querySelectorAll('.format-btn');
    formatBtns.forEach(btn => {
        btn.addEventListener('click', handleFormatSelection);
    });
    
    // Mobile navigation
    const mobileToggle = document.querySelector('.nav-mobile-toggle');
    if (mobileToggle) {
        mobileToggle.addEventListener('click', toggleMobileMenu);
    }
    
    // Smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Theme toggle functionality
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
    
    showNotification(`Switched to ${newTheme === 'dark' ? 'dark' : 'light'} mode`, 'success');
}

function updateThemeIcon(theme) {
    const themeIcon = document.querySelector('.theme-toggle i');
    if (themeIcon) {
        themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Clipboard functionality
async function checkClipboardPermission() {
    try {
        const permission = await navigator.permissions.query({ name: 'clipboard-read' });
        return permission.state === 'granted';
    } catch (error) {
        return false;
    }
}

async function pasteFromClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        if (text && isValidYouTubeUrl(text)) {
            document.getElementById('youtube-url').value = text;
            validateUrl();
            showNotification('Link pasted from clipboard', 'success');
        } else {
            showNotification('No valid YouTube link found in clipboard', 'warning');
        }
    } catch (error) {
        showNotification('Cannot access clipboard', 'error');
    }
}

// URL validation
function isValidYouTubeUrl(url) {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    return youtubeRegex.test(url);
}

function validateUrl() {
    const urlInput = document.getElementById('youtube-url');
    const convertBtn = document.querySelector('.convert-btn');
    
    if (urlInput.value.trim() && isValidYouTubeUrl(urlInput.value.trim())) {
        urlInput.style.borderColor = 'var(--success-color)';
        convertBtn.disabled = false;
    } else if (urlInput.value.trim()) {
        urlInput.style.borderColor = 'var(--error-color)';
        convertBtn.disabled = true;
    } else {
        urlInput.style.borderColor = 'var(--border-color)';
        convertBtn.disabled = false;
    }
}

// Handle URL input changes
function handleUrlInput(e) {
    clearTimeout(autoConvertTimeout);
    const url = e.target.value.trim();
    
    // Update input status
    updateInputStatus(url);
    
    // Auto-convert immediately when valid URL is detected
    if (url && isValidYouTubeUrl(url) && !isConverting) {
        autoConvertTimeout = setTimeout(() => {
            startConversion();
        }, 800); // Shorter delay for immediate response
    }
}

function handleKeyDown(e) {
    // Clear auto-convert on backspace/delete
    if (e.key === 'Backspace' || e.key === 'Delete') {
        clearTimeout(autoConvertTimeout);
    }
    
    // Manual convert on Enter
    if (e.key === 'Enter') {
        clearTimeout(autoConvertTimeout);
        startConversion();
    }
}

function updateInputStatus(url) {
    const inputStatus = document.getElementById('input-status');
    const convertBtn = document.getElementById('convert-btn');
    
    if (!url) {
        inputStatus.innerHTML = '<i class="fas fa-link"></i>';
        inputStatus.className = 'input-status';
    } else if (isValidYouTubeUrl(url)) {
        inputStatus.innerHTML = '<i class="fas fa-check-circle"></i>';
        inputStatus.className = 'input-status valid';
    } else {
        inputStatus.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
        inputStatus.className = 'input-status invalid';
    }
    // Keep button always enabled
}

function handleUrlPaste(e) {
    setTimeout(() => {
        const url = e.target.value.trim();
        updateInputStatus(url);
        
        // Auto-convert immediately on paste if valid
        if (url && isValidYouTubeUrl(url) && !isConverting) {
            clearTimeout(autoConvertTimeout);
            autoConvertTimeout = setTimeout(() => {
                startConversion();
            }, 500); // Very short delay for paste
        }
    }, 100);
}

// Format selection handling
function handleFormatSelection(e) {
    const formatBtn = e.currentTarget;
    const format = formatBtn.dataset.format;
    
    // Update selected format
    selectedFormat = format;
    
    // Update UI
    document.querySelectorAll('.format-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    formatBtn.classList.add('active');
    
    // Re-trigger conversion if URL is already entered
    const url = document.getElementById('youtube-url').value.trim();
    if (url && isValidYouTubeUrl(url) && !isConverting) {
        clearTimeout(autoConvertTimeout);
        autoConvertTimeout = setTimeout(() => {
            startConversion();
        }, 800);
    }
}

// Extract YouTube video ID
function getYouTubeVideoId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
}

// Get video info from backend API
async function getVideoInfo(url) {
    try {
        const response = await fetchWithCORS(`${API_BASE_URL}/video-info`, {
            method: 'POST',
            body: JSON.stringify({ url: url })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 安全检查响应数据
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid response data');
        }
        
        if (data.success && data.data) {
            return data.data;
        } else {
            throw new Error(data.error || 'Failed to get video info');
        }
    } catch (error) {
        console.error('Error getting video info:', error);
        
        // 如果获取视频信息失败，返回默认信息而不是抛出错误
        const videoId = url.includes('v=') ? url.split('v=')[1]?.substring(0, 11) || 'unknown' : 'unknown';
        return {
            id: videoId,
            title: 'YouTube Video',
            duration: 180,
            duration_string: '3:00',
            thumbnail: `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`,
            uploader: 'Unknown Channel'
        };
    }
}

// Start conversion with real backend API
async function startConversion() {
    if (isConverting) return;
    
    const url = document.getElementById('youtube-url').value.trim();
    if (!url || !isValidYouTubeUrl(url)) {
        showNotification('Please enter a valid YouTube link', 'error');
        return;
    }
    
    clearTimeout(autoConvertTimeout);
    isConverting = true;
    
    const convertBtn = document.getElementById('convert-btn');
    const progressSection = document.getElementById('progress-section');
    const downloadsSection = document.getElementById('downloads-section');
    const inputStatus = document.getElementById('input-status');
    
    // Update UI states
    convertBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Converting...';
    inputStatus.innerHTML = '<i class="fas fa-cog fa-spin"></i>';
    inputStatus.className = 'input-status processing';
    
    // Show progress area
    progressSection.style.display = 'block';
    downloadsSection.style.display = 'none';
    
    try {
        // Step 1: Get video info
        updateConversionStatus('Getting video information...');
        const videoInfo = await getVideoInfo(url);
        displayVideoInfo(videoInfo);
        
        // Step 2: Start conversion
        updateConversionStatus('Starting conversion...');
        
        // 根据选择的格式确定要转换的格式
        let formats;
        if (selectedFormat === 'mp3') {
            formats = ['mp3_256']; // 只转换MP3 256kbps
        } else {
            formats = ['mp4_720']; // 只转换MP4 720p
        }
        
        const response = await fetchWithCORS(`${API_BASE_URL}/convert`, {
            method: 'POST',
            body: JSON.stringify({ 
                url: url,
                formats: formats
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const conversionData = await response.json();
        if (!conversionData.success) {
            throw new Error(conversionData.error || 'Conversion failed');
        }
        
        currentTaskId = conversionData.task_id;
        
        // Step 3: Monitor conversion progress
        await monitorConversionProgress(currentTaskId);
        
    } catch (error) {
        console.error('Conversion error:', error);
        showNotification(`Conversion failed: ${error.message}`, 'error');
        progressSection.style.display = 'none';
    } finally {
        isConverting = false;
        convertBtn.innerHTML = '<i class="fas fa-magic"></i> Convert';
        inputStatus.innerHTML = '<i class="fas fa-check-circle"></i>';
        inputStatus.className = 'input-status valid';
        
        // Clear status check interval
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            statusCheckInterval = null;
        }
    }
}

// Monitor conversion progress
async function monitorConversionProgress(taskId) {
    return new Promise((resolve, reject) => {
        statusCheckInterval = setInterval(async () => {
            try {
                const response = await fetchWithCORS(`${API_BASE_URL}/status/${taskId}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const status = await response.json();
                
                // 安全检查状态对象
                if (!status || typeof status !== 'object') {
                    throw new Error('Invalid status response');
                }
                
                // 确保progress是数字
                const progress = typeof status.progress === 'number' ? status.progress : 0;
                
                // Update progress UI
                const progressFill = document.getElementById('progress-fill');
                const progressText = document.getElementById('progress-text');
                
                if (progressFill) {
                    progressFill.style.width = `${progress}%`;
                }
                if (progressText) {
                    progressText.textContent = `${progress}%`;
                }
                
                // Update status text based on progress
                if (progress < 20) {
                    updateConversionStatus('Downloading video...');
                } else if (progress < 40) {
                    updateConversionStatus('Extracting audio...');
                } else if (progress < 60) {
                    updateConversionStatus('Converting formats...');
                } else if (progress < 80) {
                    updateConversionStatus('Optimizing quality...');
                } else if (progress < 100) {
                    updateConversionStatus('Finalizing files...');
                } else {
                    updateConversionStatus('Conversion complete!');
                }
                
                if (status.status === 'completed') {
                    clearInterval(statusCheckInterval);
                    statusCheckInterval = null;
                    
                    // 调试：记录完整的status响应
                    console.log('Conversion completed, status:', status);
                    
                    // 安全检查响应数据
                    const files = status.files || {};
                    const videoInfo = status.video_info || {};
                    
                    console.log('Files object:', files);
                    console.log('Files keys:', Object.keys(files));
                    console.log('Files length:', Object.keys(files).length);
                    
                    // 显示下载链接 - 移除严格检查，总是尝试显示
                    try {
                        displayRealDownloadItems(files, videoInfo);
                        
                        // Add to history
                        addToHistory({
                            url: document.getElementById('youtube-url').value.trim(),
                            videoInfo: videoInfo,
                            timestamp: new Date().toISOString(),
                            taskId: taskId,
                            files: files
                        });
                        
                        showNotification('Conversion completed!', 'success');
                    } catch (displayError) {
                        console.error('Display error:', displayError);
                        showNotification('Conversion completed but display failed', 'warning');
                    }
                    
                    // Hide progress section
                    document.getElementById('progress-section').style.display = 'none';
                    
                    resolve();
                    
                } else if (status.status === 'error') {
                    clearInterval(statusCheckInterval);
                    statusCheckInterval = null;
                    throw new Error(status.error || 'Conversion failed');
                }
                
            } catch (error) {
                clearInterval(statusCheckInterval);
                statusCheckInterval = null;
                reject(error);
            }
        }, 2000); // Check every 2 seconds
    });
}

function displayVideoInfo(videoInfo) {
    if (!videoInfo) {
        console.error('Video info is null or undefined');
        return;
    }
    
    const thumbnail = videoInfo.thumbnail || 'https://via.placeholder.com/320x180?text=No+Thumbnail';
    const title = videoInfo.title || 'Unknown Title';
    const duration = videoInfo.duration_string || 'Unknown';
    const uploader = videoInfo.uploader || 'Unknown';
    
    document.getElementById('video-thumbnail').src = thumbnail;
    document.getElementById('video-title').textContent = title;
    document.getElementById('video-duration').textContent = `Duration: ${duration} | Channel: ${uploader}`;
}

function updateConversionStatus(status) {
    document.getElementById('conversion-status').textContent = status;
}

// Display real download items with actual backend links
function displayRealDownloadItems(files, videoInfo) {
    console.log('displayRealDownloadItems called with:', files, videoInfo);
    
    const downloadsSection = document.getElementById('downloads-section');
    const audioDownloads = document.getElementById('audio-downloads');
    const videoDownloads = document.getElementById('video-downloads');
    
    // Clear previous downloads
    if (audioDownloads) audioDownloads.innerHTML = '';
    if (videoDownloads) videoDownloads.innerHTML = '';
    
    // 如果没有文件或文件无效，显示重试选项
    if (!files || typeof files !== 'object' || Object.keys(files).length === 0) {
        console.log('No valid files, showing retry option');
        if (downloadsSection) {
            downloadsSection.innerHTML = `
                <div class="no-files-message">
                    <h3>下载文件生成中...</h3>
                    <p>正在准备下载文件，请稍候或刷新页面重试</p>
                    <button onclick="location.reload()" class="retry-btn">
                        <i class="fas fa-refresh"></i> 刷新页面
                    </button>
                </div>
                <style>
                .no-files-message {
                    text-align: center;
                    padding: 2rem;
                    background: var(--surface-color);
                    border-radius: 12px;
                    margin: 1rem 0;
                }
                .retry-btn {
                    background: var(--primary-color);
                    color: white;
                    border: none;
                    padding: 0.75rem 1.5rem;
                    border-radius: 8px;
                    cursor: pointer;
                    margin-top: 1rem;
                }
                .retry-btn:hover {
                    background: var(--primary-hover);
                }
                </style>
            `;
            downloadsSection.style.display = 'block';
        }
        return;
    }
    
    // 根据实际转换的格式显示下载项
    let hasAudio = false;
    let hasVideo = false;
    
    // Process all available files
    Object.keys(files).forEach((format, index) => {
        const fileInfo = files[format];
        console.log(`Processing format ${format}:`, fileInfo);
        
        if (!fileInfo || !fileInfo.filename || !fileInfo.download_url) {
            console.error('Invalid file info:', fileInfo);
            return;
        }
        
        // 构建正确的下载URL
        const baseUrl = API_BASE_URL.includes('localhost') 
            ? 'http://localhost:5000'
            : 'https://yt2mp3converter-production.up.railway.app';
            
        let item = {
            name: fileInfo.filename,
            size: formatFileSize(fileInfo.size || 0),
            url: `${baseUrl}${fileInfo.download_url}`,
        };
        
        if (format.startsWith('mp3')) {
            item.type = 'audio';
            if (audioDownloads) {
                audioDownloads.appendChild(createRealDownloadItem(item, 'audio', index));
                hasAudio = true;
            }
        } else if (format.startsWith('mp4')) {
            item.type = 'video';
            if (videoDownloads) {
                videoDownloads.appendChild(createRealDownloadItem(item, 'video', index));
                hasVideo = true;
            }
        }
    });
    
    console.log(`Generated downloads: audio=${hasAudio}, video=${hasVideo}`);
    
    // Hide empty sections
    const audioSection = audioDownloads?.closest('.format-group');
    const videoSection = videoDownloads?.closest('.format-group');
    
    if (audioSection) {
        audioSection.style.display = hasAudio ? 'block' : 'none';
    }
    if (videoSection) {
        videoSection.style.display = hasVideo ? 'block' : 'none';
    }
    
    if (downloadsSection) {
        downloadsSection.style.display = 'block';
    }
    
    // 即使没有文件也不报错，只显示信息
    if (!hasAudio && !hasVideo) {
        console.log('No download items created');
        showNotification('下载文件准备中，请稍候...', 'info');
    }
}

function createRealDownloadItem(item, type, index) {
    const div = document.createElement('div');
    div.className = 'download-item';
    
    const qualityText = type === 'audio' ? 
        item.name.match(/(\d+kbps)/)?.[1] || 'MP3' :
        item.name.match(/(\d+p)/)?.[1] || 'MP4';
    
    div.innerHTML = `
        <div class="download-info">
            <div class="format-icon ${type}">
                <i class="fas fa-${type === 'audio' ? 'music' : 'video'}"></i>
            </div>
            <div class="file-details">
                <span class="file-name">${type.toUpperCase()} ${qualityText}</span>
                <span class="file-size">${item.size}</span>
            </div>
        </div>
        <button class="download-btn" onclick="downloadRealFile('${item.url}', '${item.name}')">
            <i class="fas fa-download"></i>
            Download
        </button>
    `;
    
    return div;
}

function downloadRealFile(url, filename) {
    try {
        console.log(`Downloading: ${url}`);
        showNotification(`开始下载: ${filename}`, 'success');
        
        // 直接在新窗口打开下载链接
        const newWindow = window.open(url, '_blank');
        
        // 备用方案：如果新窗口被阻止，使用传统方法
        if (!newWindow) {
            const link = document.createElement('a');
            link.href = url;
            link.download = filename || 'download';
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        // 检查下载状态
        setTimeout(() => {
            showNotification(`如果下载未开始，请直接点击下载链接`, 'info');
        }, 3000);
        
    } catch (error) {
        console.error('Download error:', error);
        showNotification(`下载失败: ${error.message}`, 'error');
        
        // 最后的备用方案：直接跳转
        window.location.href = url;
    }
}

// Helper function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// History functionality
function addToHistory(fileInfo) {
    try {
        // 安全检查fileInfo
        if (!fileInfo || typeof fileInfo !== 'object') {
            console.error('Invalid fileInfo:', fileInfo);
            return;
        }
        
        // 确保必要的属性存在
        const safeFileInfo = {
            url: fileInfo.url || '',
            videoInfo: fileInfo.videoInfo || { title: 'Unknown', thumbnail: '' },
            timestamp: fileInfo.timestamp || new Date().toISOString(),
            taskId: fileInfo.taskId || '',
            files: fileInfo.files || {}
        };
        
        conversionHistory.unshift(safeFileInfo);
        
        // Limit history count
        if (conversionHistory.length > 50) {
            conversionHistory = conversionHistory.slice(0, 50);
        }
        
        localStorage.setItem('conversionHistory', JSON.stringify(conversionHistory));
        loadConversionHistory();
    } catch (error) {
        console.error('Error adding to history:', error);
    }
}

function loadConversionHistory() {
    try {
        const historyContainer = document.getElementById('history-container');
        
        if (!historyContainer) {
            console.error('History container not found');
            return;
        }
        
        if (!conversionHistory || conversionHistory.length === 0) {
            historyContainer.innerHTML = `
                <div class="empty-history">
                    <i class="fas fa-clock"></i>
                    <p>No conversion history yet</p>
                </div>
            `;
            return;
        }
        
        historyContainer.innerHTML = conversionHistory.map(item => {
            // 安全检查每个历史项目
            const videoInfo = item.videoInfo || { title: 'Unknown', thumbnail: '' };
            const title = videoInfo.title || 'Unknown';
            const thumbnail = videoInfo.thumbnail || 'https://via.placeholder.com/80x60?text=No+Image';
            const url = item.url || '';
            const timestamp = item.timestamp || new Date().toISOString();
            
            return `
            <div class="history-item">
                <div class="history-info">
                    <img src="${thumbnail}" alt="Thumbnail" class="history-thumbnail" 
                         onerror="this.src='https://via.placeholder.com/80x60?text=No+Image'">
                    <div class="history-details">
                        <h4>${title}</h4>
                        <p>Download completed</p>
                        <small>Converted: ${new Date(timestamp).toLocaleString('en-US')}</small>
                    </div>
                </div>
                <div class="history-actions">
                    <button onclick="redownload('${url}')" class="redownload-btn">
                        <i class="fas fa-redo"></i>
                        Re-convert
                    </button>
                </div>
            </div>
            `;
                 }).join('');
    } catch (error) {
        console.error('Error loading history:', error);
        const historyContainer = document.getElementById('history-container');
        if (historyContainer) {
            historyContainer.innerHTML = `
                <div class="empty-history">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading history</p>
                </div>
            `;
        }
    }
     
     // Add history styles if not already added
    if (!document.getElementById('history-styles')) {
        const style = document.createElement('style');
        style.id = 'history-styles';
        style.textContent = `
            .history-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem;
                margin-bottom: 1rem;
                background: var(--surface-color);
                border-radius: 12px;
                border: 1px solid var(--border-color);
            }
            
            .history-info {
                display: flex;
                align-items: center;
                gap: 1rem;
                flex: 1;
            }
            
            .history-thumbnail {
                width: 80px;
                height: 60px;
                border-radius: 8px;
                object-fit: cover;
            }
            
            .history-details h4 {
                margin-bottom: 0.25rem;
                color: var(--text-primary);
                font-size: 1rem;
            }
            
            .history-details p {
                color: var(--text-secondary);
                font-size: 0.875rem;
                margin-bottom: 0.25rem;
            }
            
            .history-details small {
                color: var(--text-secondary);
                font-size: 0.75rem;
            }
            
            .redownload-btn {
                background: var(--primary-color);
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.875rem;
                transition: all 0.3s ease;
            }
            
            .redownload-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
            }
        `;
        document.head.appendChild(style);
    }
}

function clearHistory() {
    if (confirm('Are you sure you want to clear all conversion history?')) {
        conversionHistory = [];
        localStorage.removeItem('conversionHistory');
        loadConversionHistory();
        showNotification('History cleared', 'success');
    }
}

function redownload(url) {
    document.getElementById('youtube-url').value = url;
    updateInputStatus(url);
    document.getElementById('youtube-url').scrollIntoView({ behavior: 'smooth' });
    showNotification('Link filled in, auto-conversion will start shortly', 'success');
    
    // Trigger auto-conversion
    if (!isConverting) {
        clearTimeout(autoConvertTimeout);
        autoConvertTimeout = setTimeout(() => {
            startConversion();
        }, 1000);
    }
}

// FAQ functionality
function toggleFaq(element) {
    const faqItem = element.closest('.faq-item');
    const isActive = faqItem.classList.contains('active');
    
    // Close all FAQs
    document.querySelectorAll('.faq-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Toggle current FAQ
    if (!isActive) {
        faqItem.classList.add('active');
    }
}

// Mobile navigation
function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    navMenu.classList.toggle('mobile-active');
}

// Notification functionality
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Page scroll effect
window.addEventListener('scroll', debounce(() => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 100) {
        navbar.style.background = 'var(--surface-color)';
        navbar.style.boxShadow = '0 2px 20px var(--shadow-color)';
    } else {
        navbar.style.background = 'var(--surface-color)';
        navbar.style.boxShadow = 'none';
    }
}, 10));

// Error handling - Only log errors, don't show notifications for every error
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    // Removed automatic error notification to prevent false positives
});

// Export functions for HTML calls
window.toggleTheme = toggleTheme;
window.pasteFromClipboard = pasteFromClipboard;
window.startConversion = startConversion;
window.downloadRealFile = downloadRealFile;
window.clearHistory = clearHistory;
window.toggleFaq = toggleFaq;
window.scrollToConverter = scrollToConverter;

// Scroll to converter function
function scrollToConverter() {
    const urlInput = document.getElementById('youtube-url');
    if (urlInput) {
        urlInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => {
            urlInput.focus();
        }, 500);
    }
} 