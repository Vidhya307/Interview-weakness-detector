"""
Simple Flask API server to serve the Groq API key from the .env file.
This runs alongside the main application to provide the /api/groq-key endpoint.
"""

from flask import Flask, jsonify
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

@app.route('/api/groq-key', methods=['GET'])
def get_groq_key():
    """
    Returns the Groq API key from the environment.
    The HTML page will call this endpoint to auto-populate the API key.
    """
    api_key = os.getenv('GROQ_API_KEY', '')
    if api_key:
        return jsonify({'api_key': api_key}), 200
    else:
        return jsonify({'error': 'GROQ_API_KEY not found in environment'}), 404

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    # Run on port 5000 (make sure Streamlit is on a different port)
    print("🚀 API Server running on http://localhost:5000")
    print("📝 Serving API key from environment variable")
    app.run(debug=False, host='127.0.0.1', port=5000)
