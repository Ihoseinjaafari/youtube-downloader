#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Downloader Web UI - رابط وب برای دانلود از یوتیوب
اجرا روی سیستم محلی و باز شدن خودکار در مرورگر
"""

import yt_dlp
import os
import sys
import json
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_file
import socket

# ==================== تنظیمات پیش‌فرض ====================
DEFAULT_OUTPUT_DIR = "downloads"
DEFAULT_AUDIO_QUALITY = "320"
app = Flask(__name__)

# نام زبان‌ها
LANG_NAMES = {
    'en': 'English', 'fa': 'فارسی', 'ar': 'العربیه', 'fr': 'Français',
    'de': 'Deutsch', 'es': 'Español', 'tr': 'Türkçe', 'ja': '日本語',
    'ko': '한국어', 'zh': '中文', 'ru': 'Русский', 'pt': 'Português',
    'it': 'Italiano', 'nl': 'Nederlands', 'pl': 'Polski', 'hi': 'हिन्दी',
    'id': 'Bahasa Indonesia', 'th': 'ไทย', 'vi': 'Tiếng Việt',
    'en-US': 'English (US)', 'en-GB': 'English (UK)',
}

# ذخیره وضعیت دانلودها
download_status = {}
download_history = []

def get_lang_name(code):
    """نام خوانای زبان"""
    if code in LANG_NAMES:
        return LANG_NAMES[code]
    base = code.split('-')[0]
    if base in LANG_NAMES:
        return LANG_NAMES[base]
    return code


def format_duration(seconds):
    """فرمت کردن مدت زمان"""
    if not seconds:
        return "نامشخص"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"


def format_filesize(size_bytes):
    """فرمت کردن حجم فایل"""
    if not size_bytes:
        return "?"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_ydl_opts(cookie_file=None, cookie_browser=None, extra=None):
    """دریافت گزینه‌های yt-dlp"""
    opts = {
        'quiet': True,
        'no_warnings': False,
        'ignoreerrors': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
        'no_check_certificate': True,
        'socket_timeout': 60,
        'retries': 5,
        'extractor_retries': 3,
        'fragment_retries': 3,
        'retry_sleep': 2,
    }
    
    if cookie_file and os.path.exists(cookie_file):
        opts['cookiefile'] = cookie_file
    elif cookie_browser:
        opts['cookiesfrombrowser'] = (cookie_browser,)
    
    if extra:
        opts.update(extra)
    
    return opts


def progress_hook(d, download_id):
    """هوک برای نمایش پیشرفت دانلود"""
    global download_status
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        if total > 0:
            percent = (downloaded / total) * 100
            speed = d.get('speed', 0)
            speed_str = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "N/A"
            download_status[download_id]['progress'] = percent
            download_status[download_id]['speed'] = speed_str
            download_status[download_id]['status'] = 'downloading'
    elif d['status'] == 'finished':
        download_status[download_id]['progress'] = 100
        download_status[download_id]['status'] = 'processing'
    elif d['status'] == 'error':
        download_status[download_id]['status'] = 'error'


def get_video_info(url, cookie_file=None, cookie_browser=None):
    """دریافت اطلاعات ویدیو یا پلی‌لیست"""
    ydl_opts = get_ydl_opts(
        cookie_file=cookie_file,
        cookie_browser=cookie_browser,
        extra={
            'extract_flat': 'in_playlist',
            'playlistend': 1,
        }
    )
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info


def get_available_formats(url, cookie_file=None, cookie_browser=None):
    """دریافت فرمت‌های موجود برای یک ویدیو"""
    ydl_opts = get_ydl_opts(
        cookie_file=cookie_file,
        cookie_browser=cookie_browser,
        extra={
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
    )
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            
            # اگر پلی‌لیست باشد، اولین ویدیو را بررسی می‌کنیم
            if 'entries' in info and info['entries']:
                first_entry = info['entries'][0]
                if first_entry:
                    # دریافت اطلاعات کامل اولین ویدیو
                    video_url = f"https://www.youtube.com/watch?v={first_entry['id']}"
                    return get_available_formats(video_url, cookie_file, cookie_browser)
            
            formats = []
            if 'formats' in info:
                for fmt in info['formats']:
                    format_info = {
                        'format_id': fmt.get('format_id', ''),
                        'ext': fmt.get('ext', ''),
                        'resolution': fmt.get('resolution', fmt.get('height', '')),
                        'filesize': fmt.get('filesize', fmt.get('filesize_approx', 0)),
                        'vcodec': fmt.get('vcodec', 'none'),
                        'acodec': fmt.get('acodec', 'none'),
                        'fps': fmt.get('fps', ''),
                        'format_note': fmt.get('format_note', ''),
                    }
                    
                    # فقط فرمت‌هایی که ویدیو یا صدا دارند
                    if format_info['vcodec'] != 'none' or format_info['acodec'] != 'none':
                        formats.append(format_info)
            
            # اطلاعات کلی ویدیو
            video_data = {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'is_playlist': 'entries' in info,
                'playlist_count': info.get('playlist_count', 1) if 'entries' in info else 1,
                'formats': formats
            }
            
            return video_data
            
        except Exception as e:
            print(f"Error getting formats: {e}")
            return {'error': str(e)}


def download_thread(download_id, url, output_format, output_dir, playlist, subtitle_lang, cookie_file=None, cookie_browser=None):
    """دانلود در ترد جداگانه"""
    global download_status, download_history
    
    try:
        base_opts = {
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: progress_hook(d, download_id)],
            'extract_flat': False,
            'no_check_certificate': True,
            'socket_timeout': 30,
            'retries': 3,
        }
        
        # تنظیمات فرمت
        if output_format == "best":
            base_opts['format'] = 'bestvideo+bestaudio/best'
            base_opts['merge_output_format'] = 'mp4'
        elif output_format == "720p":
            base_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/bestvideo+bestaudio/best'
            base_opts['merge_output_format'] = 'mp4'
        elif output_format == "480p":
            base_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]/bestvideo+bestaudio/best'
            base_opts['merge_output_format'] = 'mp4'
        elif output_format == "360p":
            base_opts['format'] = 'bestvideo[height<=360]+bestaudio/best[height<=360]/bestvideo+bestaudio/best'
            base_opts['merge_output_format'] = 'mp4'
        elif output_format == "mp3":
            base_opts['format'] = 'bestaudio/best'
            base_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': DEFAULT_AUDIO_QUALITY
            }]
        elif output_format == "m4a":
            base_opts['format'] = 'bestaudio/best'
            base_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': DEFAULT_AUDIO_QUALITY
            }]
        else:
            base_opts['format'] = output_format
        
        # تنظیمات پلی‌لیست
        if playlist:
            base_opts['playlistend'] = None
        else:
            base_opts['playlistend'] = 1
        
        # تنظیمات زیرنویس
        if subtitle_lang and subtitle_lang != 'none':
            base_opts['writesubtitles'] = True
            base_opts['writeautomaticsub'] = True
            base_opts['subtitleslangs'] = [subtitle_lang]
            base_opts['subtitlesformat'] = 'vtt'
            if 'postprocessors' not in base_opts:
                base_opts['postprocessors'] = []
            base_opts['postprocessors'].append({
                'key': 'FFmpegSubtitlesConvertor',
                'format': 'srt'
            })
        
        ydl_opts = get_ydl_opts(
            cookie_file=cookie_file,
            cookie_browser=cookie_browser,
            extra=base_opts
        )
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        download_status[download_id]['status'] = 'completed'
        download_status[download_id]['progress'] = 100
        
        # افزودن به تاریخچه
        download_history.append({
            'id': download_id,
            'url': url,
            'format': output_format,
            'playlist': playlist,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'completed'
        })
        
    except Exception as e:
        download_status[download_id]['status'] = 'error'
        download_status[download_id]['error'] = str(e)
        download_history.append({
            'id': download_id,
            'url': url,
            'format': output_format,
            'playlist': playlist,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'error',
            'error': str(e)
        })


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader - دانلودر یوتیوب</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2em;
        }
        
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #333;
        }
        
        input[type="text"],
        input[type="url"],
        select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus,
        input[type="url"]:focus,
        select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .status-section {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .status-item {
            padding: 15px;
            background: white;
            border-radius: 8px;
            margin-bottom: 10px;
            border-right: 4px solid #667eea;
        }
        
        .status-item.completed {
            border-right-color: #28a745;
        }
        
        .status-item.error {
            border-right-color: #dc3545;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s;
        }
        
        .history-section {
            margin-top: 30px;
        }
        
        .history-item {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .badge-playlist {
            background: #ffc107;
            color: #000;
        }
        
        .badge-video {
            background: #17a2b8;
            color: white;
        }
        
        .info-box {
            background: #e7f3ff;
            border: 1px solid #b3d9ff;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube Downloader</h1>
        <p class="subtitle">دانلود ویدیو، صدا و پلی‌لیست از یوتیوب</p>
        
        <div class="info-box">
            <strong>💡 نکته:</strong> لینک ویدیو یا پلی‌لیست یوتیوب را وارد کنید. پس از وارد کردن لینک، کیفیت‌های موجود نمایش داده می‌شوند.
        </div>
        
        <form id="downloadForm">
            <div class="form-group">
                <label for="url">لینک یوتیوب:</label>
                <input type="url" id="url" name="url" placeholder="https://youtube.com/watch?v=..." required>
                <button type="button" id="checkBtn" class="btn" style="margin-top: 10px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">
                    بررسی لینک و نمایش کیفیت‌ها 🔍
                </button>
            </div>
            
            <div id="videoInfo" style="display: none; margin-bottom: 20px;">
                <div class="info-box" style="background: #f0f8ff; border-color: #667eea;">
                    <img id="videoThumbnail" src="" alt="Thumbnail" style="max-width: 200px; border-radius: 8px; display: block; margin-bottom: 10px;">
                    <h4 id="videoTitle" style="color: #333; margin-bottom: 5px;"></h4>
                    <p id="videoDetails" style="color: #666; font-size: 14px;"></p>
                    <div id="playlistInfo" style="display: none; color: #ffc107; font-weight: bold; margin-top: 10px;"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label for="format">فرمت دانلود:</label>
                <select id="format" name="format">
                    <option value="best">بهترین کیفیت (ویدیو + صدا)</option>
                    <option value="720p">720p HD</option>
                    <option value="480p">480p</option>
                    <option value="360p">360p</option>
                    <option value="mp3">فقط صدا (MP3)</option>
                    <option value="m4a">فقط صدا (M4A)</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="subtitle">زیرنویس:</label>
                <select id="subtitle" name="subtitle">
                    <option value="none">بدون زیرنویس</option>
                    <option value="fa">فارسی</option>
                    <option value="en">انگلیسی</option>
                    <option value="ar">عربی</option>
                    <option value="fr">فرانسوی</option>
                    <option value="de">آلمانی</option>
                    <option value="es">اسپانیایی</option>
                    <option value="tr">ترکی</option>
                </select>
            </div>
            
            <div class="checkbox-group">
                <input type="checkbox" id="playlist" name="playlist">
                <label for="playlist" style="margin: 0;">دانلود به عنوان پلی‌لیست</label>
            </div>
            
            <button type="submit" class="btn" id="downloadBtn">
                شروع دانلود 🚀
            </button>
        </form>
        
        <div class="status-section" id="statusSection" style="display: none;">
            <h3>وضعیت دانلودها:</h3>
            <div id="statusList"></div>
        </div>
        
        <div class="history-section" id="historySection" style="display: none;">
            <h3>تاریخچه دانلودها:</h3>
            <div id="historyList"></div>
        </div>
    </div>
    
    <script>
        let refreshInterval;
        
        document.getElementById('downloadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            const btn = document.getElementById('downloadBtn');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> در حال پردازش...';
            
            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('statusSection').style.display = 'block';
                    document.getElementById('historySection').style.display = 'block';
                    
                    // شروع به‌روزرسانی وضعیت
                    refreshInterval = setInterval(refreshStatus, 1000);
                } else {
                    alert('خطا: ' + result.error);
                }
            } catch (error) {
                alert('خطا در ارتباط با سرور');
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'شروع دانلود 🚀';
            }
        });
        
        async function refreshStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const statusList = document.getElementById('statusList');
                statusList.innerHTML = '';
                
                let hasActive = false;
                
                for (const [id, status] of Object.entries(data.downloads)) {
                    hasActive = hasActive || (status.status === 'downloading' || status.status === 'processing');
                    
                    const div = document.createElement('div');
                    div.className = `status-item ${status.status}`;
                    
                    let statusText = {
                        'downloading': '⏳ در حال دانلود',
                        'processing': '⚙️ در حال پردازش',
                        'completed': '✅ کامل شد',
                        'error': '❌ خطا'
                    }[status.status] || status.status;
                    
                    div.innerHTML = `
                        <div><strong>${statusText}</strong></div>
                        <div style="font-size: 14px; color: #666;">${status.url}</div>
                        ${status.progress !== undefined ? `
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${status.progress}%"></div>
                            </div>
                            <div style="font-size: 12px; margin-top: 5px;">${status.progress.toFixed(1)}% - ${status.speed || ''}</div>
                        ` : ''}
                        ${status.error ? `<div style="color: red; font-size: 14px; margin-top: 5px;">${status.error}</div>` : ''}
                    `;
                    
                    statusList.appendChild(div);
                }
                
                if (!hasActive && refreshInterval) {
                    clearInterval(refreshInterval);
                    refreshInterval = null;
                }
                
                // به‌روزرسانی تاریخچه
                if (data.history && data.history.length > 0) {
                    const historyList = document.getElementById('historyList');
                    historyList.innerHTML = '';
                    
                    data.history.slice(-10).reverse().forEach(item => {
                        const div = document.createElement('div');
                        div.className = 'history-item';
                        const badgeClass = item.playlist ? 'badge-playlist' : 'badge-video';
                        const badgeText = item.playlist ? 'پلی‌لیست' : 'ویدیو';
                        div.innerHTML = `
                            <span class="badge ${badgeClass}">${badgeText}</span>
                            <strong>${item.format}</strong> - 
                            ${item.timestamp} - 
                            <span style="color: ${item.status === 'completed' ? 'green' : 'red'}">${item.status}</span>
                        `;
                        historyList.appendChild(div);
                    });
                }
                
            } catch (error) {
                console.error('Error refreshing status:', error);
            }
        }
        
        // بررسی لینک و نمایش اطلاعات ویدیو
        document.getElementById('checkBtn').addEventListener('click', async function() {
            const url = document.getElementById('url').value;
            
            if (!url) {
                alert('لطفاً لینک یوتیوب را وارد کنید');
                return;
            }
            
            const btn = document.getElementById('checkBtn');
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> در حال بررسی...';
            
            try {
                const response = await fetch('/api/formats', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    const data = result.data;
                    
                    // نمایش اطلاعات ویدیو
                    document.getElementById('videoInfo').style.display = 'block';
                    document.getElementById('videoTitle').textContent = data.title || 'عنوان نامشخص';
                    
                    const duration = formatDuration(data.duration);
                    document.getElementById('videoDetails').textContent = 
                        `👤 ${data.uploader || 'نامشخص'} | ⏱️ ${duration}`;
                    
                    // نمایش تامبنیل
                    if (data.thumbnail) {
                        document.getElementById('videoThumbnail').src = data.thumbnail;
                        document.getElementById('videoThumbnail').style.display = 'block';
                    } else {
                        document.getElementById('videoThumbnail').style.display = 'none';
                    }
                    
                    // اگر پلی‌لیست باشد
                    if (data.is_playlist) {
                        document.getElementById('playlistInfo').style.display = 'block';
                        document.getElementById('playlistInfo').textContent = 
                            `📋 این یک پلی‌لیست با ${data.playlist_count} ویدیو است`;
                        
                        // فعال کردن چک‌باکس پلی‌لیست
                        document.getElementById('playlist').checked = true;
                    } else {
                        document.getElementById('playlistInfo').style.display = 'none';
                    }
                    
                    // افزودن فرمت‌های موجود به سلکت (اختیاری - برای کاربران پیشرفته)
                    // فعلاً فقط اطلاعات را نمایش می‌دهیم
                    
                } else {
                    alert('خطا در دریافت اطلاعات: ' + result.error);
                    document.getElementById('videoInfo').style.display = 'none';
                }
            } catch (error) {
                alert('خطا در ارتباط با سرور');
                document.getElementById('videoInfo').style.display = 'none';
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        });
        
        function formatDuration(seconds) {
            if (!seconds) return 'نامشخص';
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            if (h > 0) {
                return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
            }
            return `${m}:${s.toString().padStart(2, '0')}`;
        }
        
        // بارگذاری اولیه تاریخچه
        refreshStatus();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.json
    url = data.get('url')
    output_format = data.get('format', 'best')
    playlist = data.get('playlist', False)
    subtitle_lang = data.get('subtitle', 'none')
    output_dir = data.get('output_dir', DEFAULT_OUTPUT_DIR)
    
    if not url:
        return jsonify({'success': False, 'error': 'URL الزامی است'})
    
    # ایجاد ID منحصر به فرد
    download_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # ایجاد پوشه دانلود
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # شروع دانلود در ترد جداگانه
    download_status[download_id] = {
        'id': download_id,
        'url': url,
        'status': 'starting',
        'progress': 0,
        'speed': ''
    }
    
    thread = threading.Thread(
        target=download_thread,
        args=(download_id, url, output_format, output_dir, playlist, subtitle_lang)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'download_id': download_id,
        'message': 'دانلود شروع شد'
    })


@app.route('/api/status')
def api_status():
    return jsonify({
        'downloads': download_status,
        'history': download_history[-20:]  # آخرین ۲۰ مورد
    })


@app.route('/api/formats', methods=['POST'])
def api_formats():
    """دریافت فرمت‌های موجود برای یک URL"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL الزامی است'})
    
    try:
        video_info = get_available_formats(url)
        
        if 'error' in video_info:
            return jsonify({'success': False, 'error': video_info['error']})
        
        return jsonify({
            'success': True,
            'data': video_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def find_available_port(start_port=5000):
    """پیدا کردن پورت آزاد"""
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                port += 1
    return start_port


def open_browser(port):
    """باز کردن مرورگر بعد از آماده شدن سرور"""
    import time
    time.sleep(2)  # صبر برای راه‌اندازی سرور
    webbrowser.open(f'http://localhost:{port}')


def main():
    print("=" * 60)
    print("🎬 YouTube Downloader Web UI")
    print("=" * 60)
    
    # پیدا کردن پورت آزاد
    port = find_available_port()
    print(f"🌐 آدرس برنامه: http://localhost:{port}")
    print("⏳ در حال راه‌اندازی...")
    print("=" * 60)
    
    # باز کردن خودکار مرورگر
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    # اجرای سرور
    app.run(host='localhost', port=port, debug=False, threaded=True)


if __name__ == '__main__':
    main()
