from flask import Flask, render_template, request, jsonify
import yt_dlp
import threading
import ujson as json  # Ultra-fast JSON processing
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to fetch video links in a separate thread
def fetch_video_links(video_url, result_dict):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'format': 'bestvideo+bestaudio/best',  # Fetch best available format
        'merge_output_format': 'mp4',  # Ensure MP4 format
        'cookiefile': 'cookies.txt',  # Use extracted cookies if available
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            result_dict["url"] = info.get("url")
            result_dict["formats"] = info.get("formats", [])  # Fetch all formats
    except Exception as e:
        logging.error(f"Error fetching video: {e}")
        result_dict["error"] = str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_video_links', methods=['POST'])
def get_video_links():
    data = request.get_json()
    video_url = data.get('video_url')

    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    result_dict = {}

    # Run yt-dlp in a separate thread
    thread = threading.Thread(target=fetch_video_links, args=(video_url, result_dict))
    thread.start()
    thread.join()  # Wait for the thread to complete

    if "url" in result_dict:
        return json.dumps({
            "video_links": [
                {"quality": f"{fmt['format_note']} ({fmt['ext']})", "url": fmt["url"]}
                for fmt in result_dict.get("formats", []) if "url" in fmt
            ]
        }), 200
    else:
        return json.dumps({"error": result_dict.get("error", "Failed to fetch video.")}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
