// Global variables
let conversionHistory = JSON.parse(localStorage.getItem('conversionHistory')) || [];
let currentConversion = null;
let batchQueue = [];
let isConverting = false;
let autoConvertTimeout;

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

// Extract YouTube video ID
function getYouTubeVideoId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
}

// Get video info (simulation)
async function getVideoInfo(videoId) {
    // This simulates getting video info, in a real application you would use the YouTube API
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                id: videoId,
                title: `Video Title - ${videoId}`,
                duration: '3:45',
                thumbnail: `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`,
                channel: 'Channel Name'
            });
        }, 1000);
    });
}

// Start conversion with multi-format output
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
        const videoId = getYouTubeVideoId(url);
        if (!videoId) {
            throw new Error('Unable to parse video ID');
        }
        
        // Get video info
        updateConversionStatus('Getting video information...');
        const videoInfo = await getVideoInfo(videoId);
        
        // Display video info
        displayVideoInfo(videoInfo);
        
        // Simulate multi-format conversion process
        await simulateMultiFormatConversion(videoInfo);
        
        // Generate download items for all formats
        const downloadItems = generateDownloadItems(videoInfo, url);
        displayDownloadItems(downloadItems);
        
        // Hide progress section after conversion is complete
        progressSection.style.display = 'none';
        
        // Add to history
        addToHistory({
            url: url,
            videoInfo: videoInfo,
            timestamp: new Date().toISOString(),
            formats: downloadItems
        });
        
        showNotification('All formats converted successfully!', 'success');
        
    } catch (error) {
        showNotification(`Conversion failed: ${error.message}`, 'error');
        progressSection.style.display = 'none';
    } finally {
        isConverting = false;
        convertBtn.innerHTML = '<i class="fas fa-magic"></i> Convert';
        inputStatus.innerHTML = '<i class="fas fa-check-circle"></i>';
        inputStatus.className = 'input-status valid';
    }
}

function displayVideoInfo(videoInfo) {
    document.getElementById('video-thumbnail').src = videoInfo.thumbnail;
    document.getElementById('video-title').textContent = videoInfo.title;
    document.getElementById('video-duration').textContent = `Duration: ${videoInfo.duration} | Channel: ${videoInfo.channel}`;
}

function updateConversionStatus(status) {
    document.getElementById('conversion-status').textContent = status;
}

async function simulateMultiFormatConversion(videoInfo) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    const steps = [
        { progress: 20, status: 'Downloading video...' },
        { progress: 40, status: 'Extracting audio...' },
        { progress: 60, status: 'Converting format...' },
        { progress: 80, status: 'Optimizing quality...' },
        { progress: 100, status: 'Conversion complete!' }
    ];
    
    for (const step of steps) {
        await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 400));
        progressFill.style.width = `${step.progress}%`;
        progressText.textContent = `${step.progress}%`;
        updateConversionStatus(step.status);
    }
}

function calculateFileSize(duration, quality) {
    // Simulate file size calculation
    const durationSeconds = parseDuration(duration);
    const bitrateKbps = parseInt(quality);
    const sizeBytes = (durationSeconds * bitrateKbps * 1000) / 8;
    
    if (sizeBytes < 1024 * 1024) {
        return `${(sizeBytes / 1024).toFixed(1)} KB`;
    } else {
        return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
    }
}

function parseDuration(duration) {
    const parts = duration.split(':');
    return parts.reduce((acc, part) => acc * 60 + parseInt(part), 0);
}

function generateDownloadItems(videoInfo, url) {
    const duration = parseDuration(videoInfo.duration);
    
    return [
        // Audio formats
        {
            name: `${videoInfo.title} - 128kbps.mp3`,
            size: calculateFileSize(videoInfo.duration, '128'),
            url: `${url}#mp3-128`,
            type: 'audio'
        },
        {
            name: `${videoInfo.title} - 256kbps.mp3`,
            size: calculateFileSize(videoInfo.duration, '256'),
            url: `${url}#mp3-256`,
            type: 'audio'
        },
        {
            name: `${videoInfo.title} - 320kbps.mp3`,
            size: calculateFileSize(videoInfo.duration, '320'),
            url: `${url}#mp3-320`,
            type: 'audio'
        },
        // Video formats
        {
            name: `${videoInfo.title} - 360p.mp4`,
            size: calculateVideoFileSize(duration, '360'),
            url: `${url}#mp4-360`,
            type: 'video'
        },
        {
            name: `${videoInfo.title} - 720p.mp4`,
            size: calculateVideoFileSize(duration, '720'),
            url: `${url}#mp4-720`,
            type: 'video'
        },
        {
            name: `${videoInfo.title} - 1080p.mp4`,
            size: calculateVideoFileSize(duration, '1080'),
            url: `${url}#mp4-1080`,
            type: 'video'
        }
    ];
}

function calculateVideoFileSize(durationSeconds, quality) {
    // Video file size calculation (rough estimate)
    const videoBitrate = quality === '360' ? 800 : quality === '720' ? 2500 : 5000;
    const sizeBytes = (durationSeconds * (videoBitrate + 128) * 1000) / 8; // Video + audio bitrate
    
    if (sizeBytes < 1024 * 1024) {
        return `${(sizeBytes / 1024).toFixed(1)} KB`;
    } else {
        return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
    }
}

function displayDownloadItems(downloadItems) {
    const downloadsSection = document.getElementById('downloads-section');
    const audioDownloads = document.getElementById('audio-downloads');
    const videoDownloads = document.getElementById('video-downloads');
    
    // Clear previous downloads
    audioDownloads.innerHTML = '';
    videoDownloads.innerHTML = '';
    
    // Separate audio and video items
    const audioItems = downloadItems.filter(item => item.type === 'audio');
    const videoItems = downloadItems.filter(item => item.type === 'video');
    
    // Generate audio download items
    audioItems.forEach((item, index) => {
        audioDownloads.appendChild(createDownloadItem(item, 'audio', index));
    });
    
    // Generate video download items
    videoItems.forEach((item, index) => {
        videoDownloads.appendChild(createDownloadItem(item, 'video', index));
    });
    
    downloadsSection.style.display = 'block';
}

function createDownloadItem(item, type, index) {
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
        <button class="download-btn" onclick="downloadFile('${item.url}', '${item.name}')">
            <i class="fas fa-download"></i>
            Download
        </button>
    `;
    
    return div;
}

function downloadFile(url, filename) {
    // Create simulated download
    const link = document.createElement('a');
    link.href = '#';
    link.download = filename || 'download';
    
    // Show download notification
    showNotification(`Download started: ${filename || 'File'} (Demo version)`, 'success');
    
    // In a real application, this would be a real file download link
    console.log('Download file:', { url, filename });
}

// History functionality
function addToHistory(fileInfo) {
    conversionHistory.unshift(fileInfo);
    
    // Limit history count
    if (conversionHistory.length > 50) {
        conversionHistory = conversionHistory.slice(0, 50);
    }
    
    localStorage.setItem('conversionHistory', JSON.stringify(conversionHistory));
    loadConversionHistory();
}

function loadConversionHistory() {
    const historyContainer = document.getElementById('history-container');
    
    if (conversionHistory.length === 0) {
        historyContainer.innerHTML = `
            <div class="empty-history">
                <i class="fas fa-clock"></i>
                <p>No conversion history yet</p>
            </div>
        `;
        return;
    }
    
    historyContainer.innerHTML = conversionHistory.map(item => `
        <div class="history-item">
            <div class="history-info">
                <img src="${item.videoInfo.thumbnail}" alt="Thumbnail" class="history-thumbnail">
                <div class="history-details">
                    <h4>${item.videoInfo.title}</h4>
                    <p>6 formats: MP3 (128k, 256k, 320k) + MP4 (360p, 720p, 1080p)</p>
                    <small>Converted: ${new Date(item.timestamp).toLocaleString('en-US')}</small>
                </div>
            </div>
            <div class="history-actions">
                <button onclick="redownload('${item.url}')" class="redownload-btn">
                    <i class="fas fa-redo"></i>
                    Re-convert
                </button>
            </div>
        </div>
    `).join('');
    
    // Add history styles
    const style = document.createElement('style');
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
    
    if (!document.getElementById('history-styles')) {
        style.id = 'history-styles';
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
window.downloadFile = downloadFile;
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