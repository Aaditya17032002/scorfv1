# Document Handler API

A FastAPI-based document processing service that accepts file uploads, validates document types, and provides intelligent document classification with confidence scoring.

## 🚀 Features

- **Document Type Detection**: Automatically detects file types using file signatures and content analysis
- **Intelligent Validation**: Accepts/rejects documents based on predefined criteria
- **Confidence Scoring**: Provides confidence scores for document classification
- **Base64 Processing**: Handles base64-encoded file data
- **Temporary Storage**: Saves processed files for backend processing
- **CORS Support**: Cross-origin request support for web applications
- **Comprehensive Logging**: Detailed backend logging for debugging

## 📋 Supported File Types

### Accepted Documents (with confidence scores):
- **PDF Documents**: 95% confidence
- **Office Documents**: 85-90% confidence (DOCX, XLSX, PPTX, DOC, XLS, PPT)
- **Images**: 80-85% confidence (JPEG, PNG, GIF)
- **Text Files**: 70-75% confidence (TXT, JSON, XML, HTML, CSV)

### Rejected Documents:
- Unsupported file types receive 30% confidence and are rejected

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip

### Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fastapi
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Running the Application

### Start the server
```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`

### Alternative startup
```bash
python app.py
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
- **URL**: `GET /`
- **Description**: Returns API status and version
- **Response**:
  ```json
  {
    "message": "Document Handler API",
    "version": "1.0.0"
  }
  ```

#### 2. Process Document
- **URL**: `POST /process-document`
- **Description**: Process and validate uploaded documents
- **Request Body**:
  ```json
  {
    "record_id": "string|number",
    "document_id": "string|number", 
    "base64_data": "base64_encoded_file_data"
  }
  ```
- **Response**:
  ```json
  {
    "record_id": "string|number",
    "document_id": "string|number",
    "status": "accepted|rejected",
    "confidence_score": 0.0-1.0,
    "reason": "Detailed explanation"
  }
  ```

#### 3. Health Check
- **URL**: `GET /health`
- **Description**: Health check endpoint
- **Response**:
  ```json
  {
    "status": "healthy",
    "timestamp": "2024-12-01T14:30:22.123456"
  }
  ```

#### 4. Cleanup Temporary Files
- **URL**: `DELETE /cleanup/{file_path}`
- **Description**: Clean up temporary files (optional)
- **Response**:
  ```json
  {
    "message": "File deleted successfully",
    "file_path": "path/to/file"
  }
  ```

## 🧪 Testing

### Using curl
```bash
# Health check
curl http://localhost:8000/

# Process document (replace with actual base64 data)
curl -X POST http://localhost:8000/process-document \
  -H "Content-Type: application/json" \
  -d '{
    "record_id": "12345",
    "document_id": "DOC001",
    "base64_data": "base64_encoded_data_here"
  }'
```

### Using Python requests
```python
import requests
import base64

# Read file and convert to base64
with open("document.pdf", "rb") as file:
    base64_data = base64.b64encode(file.read()).decode()

# Send request
response = requests.post(
    "http://localhost:8000/process-document",
    json={
        "record_id": "12345",
        "document_id": "DOC001",
        "base64_data": base64_data
    }
)

print(response.json())
```

## 📁 File Storage

- **Location**: `temp_files/` directory in the project root
- **Naming Convention**: `record_{record_id}_doc_{document_id}_{timestamp}_{uuid}.{extension}`
- **Example**: `record_12345_doc_DOC001_20241201_143022_abc12345.pdf`

## 🔧 Configuration

### Environment Variables
No environment variables required for basic operation.

### CORS Settings
The API is configured to allow all origins for development:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 Response Examples

### Accepted Document
```json
{
  "record_id": "12345",
  "document_id": "DOC001",
  "status": "accepted",
  "confidence_score": 0.95,
  "reason": "PDF document - Accepted"
}
```

### Rejected Document
```json
{
  "record_id": "12345",
  "document_id": "DOC001",
  "status": "rejected",
  "confidence_score": 0.3,
  "reason": "File type 'application/octet-stream' not in accepted list - Rejected"
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Use different port
   uvicorn app:app --reload --port 8001
   ```

2. **CORS errors**
   - Ensure the CORS middleware is properly configured
   - Check that the frontend is making requests to the correct URL

3. **File type detection issues**
   - Check console logs for detailed file analysis
   - Verify file signatures are being detected correctly

### Debugging
- Check the console output for detailed processing logs
- Monitor the `temp_files/` directory for saved files
- Use browser developer tools to inspect network requests

## 📝 Development

### Project Structure
```
fastapi/
├── app.py              # Main FastAPI application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── temp_files/        # Temporary file storage (created automatically)
```

### Adding New File Types
To add support for new file types, modify the `accepted_types` dictionary in `app.py`:

```python
accepted_types = {
    'application/pdf': (0.95, "PDF document - Accepted"),
    'your/mime-type': (0.85, "Your file type - Accepted"),
    # Add more types here
}
```

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review the console logs for detailed error information
- Ensure all dependencies are properly installed 