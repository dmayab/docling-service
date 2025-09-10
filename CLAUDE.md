# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Docling REST API Service** - a FastAPI-based web service that wraps IBM's Docling library to provide HTTP endpoints for document processing. It serves as a bridge between Docling (a Python document processing library) and web applications that need OCR and document structure extraction capabilities.

## Development Commands

### Local Development
```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the service
python app.py
```

### Platform-Specific Installation
```bash
# macOS
./install_mac.sh
./start_service_mac.command

# macOS with GPU support
./run_local_gpu.sh

# Linux
./install_linux.sh

# Windows
install_windows.bat
```

### Docker Development
```bash
# Basic service only
docker-compose up docling-service

# Production with Nginx proxy
docker-compose --profile production up --build

# All services
docker-compose up --build
```

### Testing
```bash
# Run coordinate extraction tests
python test_coordinates.py

# Create test documents
python create_test_docx.py

# Manual API testing
curl http://localhost:8000/health
```

## Architecture Overview

### Core Components
- **app.py** (670+ lines) - Main FastAPI application with all endpoints
- **task_cleanup.py** - Background task cleanup management
- **Docker setup** - Multi-service orchestration with optional Nginx proxy

### Key Design Patterns

#### Asynchronous Processing Pipeline
1. Client uploads document to `/process` → returns task_id immediately
2. Background processing using FastAPI's BackgroundTasks
3. Client polls `/status/{task_id}` for progress
4. Results include structured text blocks with coordinates (PDFs only)

#### Smart Hardware Detection
The service auto-detects and optimizes for available hardware:
- Apple Silicon GPU (M1/M2/M3/M4) via MPS
- NVIDIA CUDA GPUs
- Windows DirectML
- CPU fallback

#### Document Processing Flow
- **PDF**: Full coordinate extraction with bounding boxes for text blocks
- **DOCX**: Structural extraction only (no coordinates)
- Both formats support table and metadata extraction

### API Endpoints
- `GET /health` - System health with hardware info
- `GET /` - Service information and endpoint listing  
- `POST /process` - Document upload (PDF/DOCX only)
- `GET /status/{task_id}` - Processing status polling
- `DELETE /status/{task_id}` - Task cleanup

### Performance Expectations
- Small docs (<10 pages): ~5-15 seconds
- Medium docs (10-50 pages): ~15-60 seconds
- Large docs (50+ pages): ~1-5 minutes

## Key Dependencies
- **docling>=2.8.0** - IBM's document processing library (core functionality)
- **fastapi>=0.104.0** - Web framework
- **torch** - Neural network framework with hardware acceleration
- **pytesseract** - OCR engine
- **PyMuPDF** - PDF processing

## Development Notes

### Hardware Acceleration
The service automatically detects and utilizes GPU acceleration when available. The `detect_hardware()` function in app.py handles this detection and configures the appropriate device settings for optimal performance.

### Task Management
In-memory task storage with UUID-based tracking. Tasks are automatically cleaned up after completion to prevent memory leaks. Background cleanup runs periodically via task_cleanup.py.

### Production Deployment
The service includes production-ready features:
- Nginx reverse proxy configuration
- CORS handling
- Health monitoring endpoints
- Docker containerization
- Automatic task cleanup