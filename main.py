from flask import Flask, request, jsonify
from pathlib import Path
import yt_dlp
import uuid

app = Flask(__name__)

# مجلد التحميلات (تأكد أن السيرفر يسمح بالكتابة هنا)
DOWNLOAD_DIR = Path("/app/downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# تخزين حالة التحميل
downloads_status = {}

# ضع هنا مسار ملف الكوكيز إذا احتاجت الفيديوهات تسجيل دخول
COOKIES_FILE = "cookies.txt"  # مثال: cookies.txt من متصفحك

def get_ydl_options(download_id):
    return {
        'outtmpl': str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
        'progress_hooks': [lambda d: downloads_status.update({download_id: d})],
        'quiet': True,
        'no_warnings': True,
        'cookiefile': COOKIES_FILE if Path(COOKIES_FILE).exists() else None,
        'age_limit': None,
        'geo_bypass': True,
    }

@app.route("/api/get_video_links", methods=["POST"])
def get_video_links():
    """
    Body: { "url": "https://youtube.com/watch?v=..." }
    Returns: JSON with available qualities and direct links
    """
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL is required"}), 400

    download_id = str(uuid.uuid4())
    downloads_status[download_id] = {"status": "starting"}

    try:
        with yt_dlp.YoutubeDL(get_ydl_options(download_id)) as ydl:
            info = ydl.extract_info(url, download=False)

            links = []
            for f in info.get("formats", []):
                if f.get("url"):
                    links.append({
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "quality": f.get("format_note"),
                        "resolution": f.get("resolution"),
                        "audio_codec": f.get("acodec"),
                        "video_codec": f.get("vcodec"),
                        "filesize": f.get("filesize"),
                        "direct_url": f.get("url")
                    })

            return jsonify({
                "title": info.get("title"),
                "duration": info.get("duration"),
                "is_live": info.get("is_live", False),
                "age_limited": info.get("age_limit", 0) > 0,
                "links": links
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download_status/<download_id>", methods=["GET"])
def download_status(download_id):
    if download_id not in downloads_status:
        return jsonify({"error": "Download ID not found"}), 404
    return jsonify(downloads_status[download_id]), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
