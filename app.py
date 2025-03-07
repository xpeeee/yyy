from flask import Flask, render_template, request, jsonify
import yt_dlp
import threading
import ujson as json  # Ultra-fast JSON processing

app = Flask(__name__)

# Function to fetch video links in a separate thread
def fetch_video_links(video_url, result_dict):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'format': 'best[ext=mp4]',  # Fetch only the best MP4 format
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            result_dict["url"] = info.get("url")
    except Exception as e:
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
        return json.dumps({"video_links": [{"quality": "Best Available", "url": result_dict["url"]}]}), 200
    else:
        return json.dumps({"error": "Failed to fetch video."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
