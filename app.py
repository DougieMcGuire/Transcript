import os
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

app = Flask(__name__)

@app.route('/transcript', methods=['POST'])
def get_transcript():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    if "v=" not in url:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    video_id = url.split("v=")[1].split("&")[0]

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        texts = [entry['text'] for entry in transcript]
        return jsonify({"transcript": " ".join(texts)})
    except (TranscriptsDisabled, NoTranscriptFound):
        return jsonify({"error": "Transcript not available"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # use Render's port or default 5000 locally
    app.run(host='0.0.0.0', port=port)
