# Flask Web Application Setup

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_api_key_here
   SECRET_KEY=your-secret-key-here  # Optional, for production
   ```

3. **Run the Flask app:**
   ```bash
   python app.py
   ```

4. **Open your browser:**
   Navigate to `http://localhost:5001`
   
   Note: Port 5001 is used by default to avoid conflict with macOS AirPlay Receiver (port 5000).
   You can change the port by setting the `PORT` environment variable.

## Features

- **File Upload**: Drag and drop or click to upload requirements Excel files (.xlsm, .xlsx)
- **Analysis**: Automatically analyzes uploaded requirements and shows BSD summary
- **Real-time Progress**: Shows detailed progress bars and spinners during document generation
- **Progress Stages**:
  - Initializing LLM
  - Generating Business Solution Overview
  - Generating Function Summaries
  - Generating Function Implementations
  - Assembling Document
  - Complete
- **Download**: Download generated BSD documents directly from the web interface

## API Endpoints

- `GET /` - Main web interface
- `POST /api/upload` - Upload and analyze requirements file
- `POST /api/generate` - Generate BSD documents
- `GET /api/progress` - Get current generation progress
- `GET /api/download/<filename>` - Download generated document
- `POST /api/clear` - Clear session data

## Project Structure

```
Req_BSD_Automation/
├── app.py                 # Flask application
├── frontend/              # Frontend files
│   ├── templates/
│   │   └── index.html     # Main web interface
│   └── static/
│       ├── css/
│       │   └── style.css  # Styles
│       └── js/
│           └── app.js     # Frontend JavaScript
└── src/                   # Core logic (unchanged)
```

## Development

The app runs in debug mode by default. For production:

1. Set `SECRET_KEY` environment variable
2. Disable debug mode in `app.py`:
   ```python
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

## Notes

- Progress tracking uses polling (checks every 500ms)
- File uploads are stored temporarily and cleaned up after session ends
- For production, consider using:
  - Celery for async task processing
  - Redis for progress storage
  - Proper file storage (S3, etc.)
  - Database for document history

