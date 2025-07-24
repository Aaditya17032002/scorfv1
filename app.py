from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import base64
import tempfile
import os
from typing import Union, Dict, Any
import mimetypes  # Use mimetypes instead of magic for Windows compatibility
from datetime import datetime
import uuid

app = FastAPI(title="Document Handler API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class DocumentRequest(BaseModel):
    record_id: Union[str, int] = Field(..., description="Record ID (can be string or number)")
    document_id: Union[str, int] = Field(..., description="Document ID (can be string or number)")
    base64_data: str = Field(..., description="Base64 encoded document data")

class DocumentResponse(BaseModel):
    record_id: Union[str, int]
    document_id: Union[str, int]
    status: str
    confidence_score: float
    reason: str

def detect_file_type(base64_data: str) -> tuple[str, str]:
    """
    Detect file type from base64 data
    Returns: (mime_type, file_extension)
    """
    try:
        # Decode base64 data
        decoded_data = base64.b64decode(base64_data)
        
        print(f"🔍 Analyzing file... File size: {len(decoded_data)} bytes")
        
        # Try to detect from base64 header if present
        if base64_data.startswith('data:'):
            try:
                header, data = base64_data.split(',', 1)
                mime_type = header.split(':')[1].split(';')[0]
                file_extension = mime_type.split('/')[-1] if '/' in mime_type else 'bin'
                print(f"📄 Detected from data URL: {mime_type} -> .{file_extension}")
                return mime_type, file_extension
            except:
                pass
        
        # Try to detect from file signature (magic bytes)
        file_signatures = {
            b'\x89PNG\r\n\x1a\n': ('image/png', 'png'),
            b'\xff\xd8\xff': ('image/jpeg', 'jpg'),
            b'GIF87a': ('image/gif', 'gif'),
            b'GIF89a': ('image/gif', 'gif'),
            b'%PDF': ('application/pdf', 'pdf'),
            b'PK\x03\x04': ('application/zip', 'zip'),
            b'PK\x05\x06': ('application/zip', 'zip'),
            b'PK\x07\x08': ('application/zip', 'zip'),
            b'\x50\x4b\x03\x04': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'docx'),
            b'\x50\x4b\x05\x06': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'docx'),
            b'\x50\x4b\x07\x08': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'docx'),
        }
        
        for signature, (mime_type, ext) in file_signatures.items():
            if decoded_data.startswith(signature):
                print(f"📄 Detected from signature: {mime_type} -> .{ext}")
                return mime_type, ext
        
        # Fallback: try to detect from first few bytes
        if len(decoded_data) >= 4:
            # Check for common text formats
            try:
                text_start = decoded_data[:100].decode('utf-8', errors='ignore')
                if text_start.startswith('<?xml'):
                    print("📄 Detected: XML file -> .xml")
                    return 'application/xml', 'xml'
                elif text_start.startswith('{') or text_start.startswith('['):
                    print("📄 Detected: JSON file -> .json")
                    return 'application/json', 'json'
                elif text_start.startswith('<html') or text_start.startswith('<!DOCTYPE'):
                    print("📄 Detected: HTML file -> .html")
                    return 'text/html', 'html'
                elif text_start.startswith('<?php'):
                    print("📄 Detected: PHP file -> .php")
                    return 'application/x-httpd-php', 'php'
                elif text_start.startswith('#!/'):
                    print("📄 Detected: Script file -> .txt")
                    return 'text/plain', 'txt'
            except:
                pass
        
        # Ultimate fallback
        print("📄 Could not detect file type, using generic binary -> .bin")
        return 'application/octet-stream', 'bin'
        
    except Exception as e:
        print(f"❌ Error detecting file type: {e}")
        # Ultimate fallback
        return 'application/octet-stream', 'bin'

def save_temp_file(decoded_data: bytes, record_id: Union[str, int], 
                  document_id: Union[str, int], file_extension: str) -> str:
    """
    Save decoded data to a temporary file in the working directory
    Returns: temporary file path
    """
    # Create a unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"record_{record_id}_doc_{document_id}_{timestamp}_{unique_id}.{file_extension}"
    
    # Create temp directory in working directory
    temp_dir = os.path.join(os.getcwd(), "temp_files")
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_file_path = os.path.join(temp_dir, filename)
    
    # Write data to temporary file
    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(decoded_data)
    
    print(f"💾 File saved to: {temp_file_path}")
    print(f"📁 File size: {len(decoded_data)} bytes")
    
    return temp_file_path

@app.get("/")
async def root():
    return {"message": "Document Handler API", "version": "1.0.0"}

@app.post("/process-document", response_model=DocumentResponse)
async def process_document(request: DocumentRequest):
    """
    Process document: detect type and save as temporary backup
    """
    try:
        print(f"\n🚀 Processing document request:")
        print(f"   Record ID: {request.record_id}")
        print(f"   Document ID: {request.document_id}")
        
        # Clean base64 data (remove data URL prefix if present)
        base64_data = request.base64_data
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',', 1)[1]
        
        # Validate base64 data
        try:
            decoded_data = base64.b64decode(base64_data, validate=True)
        except Exception as e:
            print(f"❌ Invalid base64 data: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid base64 data: {str(e)}")
        
        if len(decoded_data) == 0:
            print("❌ Empty file data")
            raise HTTPException(status_code=400, detail="Empty file data")
        
        print(f"✅ Base64 validation successful")
        
        # Detect file type
        mime_type, file_extension = detect_file_type(base64_data)
        
        # Calculate confidence score and determine status
        confidence_score = 0.0
        status = "rejected"
        reason = ""
        
        # Define accepted file types and their confidence scores
        accepted_types = {
            'application/pdf': (0.95, "PDF document - Accepted"),
            'image/jpeg': (0.85, "JPEG image - Accepted"),
            'image/png': (0.85, "PNG image - Accepted"),
            'image/gif': (0.80, "GIF image - Accepted"),
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': (0.90, "DOCX document - Accepted"),
            'application/msword': (0.85, "DOC document - Accepted"),
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': (0.90, "XLSX spreadsheet - Accepted"),
            'application/vnd.ms-excel': (0.85, "XLS spreadsheet - Accepted"),
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': (0.90, "PPTX presentation - Accepted"),
            'application/vnd.ms-powerpoint': (0.85, "PPT presentation - Accepted"),
            'text/plain': (0.70, "Text file - Accepted"),
            'application/json': (0.75, "JSON file - Accepted"),
            'application/xml': (0.75, "XML file - Accepted"),
            'text/html': (0.70, "HTML file - Accepted"),
            'text/csv': (0.75, "CSV file - Accepted")
        }
        
        if mime_type in accepted_types:
            confidence_score, reason = accepted_types[mime_type]
            status = "accepted"
            print(f"✅ Document accepted: {reason}")
        else:
            confidence_score = 0.3
            reason = f"File type '{mime_type}' not in accepted list - Rejected"
            print(f"❌ Document rejected: {reason}")
        
        # Save temporary file (for backend processing only)
        temp_file_path = save_temp_file(
            decoded_data, 
            request.record_id, 
            request.document_id, 
            file_extension
        )
        
        # Prepare response with only 5 required fields
        response = DocumentResponse(
            record_id=request.record_id,
            document_id=request.document_id,
            status=status,
            confidence_score=confidence_score,
            reason=reason
        )
        
        print(f"📤 Sending response:")
        print(f"   Status: {status}")
        print(f"   Confidence Score: {confidence_score}")
        print(f"   Reason: {reason}")
        print(f"   File Type: {mime_type}")
        print(f"   File Extension: {file_extension}")
        print(f"   File Size: {len(decoded_data)} bytes")
        print(f"   Saved to: {temp_file_path}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.delete("/cleanup/{file_path}")
async def cleanup_temp_file(file_path: str):
    """
    Optional endpoint to cleanup temporary files
    """
    try:
        if os.path.exists(file_path) and os.path.dirname(file_path) == os.path.join(os.getcwd(), "temp_files"):
            os.remove(file_path)
            print(f"🧹 Deleted file: {file_path}")
            return {"message": "File deleted successfully", "file_path": file_path}
        else:
            raise HTTPException(status_code=404, detail="File not found or invalid path")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

if __name__ == "__main__":
    import os
    import uvicorn
    
    # Check if we're in production (Azure Web App sets WEBSITE_SITE_NAME)
    is_production = os.environ.get('WEBSITE_SITE_NAME') is not None
    
    if is_production:
        # Production: Use Gunicorn
        try:
            import gunicorn.app.base
            from gunicorn.six import iteritems
            
            class StandaloneApplication(gunicorn.app.base.BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()
                
                def load_config(self):
                    config = {key: value for key, value in iteritems(self.options)
                             if key in self.cfg.settings and value is not None}
                    for key, value in iteritems(config):
                        self.cfg.set(key.lower(), value)
                
                def load(self):
                    return self.application
            
            # Gunicorn options for production
            options = {
                'bind': f"0.0.0.0:{os.environ.get('PORT', '8000')}",
                'workers': 4,
                'worker_class': 'uvicorn.workers.UvicornWorker',
                'timeout': 30,
                'keepalive': 2,
                'max_requests': 1000,
                'max_requests_jitter': 50,
                'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
            }
            
            print("🚀 Starting Document Handler API with Gunicorn (Production)")
            StandaloneApplication(app, options).run()
            
        except ImportError:
            print("⚠️ Gunicorn not available, falling back to Uvicorn")
            uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get('PORT', '8000')))
    else:
        # Development: Use Uvicorn with reload
        print("🚀 Starting Document Handler API with Uvicorn (Development)")
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)