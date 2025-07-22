from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Let's test what methods are actually available
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print("Available methods in YouTubeTranscriptApi:")
    print([method for method in dir(YouTubeTranscriptApi) if not method.startswith('_')])
except ImportError as e:
    print(f"Import error: {e}")

def extract_video_id(url):
    """Extract YouTube video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    if len(url) == 11 and url.isalnum():
        return url
    
    return None

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        response_type = data.get('type', 'json')  # Default to JSON if not specified
        
        video_id = extract_video_id(url)
        
        if not video_id:
            if response_type == 'text':
                return "Invalid YouTube URL", 400, {'Content-Type': 'text/plain'}
            else:
                return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        # Get transcript using the API
        try:
            api_instance = YouTubeTranscriptApi()
            transcript_list = api_instance.list(video_id)
            
            # Find first available transcript
            transcript = None
            for t in transcript_list:
                transcript = t
                break
            
            if transcript is None:
                if response_type == 'text':
                    return "No transcripts found", 404, {'Content-Type': 'text/plain'}
                else:
                    return jsonify({'error': 'No transcripts found'}), 404
            
            # Fetch the actual transcript data
            fetched_transcript = transcript.fetch()
            transcript_data = fetched_transcript.snippets
            
        except Exception as e:
            if response_type == 'text':
                return f"Error: {str(e)}", 500, {'Content-Type': 'text/plain'}
            else:
                return jsonify({
                    'error': 'Failed to get transcript',
                    'details': str(e),
                    'available_methods': [method for method in dir(YouTubeTranscriptApi) if not method.startswith('_')]
                }), 500

        # Handle different response types
        if response_type == 'text':
            # Return only the text content
            full_transcript = ' '.join([entry.text for entry in transcript_data])
            return full_transcript, 200, {'Content-Type': 'text/plain'}
            
        elif response_type == 'raw':
            # Return raw transcript entries as simple list
            transcript_entries = []
            for entry in transcript_data:
                transcript_entries.append({
                    'text': entry.text,
                    'start': entry.start,
                    'duration': entry.duration
                })
            return jsonify(transcript_entries)
            
        else:
            # Default JSON response with metadata
            full_transcript = ' '.join([entry.text for entry in transcript_data])
            
            transcript_entries = []
            for entry in transcript_data:
                transcript_entries.append({
                    'text': entry.text,
                    'start': entry.start,
                    'duration': entry.duration
                })
            
            return jsonify({
                'video_id': video_id,
                'transcript': full_transcript,
                'transcript_entries': transcript_entries,
                'total_entries': len(transcript_entries)
            })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get transcript',
            'details': str(e)
        }), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'YouTube Transcript API',
        'endpoint': '/transcript',
        'method': 'POST',
        'body_options': {
            'url': 'https://www.youtube.com/watch?v=VIDEO_ID (required)',
            'type': 'json (default) | text | raw (optional)'
        },
        'examples': {
            'full_json': {'url': 'https://www.youtube.com/watch?v=VIDEO_ID'},
            'text_only': {'url': 'https://www.youtube.com/watch?v=VIDEO_ID', 'type': 'text'},
            'raw_entries': {'url': 'https://www.youtube.com/watch?v=VIDEO_ID', 'type': 'raw'}
        }
    })

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True, host='localhost', port=5000)
