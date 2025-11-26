from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL
import os

app = Flask(__name__)

# لو عندك ملف كوكيز، ضع اسمه هنا (اختياري)
COOKIES_FILE = "cookies.txt"  # اتركه فاضي إذا ما عندك كوكيز


def get_video_info(url):
    """
    إرجاع:
    - روابط مباشرة للفيديو والصوت (temporary)
    - معلومات الفيديو: عنوان، مدة، صورة مصغرة
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "nocheckcertificate": True,
    }

    # لو معك ملف كوكيز (لتجاوز الفيديوهات المحمية)
    if os.path.exists(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # الروابط المباشرة
        formats = info.get("formats", [])
        direct_urls = []

        for f in formats:
            if f.get("url"):
                direct_urls.append({
                    "itag": f.get("format_id"),
                    "ext": f.get("ext"),
                    "resolution": f.get("resolution"),
                    "fps": f.get("fps"),
                    "vcodec": f.get("vcodec"),
                    "acodec": f.get("acodec"),
                    "url": f.get("url"),  # ← الرابط المباشر
                })

        # ترتيب الروابط من أعلى جودة لأقل
        direct_urls = sorted(direct_urls, key=lambda x: (x["resolution"] or ""), reverse=True)

        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "direct_urls": direct_urls
        }


@app.route("/api/get_direct_urls", methods=["POST"])
def api_get_urls():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url'"}), 400

    url = data["url"]

    try:
        result = get_video_info(url)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return jsonify({"status": "YouTube Direct API is running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
