# app.py — نسخه نهایی با بخش متن ویدیو

import streamlit as st
import yt_dlp
import os
import json
import tempfile
import re
from datetime import datetime

# ==================== تنظیمات صفحه ====================
st.set_page_config(
    page_title="دانلودر یوتیوب",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================== استایل ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800;900&display=swap');

    * { font-family: 'Vazirmatn', sans-serif !important; }

    .stApp {
        background: linear-gradient(135deg, #0a0b0f 0%, #12141a 50%, #0d0f14 100%);
    }
    .main .block-container { max-width: 700px; padding-top: 3rem; }

    .hero-header { text-align: center; padding: 2rem 0; margin-bottom: 2rem; }
    .hero-header h1 {
        font-size: 2.5rem; font-weight: 900;
        background: linear-gradient(135deg, #6c5ce7, #00cec9);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; margin-bottom: 0.5rem;
    }
    .hero-header p { color: #9694a8; font-size: 1rem; }

    .video-card {
        background: rgba(26, 29, 38, 0.8);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px; padding: 1.5rem; margin: 1.5rem 0;
    }
    .video-card h3 { color: #e8e6f0; font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; }
    .video-meta { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 0.8rem; }
    .meta-tag {
        background: rgba(108, 92, 231, 0.1); color: #a29bfe;
        padding: 4px 14px; border-radius: 100px; font-size: 0.8rem;
        font-weight: 500; border: 1px solid rgba(108, 92, 231, 0.15);
    }
    .meta-tag.green {
        background: rgba(0, 206, 201, 0.1); color: #00cec9;
        border-color: rgba(0, 206, 201, 0.15);
    }
    .meta-tag.orange {
        background: rgba(225, 112, 85, 0.1); color: #e17055;
        border-color: rgba(225, 112, 85, 0.15);
    }

    .error-box {
        background: rgba(255, 107, 107, 0.08);
        border: 1px solid rgba(255, 107, 107, 0.2);
        border-radius: 12px; padding: 1.2rem 1.5rem; margin: 1rem 0;
    }
    .error-box h4 { color: #ff6b6b; margin-bottom: 0.5rem; font-size: 0.95rem; }
    .error-box ol { color: #e8e6f0; font-size: 0.85rem; padding-right: 1.2rem; }
    .error-box li { margin-bottom: 0.4rem; }
    .error-box code {
        background: rgba(108, 92, 231, 0.15); color: #a29bfe;
        padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;
    }

    .transcript-box {
        background: rgba(18, 20, 26, 0.8);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        max-height: 500px;
        overflow-y: auto;
        line-height: 2;
    }
    .transcript-line {
        padding: 4px 0;
        border-bottom: 1px solid rgba(255,255,255,0.02);
        transition: background 0.2s;
    }
    .transcript-line:hover {
        background: rgba(108, 92, 231, 0.05);
    }
    .transcript-time {
        color: #6c5ce7;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 8px;
        cursor: pointer;
        font-family: monospace;
    }
    .transcript-text {
        color: #e8e6f0;
        font-size: 0.9rem;
    }

    .transcript-stats {
        display: flex; gap: 1rem; margin: 1rem 0; flex-wrap: wrap;
    }
    .t-stat {
        background: rgba(108, 92, 231, 0.06);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 10px; padding: 0.8rem 1.2rem; flex: 1; text-align: center;
    }
    .t-stat .val { font-size: 1.3rem; font-weight: 800; color: #e8e6f0; }
    .t-stat .lbl { font-size: 0.7rem; color: #5c5a6e; margin-top: 2px; }

    .formats-table {
        width: 100%; border-collapse: collapse;
        margin: 1rem 0; font-size: 0.8rem;
    }
    .formats-table th {
        background: rgba(108, 92, 231, 0.1); color: #a29bfe;
        padding: 8px 12px; text-align: right;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .formats-table td {
        padding: 6px 12px; color: #9694a8;
        border-bottom: 1px solid rgba(255,255,255,0.03);
    }

    .stButton > button {
        background: linear-gradient(135deg, #6c5ce7, #8b7cf7) !important;
        color: white !important; border: none !important;
        border-radius: 100px !important; padding: 0.6rem 2rem !important;
        font-family: 'Vazirmatn', sans-serif !important;
        font-weight: 600 !important; font-size: 0.95rem !important;
        box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3) !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(108, 92, 231, 0.4) !important;
    }

    .stTextInput > div > div > input {
        background: rgba(26, 29, 38, 0.8) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important; color: #e8e6f0 !important;
        font-family: 'Vazirmatn', sans-serif !important;
        padding: 0.8rem 1rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6c5ce7 !important;
        box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.2) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0; background: rgba(10, 11, 15, 0.5);
        border-radius: 12px; padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-family: 'Vazirmatn', sans-serif !important;
        font-weight: 500; color: #9694a8; padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(108, 92, 231, 0.15) !important;
        color: #a29bfe !important;
    }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] { display: none; }

    .stProgress > div > div > div {
        background: linear-gradient(90deg, #6c5ce7, #00cec9) !important;
        border-radius: 100px !important;
    }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(108, 92, 231, 0.3); border-radius: 100px;
    }

    .history-item {
        background: rgba(26, 29, 38, 0.5);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.5rem;
    }
    .history-title { color: #e8e6f0; font-weight: 600; font-size: 0.85rem; }
    .history-time { color: #5c5a6e; font-size: 0.75rem; }
    .footer { text-align: center; padding: 2rem 0 1rem; color: #5c5a6e; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


# ==================== سشن استیت ====================
defaults = {
    'download_progress': 0,
    'video_info': None,
    'available_formats': [],
    'history': [],
    'cookie_method': 'none',
    'cookie_file_path': '',
    'cookie_browser': 'chrome',
    'current_url': '',
    'transcript_data': None,
    'transcript_langs': [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ==================== توابع کمکی عمومی ====================
def format_duration(seconds):
    if not seconds:
        return "نامشخص"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"


def format_view_count(count):
    if not count:
        return "نامشخص"
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


def format_filesize(size_bytes):
    if not size_bytes:
        return "?"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_ydl_opts(extra=None):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
    }
    method = st.session_state['cookie_method']
    if method == 'file':
        path = st.session_state['cookie_file_path']
        if path and os.path.exists(path):
            opts['cookiefile'] = path
    elif method == 'browser':
        opts['cookiesfrombrowser'] = (st.session_state.get('cookie_browser', 'chrome'),)
    if extra:
        opts.update(extra)
    return opts


# ==================== توابع اطلاعات ویدیو ====================
def get_video_info(url):
    ydl_opts = get_ydl_opts()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info is None:
            raise Exception("نتوانست اطلاعات ویدیو را دریافت کند")
        formats = []
        if 'formats' in info:
            for f in info['formats']:
                formats.append({
                    'id': f.get('format_id', ''),
                    'ext': f.get('ext', ''),
                    'resolution': f.get('resolution', 'audio only'),
                    'height': f.get('height'),
                    'width': f.get('width'),
                    'fps': f.get('fps'),
                    'vcodec': f.get('vcodec', 'none'),
                    'acodec': f.get('acodec', 'none'),
                    'filesize': f.get('filesize') or f.get('filesize_approx'),
                    'tbr': f.get('tbr'),
                    'note': f.get('format_note', ''),
                })
        st.session_state['available_formats'] = formats

        # ذخیره زیرنویس‌های موجود
        subs = info.get('subtitles', {})
        auto_subs = info.get('automatic_captions', {})
        available_langs = {}

        for lang, val in subs.items():
            available_langs[lang] = {'type': 'manual', 'name': val[0].get('name', lang) if val else lang}

        for lang, val in auto_subs.items():
            if lang not in available_langs:
                available_langs[lang] = {'type': 'auto', 'name': val[0].get('name', lang) if val else lang}

        st.session_state['transcript_langs'] = available_langs
        return info


# ==================== توابع دانلود ====================
def download_video(url, format_id_or_option, output_path="downloads"):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    base_opts = get_ydl_opts({
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
    })

    if format_id_or_option.startswith('id:'):
        fid = format_id_or_option[3:]
        base_opts['format'] = f'{fid}+bestaudio/{fid}/best'
    elif format_id_or_option == "best_video":
        base_opts['format'] = 'bestvideo+bestaudio/best'
        base_opts['merge_output_format'] = 'mp4'
    elif format_id_or_option == "720p":
        base_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/bestvideo+bestaudio/best'
        base_opts['merge_output_format'] = 'mp4'
    elif format_id_or_option == "480p":
        base_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]/bestvideo+bestaudio/best'
        base_opts['merge_output_format'] = 'mp4'
    elif format_id_or_option == "360p":
        base_opts['format'] = 'bestvideo[height<=360]+bestaudio/best[height<=360]/bestvideo+bestaudio/best'
        base_opts['merge_output_format'] = 'mp4'
    elif format_id_or_option == "audio_mp3":
        base_opts['format'] = 'bestaudio/best'
        base_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
    elif format_id_or_option == "audio_m4a":
        base_opts['format'] = 'bestaudio/best'
    else:
        base_opts['format'] = 'best'

    with yt_dlp.YoutubeDL(base_opts) as ydl:
        ydl.download([url])


def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        if total > 0:
            st.session_state['download_progress'] = downloaded / total
    elif d['status'] == 'finished':
        st.session_state['download_progress'] = 1.0
        st.session_state['download_filename'] = d.get('filename', '')


# ==================== توابع استخراج متن ویدیو ====================

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
    # حذف بخش بعد از خط تیره
    base = code.split('-')[0]
    if base in LANG_NAMES:
        return LANG_NAMES[base]
    return code


def extract_transcript_ytdlp(url, lang='en'):
    """استخراج زیرنویس با yt-dlp"""
    tmp_dir = tempfile.mkdtemp()

    opts = get_ydl_opts({
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang],
        'subtitlesformat': 'json3',
        'outtmpl': os.path.join(tmp_dir, '%(id)s.%(ext)s'),
    })

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    video_id = info.get('id', '')

    # جستجوی فایل زیرنویس
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

    # پاک کردن فایل‌های موقت
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    return transcript_entries, info


def extract_transcript_vtt(url, lang='en'):
    """استخراج زیرنویس با فرمت VTT (جایگزین)"""
    tmp_dir = tempfile.mkdtemp()

    opts = get_ydl_opts({
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang],
        'subtitlesformat': 'vtt',
        'outtmpl': os.path.join(tmp_dir, '%(id)s.%(ext)s'),
    })

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    video_id = info.get('id', '')
    entries = []

    for fname in os.listdir(tmp_dir):
        if fname.endswith('.vtt') and video_id in fname:
            filepath = os.path.join(tmp_dir, fname)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # پارس VTT
            pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}\s*\n(.+?)(?:\n\n|\Z)'
            matches = re.findall(pattern, content, re.DOTALL)

            seen_texts = set()
            for time_str, text in matches:
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                clean_text = clean_text.replace('\n', ' ')

                if not clean_text or clean_text in seen_texts:
                    continue
                seen_texts.add(clean_text)

                parts = time_str.split(':')
                minutes = int(parts[1])
                seconds = int(float(parts[2]))

                entries.append({
                    'time': f"{minutes:02d}:{seconds:02d}",
                    'time_sec': int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2]),
                    'text': clean_text,
                })
            break

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    return entries, info


def get_transcript(url, lang='en'):
    """دریافت متن ویدیو — اول json3، بعد vtt"""
    try:
        entries, info = extract_transcript_ytdlp(url, lang)
        if entries:
            return entries, info
    except Exception:
        pass

    try:
        entries, info = extract_transcript_vtt(url, lang)
        if entries:
            return entries, info
    except Exception:
        pass

    return [], None


def transcript_to_plain_text(entries):
    """تبدیل به متن ساده"""
    return '\n'.join(e['text'] for e in entries)


def transcript_to_timestamped(entries):
    """تبدیل به متن با زمان"""
    return '\n'.join(f"[{e['time']}] {e['text']}" for e in entries)


def count_words(text):
    """شمارش کلمات (فارسی و انگلیسی)"""
    # کلمات انگلیسی
    en_words = len(re.findall(r'[a-zA-Z]+', text))
    # کلمات فارسی/عربی (هر گروه حروف متوالی)
    fa_words = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F]+', text))
    return en_words + fa_words


# ==================== سایر توابع ====================
def add_to_history(title, url):
    st.session_state['history'].insert(0, {
        'title': title, 'url': url,
        'time': datetime.now().strftime('%H:%M')
    })
    st.session_state['history'] = st.session_state['history'][:10]


def show_cookie_error():
    st.markdown("""
    <div class="error-box">
        <h4>خطای تشخیص ربات توسط یوتیوب</h4>
        <ol>
            <li>از نوار کناری (<strong>≡</strong>) → <strong>فایل کوکی</strong> → آپلود cookies.txt</li>
            <li>یا <strong>کوکی مرورگر</strong> (مرورگر باید بسته باشه)</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)


def show_format_error():
    st.markdown("""
    <div class="error-box">
        <h4>فرمت درخواست‌شده موجود نیست</h4>
        <p style="color:#9694a8; font-size:0.85rem;">
            از گزینه «بهترین کیفیت» استفاده کن یا فرمت دیگه‌ای امتحان کن.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_formats_table(formats):
    if not formats:
        return
    video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('height')]
    audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']

    seen = set()
    unique = []
    for f in sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True):
        h = f.get('height')
        if h and h not in seen:
            seen.add(h)
            unique.append(f)

    st.markdown(f"""
    <table class="formats-table">
        <tr><th>کیفیت</th><th>فرمت</th><th>حجم</th><th>کدک</th></tr>
        {''.join(f"""<tr><td>{f.get('height','?')}p</td><td>{f.get('ext','?')}</td>
        <td>{format_filesize(f.get('filesize'))}</td><td>{f.get('vcodec','?')[:20]}</td></tr>""" for f in unique[:10])}
    </table>
    """, unsafe_allow_html=True)

    if audio_formats:
        st.markdown(f"""
        <table class="formats-table">
            <tr><th>کیفیت</th><th>فرمت</th><th>حجم</th><th>کدک</th></tr>
            {''.join(f"""<tr><td>{f.get('tbr','?')}kbps</td><td>{f.get('ext','?')}</td>
            <td>{format_filesize(f.get('filesize'))}</td><td>{f.get('acodec','?')[:20]}</td></tr>""" for f in audio_formats[:8])}
        </table>
        """, unsafe_allow_html=True)


# ==================== هدر ====================
st.markdown("""
<div class="hero-header">
    <h1>دانلودر یوتیوب</h1>
    <p>دانلود ویدیو، صدا و استخراج متن از یوتیوب</p>
</div>
""", unsafe_allow_html=True)


# ==================== نوار کناری ====================
with st.sidebar:
    st.markdown("### تنظیمات")
    st.markdown("---")

    cookie_method = st.radio(
        "روش احراز هویت",
        options=['none', 'file', 'browser'],
        format_func=lambda x: {'none': 'بدون کوکی', 'file': 'فایل cookies.txt', 'browser': 'خواندن از مرورگر'}[x],
        index=['none', 'file', 'browser'].index(st.session_state['cookie_method'])
    )
    st.session_state['cookie_method'] = cookie_method

    if cookie_method == 'file':
        st.markdown("افزونه **Get cookies.txt LOCALLY** → youtube.com → Export")
        uploaded = st.file_uploader("آپلود cookies.txt", type=['txt'])
        if uploaded:
            path = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
            with open(path, "wb") as f:
                f.write(uploaded.getvalue())
            st.session_state['cookie_file_path'] = path
            st.success("آماده ✓")

    elif cookie_method == 'browser':
        browsers = {'chrome': 'Chrome', 'firefox': 'Firefox', 'edge': 'Edge', 'brave': 'Brave', 'opera': 'Opera'}
        st.session_state['cookie_browser'] = st.selectbox("مرورگر", list(browsers.keys()), format_func=lambda x: browsers[x])
        st.warning("مرورگر باید بسته باشه")

    st.markdown("---")
    st.markdown('<div style="color:#5c5a6e;font-size:0.75rem;text-align:center">فقط استفاده شخصی</div>', unsafe_allow_html=True)


# ==================== تب‌ها ====================
tab1, tab2, tab3, tab4 = st.tabs(["دانلود ویدیو", "متن ویدیو", "دانلود دسته‌ای", "تاریخچه"])


# ==================== تب ۱: دانلود ویدیو ====================
with tab1:
    url = st.text_input("لینک", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")

    col1, col2 = st.columns([4, 1])
    with col2:
        fetch_btn = st.button("دریافت اطلاعات", use_container_width=True, key='fetch1')

    if fetch_btn and url:
        st.session_state['video_info'] = None
        st.session_state['available_formats'] = []
        st.session_state['transcript_data'] = None
        st.session_state['transcript_langs'] = []

        with st.spinner("در حال دریافت..."):
            try:
                info = get_video_info(url)
                st.session_state['video_info'] = info
                st.session_state['current_url'] = url
                add_to_history(info.get('title', ''), url)
            except Exception as e:
                err = str(e)
                if any(kw in err for kw in ['Sign in', 'bot', 'Could not copy', 'Permission', 'cookies']):
                    show_cookie_error()
                else:
                    st.error(f"خطا: {err[:300]}")

    if st.session_state['video_info']:
        info = st.session_state['video_info']

        thumbnail = info.get('thumbnail', '')
        title = info.get('title', '')
        duration = format_duration(info.get('duration'))
        uploader = info.get('uploader', '')
        view_count = format_view_count(info.get('view_count'))
        upload_date = info.get('upload_date', '')
        if upload_date and len(upload_date) == 8:
            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

        if thumbnail:
            st.image(thumbnail, use_container_width=True)

        st.markdown(f"""
        <div class="video-card">
            <h3>{title}</h3>
            <p style="color:#9694a8;font-size:0.9rem">{uploader}</p>
            <div class="video-meta">
                <span class="meta-tag">⏱ {duration}</span>
                <span class="meta-tag green">👁 {view_count}</span>
                <span class="meta-tag orange">📅 {upload_date}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### فرمت دانلود")
        dl_type = st.radio("نوع", ["ویدیو", "فقط صدا"], horizontal=True, label_visibility="collapsed")

        if dl_type == "ویدیو":
            opts = {"بهترین کیفیت": "best_video", "720p": "720p", "480p": "480p", "360p": "360p"}
            selected_format = opts[st.selectbox("کیفیت", list(opts.keys()))]
        else:
            opts = {"MP3 (320kbps)": "audio_mp3", "بهترین صدا": "audio_m4a"}
            selected_format = opts[st.selectbox("فرمت", list(opts.keys()))]

        available = st.session_state.get('available_formats', [])
        if available:
            with st.expander("فرمت‌های موجود"):
                render_formats_table(available)

        if st.button("شروع دانلود", use_container_width=True, key='dl1'):
            progress_bar = st.progress(0)
            try:
                download_video(st.session_state['current_url'], selected_format)
                progress_bar.progress(1.0)
                filename = st.session_state.get('download_filename', '')
                st.success("انجام شد!")
                st.balloons()

                if filename and os.path.exists(filename):
                    with open(filename, 'rb') as f:
                        file_data = f.read()
                    basename = os.path.basename(filename)
                    ext = os.path.splitext(filename)[1].lower()

                    if ext in ['.mp4', '.mkv', '.webm', '.avi']:
                        st.video(filename)
                        st.download_button("ذخیره ویدیو", file_data, basename, use_container_width=True)
                    elif ext in ['.mp3', '.m4a', '.opus', '.ogg', '.wav']:
                        st.audio(filename)
                        st.download_button("ذخیره صدا", file_data, basename, use_container_width=True)
                    else:
                        st.download_button("دانلود فایل", file_data, basename, use_container_width=True)

            except Exception as e:
                err = str(e)
                if any(kw in err for kw in ['Sign in', 'bot', 'Could not copy', 'Permission', 'cookies']):
                    show_cookie_error()
                elif any(kw in err for kw in ['Requested format', 'not available']):
                    show_format_error()
                else:
                    st.error(f"خطا: {err[:300]}")


# ==================== تب ۲: متن ویدیو ====================
with tab2:
    st.markdown("### استخراج متن ویدیو (ترانسکریپت)")
    st.markdown("زیرنویس خودکار یا دستی ویدیو رو استخراج کن و به صورت متن کامل داشته باش.")

    t_url = st.text_input("لینک ویدیو", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed", key='t_url')

    col_a, col_b = st.columns([4, 1])
    with col_b:
        fetch_transcript_btn = st.button("بررسی زبان‌ها", use_container_width=True, key='fetch_t')

    if fetch_transcript_btn and t_url:
        st.session_state['video_info'] = None
        st.session_state['transcript_data'] = None

        with st.spinner("در حال بررسی زبان‌های موجود..."):
            try:
                info = get_video_info(t_url)
                st.session_state['video_info'] = info
                st.session_state['current_url'] = t_url

                langs = st.session_state.get('transcript_langs', {})
                if langs:
                    st.success(f"{len(langs)} زبان زیرنویس پیدا شد!")
                else:
                    st.warning("زیرنویسی برای این ویدیو یافت نشد. ممکنه زیرنویس غیرفعال باشه.")

            except Exception as e:
                err = str(e)
                if any(kw in err for kw in ['Sign in', 'bot', 'Could not copy', 'Permission', 'cookies']):
                    show_cookie_error()
                else:
                    st.error(f"خطا: {err[:300]}")

    # نمایش اطلاعات ویدیو و انتخاب زبان
    if st.session_state['video_info']:
        info = st.session_state['video_info']
        langs = st.session_state.get('transcript_langs', {})

        st.markdown(f"""
        <div class="video-card">
            <h3>{info.get('title', '')}</h3>
            <p style="color:#9694a8;font-size:0.85rem">{info.get('uploader', '')} · {format_duration(info.get('duration'))}</p>
        </div>
        """, unsafe_allow_html=True)

        if langs:
            st.markdown("### انتخاب زبان")

            # مرتب‌سازی: اول فارسی، بعد انگلیسی، بعد بقیه
            sorted_langs = sorted(langs.keys(), key=lambda x: (
                0 if x.startswith('fa') else
                1 if x.startswith('en') else
                2
            ))

            lang_options = {}
            for code in sorted_langs:
                info_lang = langs[code]
                type_label = "دستی ✓" if info_lang['type'] == 'manual' else "خودکار"
                name = get_lang_name(code)
                label = f"{name} ({code}) — {type_label}"
                lang_options[label] = code

            selected_label = st.selectbox("زبان زیرنویس", list(lang_options.keys()))
            selected_lang = lang_options[selected_label]

            # تنظیمات نمایش
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                show_timestamps = st.checkbox("نمایش زمان‌بندی", value=True)
            with col_opt2:
                merge_lines = st.checkbox("ادغام خطوط تکراری", value=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("استخراج متن", use_container_width=True, key='extract_t'):
                with st.spinner("در حال استخراج متن ویدیو..."):
                    try:
                        entries, vid_info = get_transcript(t_url, selected_lang)

                        if entries:
                            # ادغام خطوط تکراری
                            if merge_lines:
                                merged = []
                                seen = set()
                                for e in entries:
                                    if e['text'] not in seen:
                                        seen.add(e['text'])
                                        merged.append(e)
                                entries = merged

                            st.session_state['transcript_data'] = entries
                            st.success(f"{len(entries)} خط متن استخراج شد!")
                        else:
                            st.error("متنی استخراج نشد. زبان دیگه‌ای امتحان کن.")

                    except Exception as e:
                        st.error(f"خطا: {str(e)[:300]}")

        else:
            st.info("زیرنویسی موجود نیست. لینک دیگه‌ای امتحان کن.")

    # نمایش متن استخراج‌شده
    if st.session_state.get('transcript_data'):
        entries = st.session_state['transcript_data']
        full_text = transcript_to_plain_text(entries)
        word_count = count_words(full_text)
        char_count = len(full_text)

        # آمار
        st.markdown(f"""
        <div class="transcript-stats">
            <div class="t-stat"><div class="val">{len(entries)}</div><div class="lbl">خط</div></div>
            <div class="t-stat"><div class="val">{word_count}</div><div class="lbl">کلمه</div></div>
            <div class="t-stat"><div class="val">{char_count}</div><div class="lbl">کاراکتر</div></div>
            <div class="t-stat"><div class="val">{format_duration(int(entries[-1]['time_sec'])) if entries else '0'}</div><div class="lbl">مدت</div></div>
        </div>
        """, unsafe_allow_html=True)

        # تب‌های نمایش متن
        view_tab1, view_tab2, view_tab3 = st.tabs(["متن با زمان‌بندی", "متن خام", "فقط متن"])

        with view_tab1:
            # نمایش با زمان‌بندی
            html_lines = ""
            for e in entries:
                yt_link = f"https://www.youtube.com/watch?v={st.session_state['video_info'].get('id', '')}&t={int(e['time_sec'])}s"
                html_lines += f"""<div class="transcript-line">
                    <a href="{yt_link}" target="_blank" class="transcript-time">[{e['time']}]</a>
                    <span class="transcript-text">{e['text']}</span>
                </div>"""

            st.markdown(f'<div class="transcript-box">{html_lines}</div>', unsafe_allow_html=True)

        with view_tab2:
            # متن با زمان‌بندی ساده
            timestamped = transcript_to_timestamped(entries)
            st.text_area("متن", timestamped, height=400, label_visibility="collapsed")

        with view_tab3:
            # فقط متن
            st.text_area("متن", full_text, height=400, label_visibility="collapsed")

        # دکمه‌های دانلود
        st.markdown("### دانلود متن")

        col_dl1, col_dl2, col_dl3 = st.columns(3)

        with col_dl1:
            st.download_button(
                "متن خام (.txt)",
                full_text.encode('utf-8'),
                file_name=f"transcript_{st.session_state['video_info'].get('id', 'video')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with col_dl2:
            timestamped_text = transcript_to_timestamped(entries)
            st.download_button(
                "با زمان‌بندی (.txt)",
                timestamped_text.encode('utf-8'),
                file_name=f"transcript_{st.session_state['video_info'].get('id', 'video')}_timed.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with col_dl3:
            # SRT
            srt_content = ""
            for i, e in enumerate(entries, 1):
                start = e['time'].replace(':', ':') + ',000'
                if i < len(entries):
                    end = entries[i]['time'].replace(':', ':') + ',000'
                else:
                    end_sec = e['time_sec'] + 5
                    m = int(end_sec // 60)
                    s = int(end_sec % 60)
                    end = f"{m:02d}:{s:02d},000"

                srt_content += f"{i}\n00:{start} --> 00:{end}\n{e['text']}\n\n"

            st.download_button(
                "زیرنویس SRT (.srt)",
                srt_content.encode('utf-8'),
                file_name=f"subtitle_{st.session_state['video_info'].get('id', 'video')}.srt",
                mime="text/plain",
                use_container_width=True,
            )


# ==================== تب ۳: دانلود دسته‌ای ====================
with tab3:
    st.markdown("### دانلود چند ویدیو")

    batch_urls = st.text_area("لینک‌ها", placeholder="هر لینک در یک خط...", height=150, label_visibility="collapsed", key='batch')

    batch_format = st.selectbox("فرمت", ["بهترین کیفیت ویدیو", "720p", "480p", "فقط صدا MP3"], key='bf')
    fmap = {"بهترین کیفیت ویدیو": "best_video", "720p": "720p", "480p": "480p", "فقط صدا MP3": "audio_mp3"}

    if st.button("شروع دانلود دسته‌ای", use_container_width=True, key='batch_dl'):
        urls_list = [u.strip() for u in batch_urls.strip().split('\n') if u.strip()]
        if not urls_list:
            st.warning("حداقل یک لینک وارد کن")
        else:
            prog = st.progress(0)
            stat = st.empty()
            ok, fail = 0, 0

            for i, video_url in enumerate(urls_list):
                stat.markdown(f"**{i+1} / {len(urls_list)}**")
                try:
                    download_video(video_url, fmap[batch_format])
                    ok += 1
                except Exception as e:
                    fail += 1
                    st.error(f"لینک {i+1}: {str(e)[:80]}")
                prog.progress((i + 1) / len(urls_list))

            stat.empty()
            if ok:
                st.success(f"{ok} موفق")
            if fail:
                st.warning(f"{fail} ناموفق")
            st.balloons()


# ==================== تب ۴: تاریخچه ====================
with tab4:
    st.markdown("### تاریخچه")
    if st.session_state['history']:
        for item in st.session_state['history']:
            st.markdown(f"""
            <div class="history-item">
                <div class="history-title">▶ {item['title'][:60]}</div>
                <div class="history-time">{item['time']}</div>
            </div>
            """, unsafe_allow_html=True)
        if st.button("پاک کردن", key='clear_h'):
            st.session_state['history'] = []
            st.rerun()
    else:
        st.markdown('<p style="color:#5c5a6e;text-align:center;padding:3rem">خالی است</p>', unsafe_allow_html=True)


# ==================== فوتر ====================
st.markdown("""<div class="footer">ساخته شده با Streamlit و yt-dlp</div>""", unsafe_allow_html=True)
