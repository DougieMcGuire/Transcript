from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

def extract_video_id(url):
    """Extract YouTube video ID from various YouTube URL formats"""
    # Handle different YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If it's already just a video ID
    if len(url) == 11 and url.isalnum():
        return url
    
    return None

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        # Get URL from request body
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'error': 'URL is required in request body',
                'example': {'url': 'https://www.youtube.com/watch?v=VIDEO_ID'}
            }), 400
        
        url = data['url']
        
        # Extract video ID from URL
        video_id = extract_video_id(url)
        
        if not video_id:
            return jsonify({
                'error': 'Invalid YouTube URL or video ID',
                'provided_url': url
            }), 400
        
        # Get transcript - using list_transcripts to get available transcripts first
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Get the first available transcript (usually auto-generated or manual)
        transcript = None
        for t in transcript_list:
            try:
                transcript = t.fetch()
                break
            except:
                continue
        
        if not transcript:
            return jsonify({
                'error': 'No accessible transcripts found',
                'video_id': video_id
            }), 404
        
        # Format transcript
        full_transcript = ' '.join([entry['text'] for entry in transcript])
        
        return jsonify({
            'video_id': video_id,
            'transcript': full_transcript,
            'transcript_entries': transcript,  # Include timestamped entries
            'total_entries': len(transcript)
        })
        
    except Exception as e:
        error_msg = str(e)
        
        # Handle common errors
        if 'No transcripts were found' in error_msg:
            return jsonify({
                'error': 'No transcripts available for this video',
                'details': 'The video may not have captions or transcripts enabled'
            }), 404
        elif 'Video unavailable' in error_msg:
            return jsonify({
                'error': 'Video is unavailable or private',
                'details': 'Cannot access this video'
            }), 404
        else:
            return jsonify({
                'error': 'Failed to get transcript',
                'details': error_msg
            }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'YouTube Transcript API'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'YouTube Transcript API',
        'usage': {
            'endpoint': '/transcript',
            'method': 'POST',
            'body': {'url': 'https://www.youtube.com/watch?v=VIDEO_ID'},
            'description': 'Send a POST request with a YouTube URL to get the transcript'
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
