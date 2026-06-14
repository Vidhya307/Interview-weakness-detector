# API Key Loading Setup

## Overview
The interview system now automatically loads the Groq API key from the `.env` file instead of requiring manual entry.

## How it works

1. **API Server** (`api_server.py`): A simple Flask server that reads the `GROQ_API_KEY` from your `.env` file and serves it via an HTTP endpoint.

2. **HTML/JavaScript**: When `interview_room.html` loads, it automatically fetches the API key from the API server and auto-fills the input field.

3. **Fallback**: If the API server is not available, the form gracefully falls back to manual API key entry.

## Setup Instructions

### 1. Install Required Dependencies
```bash
pip install flask python-dotenv
```

### 2. Verify Your .env File
Make sure you have a `.env` file in the project root with:
```
GROQ_API_KEY=gsk_your_actual_api_key_here
```

### 3. Run the API Server
In a separate terminal, run:
```bash
python api_server.py
```

You should see:
```
🚀 API Server running on http://localhost:5000
📝 Serving API key from environment variable
```

### 4. Open the Interview Room
- Keep the API server running
- Open `interview_room.html` in your browser
- The API key should automatically load (you'll see a green checkmark)
- The input field will be disabled and show the API key is loaded from the environment

## Troubleshooting

### API key doesn't load automatically
- Make sure `api_server.py` is running on port 5000
- Check browser console for CORS errors
- Verify `.env` file contains `GROQ_API_KEY`

### Port 5000 is already in use
Edit `api_server.py` and change the port number in the last line:
```python
app.run(debug=False, host='127.0.0.1', port=5001)  # Use 5001 instead
```

Then update the HTML fetch URL to match:
```javascript
const response = await fetch("http://localhost:5001/api/groq-key", {
```

### Manual Entry Still Works
If the API server is not running, you can still manually enter your API key in the input field.

## Security Note
The API server only exposes the endpoint to your local machine (`127.0.0.1`). Keep it running only when needed.
