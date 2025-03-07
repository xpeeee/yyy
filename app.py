from flask import Flask, render_template, request, jsonify
import yt_dlp
import threading
import ujson as json  # Ultra-fast JSON processing
import logging
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to fetch video links in a separate thread
def fetch_video_links(video_url, result_dict, done_event):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'format': 'bestvideo+bestaudio/best',  # Fetch best available format
        'merge_output_format': 'mp4',  # Ensure MP4 format
    }

    # Add cookies if available
    cookies_path = 'cookies.txt'
    if os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            result_dict["url"] = info.get("url")
            result_dict["formats"] = info.get("formats", [])  # Fetch all formats
            logging.info(f"Successfully fetched video: {video_url}")
    except Exception as e:
        logging.error(f"Error fetching video: {e}")
        result_dict["error"] = str(e)

    done_event.set()  # Signal that processing is complete

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
    done_event = threading.Event()

    # Run yt-dlp in a separate thread
    thread = threading.Thread(target=fetch_video_links, args=(video_url, result_dict, done_event))
    thread.start()
    done_event.wait()  # Wait for the thread to complete

    if "url" in result_dict:
        return json.dumps({
            "video_links": [
                {"quality": f"{fmt.get('format_note', 'Unknown')} ({fmt['ext']})", "url": fmt["url"]}
                for fmt in result_dict.get("formats", []) if "url" in fmt
            ]
        }), 200
    else:
        return json.dumps({"error": result_dict.get("error", "Failed to fetch video.")}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
