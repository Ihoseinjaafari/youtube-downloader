#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Downloader CLI - دانلودر خط فرمان یوتیوب
قابلیت دانلود ویدیو، صدا، زیرنویس و پلی‌لیست‌ها
"""

import yt_dlp
import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

# ==================== تنظیمات پیش‌فرض ====================
DEFAULT_OUTPUT_DIR = "downloads"
DEFAULT_AUDIO_QUALITY = "320"

# نام زبان‌ها
LANG_NAMES = {
    'en': 'English', 'fa': 'فارسی', 'ar': 'العربیه', 'fr': 'Français',
    'de': 'Deutsch', 'es': 'Español', 'tr': 'Türkçe', 'ja': '日本語',
    'ko': '한국어', 'zh': '中文', 'ru': 'Русский', 'pt': 'Português',
    'it': 'Italiano', 'nl': 'Nederlands', 'pl': 'Polski', 'hi': 'हिन्दी',
    'id': 'Bahasa Indonesia', 'th': 'ไทย', 'vi': 'Tiếng Việt',
    'en-US': 'English (US)', 'en-GB': 'English (UK)',
}


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
        'quiet': False,
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
        'socket_timeout': 30,
        'retries': 3,
    }
    
    if cookie_file and os.path.exists(cookie_file):
        opts['cookiefile'] = cookie_file
    elif cookie_browser:
        opts['cookiesfrombrowser'] = (cookie_browser,)
    
    if extra:
        opts.update(extra)
    
    return opts


def progress_hook(d):
    """هوک برای نمایش پیشرفت دانلود"""
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        if total > 0:
            percent = (downloaded / total) * 100
            speed = d.get('speed', 0)
            speed_str = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "N/A"
            print(f"\rپیشرفت: {percent:5.1f}% | سرعت: {speed_str}", end='', flush=True)
    elif d['status'] == 'finished':
        print("\r✓ دانلود کامل شد                    ")


def get_video_info(url, cookie_file=None, cookie_browser=None):
    """دریافت اطلاعات ویدیو یا پلی‌لیست"""
    ydl_opts = get_ydl_opts(
        cookie_file=cookie_file,
        cookie_browser=cookie_browser,
        extra={
            'extract_flat': False,
            'playlistend': 1,  # فقط اولین آیتم برای دریافت اطلاعات
        }
    )
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info


def download_content(url, output_format="best", output_dir=DEFAULT_OUTPUT_DIR,
                     cookie_file=None, cookie_browser=None, playlist=False,
                     subtitle_lang=None, extract_audio_only=False):
    """دانلود محتوا (ویدیو تکی یا پلی‌لیست)"""
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"پوشه دانلود ساخته شد: {output_dir}")
    
    # تنظیم فرمت دانلود
    base_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'extract_flat': False,
        'no_check_certificate': True,
        'socket_timeout': 30,
        'retries': 3,
        'ratelimit': None,
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
        # فرمت سفارشی
        base_opts['format'] = output_format
    
    # تنظیمات پلی‌لیست
    if playlist:
        base_opts['playlistend'] = None  # دانلود کل پلی‌لیست
        print("📋 در حال دانلود پلی‌لیست...")
    else:
        # فقط یک ویدیو
        base_opts['playlistend'] = 1
    
    # تنظیمات زیرنویس
    if subtitle_lang:
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
    
    # اضافه کردن کوکی‌ها
    ydl_opts = get_ydl_opts(
        cookie_file=cookie_file,
        cookie_browser=cookie_browser,
        extra=base_opts
    )
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("\n✓ دانلود با موفقیت انجام شد!")
        return True
    except Exception as e:
        print(f"\n✗ خطا در دانلود: {str(e)}")
        return False


def list_available_formats(url, cookie_file=None, cookie_browser=None):
    """نمایش فرمت‌های موجود برای دانلود"""
    ydl_opts = get_ydl_opts(
        cookie_file=cookie_file,
        cookie_browser=cookie_browser,
        extra={'extract_flat': False}
    )
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        print("\n" + "="*60)
        print(f"عنوان: {info.get('title', 'نامشخص')}")
        print(f"آپلودر: {info.get('uploader', 'نامشخص')}")
        print(f"مدت: {format_duration(info.get('duration'))}")
        print(f"تاریخ آپلود: {info.get('upload_date', 'نامشخص')}")
        print("="*60)
        
        if 'formats' in info:
            video_formats = []
            audio_formats = []
            
            for f in info['formats']:
                if f.get('vcodec') != 'none' and f.get('height'):
                    video_formats.append({
                        'id': f.get('format_id', ''),
                        'ext': f.get('ext', ''),
                        'resolution': f.get('resolution', 'audio only'),
                        'height': f.get('height'),
                        'filesize': f.get('filesize') or f.get('filesize_approx'),
                        'vcodec': f.get('vcodec', 'none'),
                    })
                elif f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    audio_formats.append({
                        'id': f.get('format_id', ''),
                        'ext': f.get('ext', ''),
                        'abr': f.get('abr'),
                        'filesize': f.get('filesize') or f.get('filesize_approx'),
                        'acodec': f.get('acodec', 'none'),
                    })
            
            print("\n📹 فرمت‌های ویدیویی:")
            print("-" * 60)
            seen = set()
            for f in sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True):
                h = f.get('height')
                if h and h not in seen:
                    seen.add(h)
                    print(f"  {h}p - {f['ext']} - {format_filesize(f['filesize'])} - {f['vcodec'][:20]}")
            
            print("\n🎵 فرمت‌های صوتی:")
            print("-" * 60)
            for f in audio_formats[:10]:
                print(f"  {f['id']} - {f['ext']} - {f['abr']}kbps - {format_filesize(f['filesize'])}")
        
        # نمایش زیرنویس‌های موجود
        subs = info.get('subtitles', {})
        auto_subs = info.get('automatic_captions', {})
        
        if subs or auto_subs:
            print("\n📝 زیرنویس‌های موجود:")
            print("-" * 60)
            
            all_langs = {}
            for lang, val in subs.items():
                all_langs[lang] = {'type': 'manual', 'name': val[0].get('name', lang) if val else lang}
            for lang, val in auto_subs.items():
                if lang not in all_langs:
                    all_langs[lang] = {'type': 'auto', 'name': val[0].get('name', lang) if val else lang}
            
            for code, data in all_langs.items():
                type_label = "دستی ✓" if data['type'] == 'manual' else "خودکار"
                name = get_lang_name(code)
                print(f"  {name} ({code}) - {type_label}")
        
        print("="*60)


def extract_transcript(url, lang='en', cookie_file=None, cookie_browser=None):
    """استخراج زیرنویس از ویدیو"""
    import tempfile
    import shutil
    
    tmp_dir = tempfile.mkdtemp()
    
    opts = get_ydl_opts(
        cookie_file=cookie_file,
        cookie_browser=cookie_browser,
        extra={
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [lang],
            'subtitlesformat': 'json3',
            'outtmpl': os.path.join(tmp_dir, '%(id)s.%(ext)s'),
        }
    )
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        
        video_id = info.get('id', '')
        transcript_entries = []
        
        for fname in os.listdir(tmp_dir):
            if fname.endswith('.json3') and video_id in fname:
                filepath = os.path.join(tmp_dir, fname)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                events = data.get('events', [])
                for event in events:
                    segs = event.get('segs', [])
                    if not segs:
                        continue
                    
                    text = ''.join(seg.get('utf8', '') for seg in segs)
                    text = text.strip()
                    
                    if not text or text == '\n':
                        continue
                    
                    start_ms = event.get('tStartMs', 0)
                    start_sec = start_ms / 1000
                    minutes = int(start_sec // 60)
                    seconds = int(start_sec % 60)
                    
                    transcript_entries.append({
                        'time': f"{minutes:02d}:{seconds:02d}",
                        'time_sec': start_sec,
                        'text': text.replace('\n', ' '),
                    })
                break
        
        return transcript_entries, info
    
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def save_transcript(entries, output_file, with_timestamps=False):
    """ذخیره زیرنویس در فایل"""
    with open(output_file, 'w', encoding='utf-8') as f:
        if with_timestamps:
            for e in entries:
                f.write(f"[{e['time']}] {e['text']}\n")
        else:
            for e in entries:
                f.write(f"{e['text']}\n")
    print(f"✓ زیرنویس ذخیره شد: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Downloader CLI - دانلودر خط فرمان یوتیوب",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
مثال‌ها:
  %(prog)s https://youtube.com/watch?v=xxx
  %(prog)s -p https://youtube.com/playlist?list=xxx
  %(prog)s -f mp3 https://youtube.com/watch?v=xxx
  %(prog)s --list-formats https://youtube.com/watch?v=xxx
  %(prog)s --transcript fa https://youtube.com/watch?v=xxx
        """
    )
    
    parser.add_argument('url', nargs='?', help='لینک یوتیوب (ویدیو یا پلی‌لیست)')
    parser.add_argument('-f', '--format', choices=['best', '720p', '480p', '360p', 'mp3', 'm4a'],
                       default='best', help='فرمت دانلود (پیش‌فرض: best)')
    parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT_DIR,
                       help=f'پوشه خروجی (پیش‌فرض: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('-p', '--playlist', action='store_true',
                       help='دانلود به عنوان پلی‌لیست')
    parser.add_argument('--list-formats', action='store_true',
                       help='نمایش فرمت‌های موجود بدون دانلود')
    parser.add_argument('--transcript', metavar='LANG',
                       help='استخراج زیرنویس (کد زبان مثل: fa, en)')
    parser.add_argument('--transcript-only', action='store_true',
                       help='فقط استخراج زیرنویس بدون دانلود ویدیو')
    parser.add_argument('--cookie-file', metavar='FILE',
                       help='فایل cookies.txt برای احراز هویت')
    parser.add_argument('--cookie-browser', choices=['chrome', 'firefox', 'edge', 'brave', 'opera'],
                       help='خواندن کوکی از مرورگر')
    parser.add_argument('--audio-quality', default='320',
                       help='کیفیت صدا برای MP3/M4A (پیش‌فرض: 320)')
    
    args = parser.parse_args()
    
    if not args.url:
        parser.print_help()
        sys.exit(1)
    
    global DEFAULT_AUDIO_QUALITY
    DEFAULT_AUDIO_QUALITY = args.audio_quality
    
    # نمایش فرمت‌ها
    if args.list_formats:
        print("در حال دریافت اطلاعات...")
        list_available_formats(args.url, args.cookie_file, args.cookie_browser)
        sys.exit(0)
    
    # استخراج زیرنویس
    if args.transcript:
        print(f"در حال استخراج زیرنویس به زبان {args.transcript}...")
        entries, info = extract_transcript(args.url, args.transcript, 
                                          args.cookie_file, args.cookie_browser)
        
        if entries:
            video_id = info.get('id', 'video')
            output_file = f"transcript_{video_id}.txt"
            save_transcript(entries, output_file, with_timestamps=True)
            print(f"✓ {len(entries)} خط متن استخراج شد")
        else:
            print("✗ زیرنویسی یافت نشد")
        
        if args.transcript_only:
            sys.exit(0)
    
    # دانلود
    print(f"در حال دانلود از: {args.url}")
    if args.playlist:
        print("📋 حالت پلی‌لیست فعال است")
    
    success = download_content(
        url=args.url,
        output_format=args.format,
        output_dir=args.output,
        cookie_file=args.cookie_file,
        cookie_browser=args.cookie_browser,
        playlist=args.playlist,
        subtitle_lang=args.transcript if not args.transcript_only else None
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
