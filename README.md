# RAG Agents - Retrieval-Augmented Generation System

A RAG system built with FastAPI, Streamlit, and Qdrant for intelligent document processing and question answering.

## 🏗️ Architecture

Frontend (Streamlit) ──→ Backend (FastAPI) ──→ Qdrant (Vector DB) :8501 :8000 :6333

**Components:**
- **Frontend**: Streamlit UI for document upload and queries
- **Backend**: FastAPI server with AI agents and RAG pipeline  
- **Qdrant**: Vector database for document embeddings

## 🤖 AI Agents Workflow

1. **Document Processing Agent**: Extracts, chunks, and embeds documents
2. **Query Processing Agent**: Processes queries and performs vector search
3. **Response Generation Agent**: Synthesizes answers from retrieved context

**Pipeline:** `Upload → Process → Embed → Store → Query → Retrieve → Generate`

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local dev)

### Run with Docker

bash
# Clone and start all services
git clone <repository-url> cd RAG-Agents docker-compose up -d
# Access applications
# Frontend: [http://localhost:8501](http://localhost:8501)
# Backend API: [http://localhost:8000/docs](http://localhost:8000/docs)
# Qdrant: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

### Local Development
# Backend
cd backend uv sync docker run -p 6333:6333 qdrant/qdrant # Start Qdrant uv run uvicorn main:app --reload --port 8000
# Frontend (new terminal)
cd frontend pip install -r requirements.txt export BACKEND_URL=[http://localhost:8000](http://localhost:8000) streamlit run streamlit_app.py --server.port 8501

## 📚 Usage

### Upload Documents
1. Go to http://localhost:8501
2. Upload PDF, DOCX, or TXT files
3. Documents are processed and stored automatically

### Query System
1. Enter questions in the query field
2. Get answers with source attribution
3. View confidence scores and relevant chunks

### API Examples
# Upload document
curl -X POST "[http://localhost:8000/upload](http://localhost:8000/upload)"
-F "file=@document.pdf"
# Query
curl -X POST "[http://localhost:8000/query](http://localhost:8000/query)"
-H "Content-Type: application/json"
-d '{"query": "Your question here"}'

## 🔧 Configuration

**Environment Variables:**
- `BACKEND_URL`: Frontend → Backend connection
- `QDRANT_HOST/PORT`: Backend → Qdrant connection

## 🐳 Docker Commands
# Start services
docker-compose up -d
# View logs
docker-compose logs -f
# Stop services
docker-compose down
# Rebuild
docker-compose up --build -d

## 🛠️ Troubleshooting

**Common Issues:**
- **Port conflicts**: Modify ports in `docker-compose.yml`
- **Services not starting**: Check `docker-compose logs`
- **Connection issues**: Verify all services are running with `docker-compose ps`

**Health Checks:**
- Backend: http://localhost:8000/health
- Frontend: http://localhost:8501/_stcore/health
- Qdrant: http://localhost:6333/health

## 📁 Project Structure

RAG Agents/ ├── backend/ # FastAPI application ├── frontend/ # Streamlit application
├── uploads/ # Document storage ├── docker-compose.yml # Service orchestration └── README.md # Documentation

**🚀 Ready to build intelligent document Q&A systems!**

## Agents Architecture

<img width="269" height="531" alt="graph_diagram1" src="https://github.com/user-attachments/assets/a2a41a49-834c-488d-bdb7-162a4ea43934" />

## UI snapshots

<img width="1904" height="876" alt="snippet" src="https://github.com/user-attachments/assets/4c283fef-540d-40dc-bca0-7632dc856096" />
<img width="1333" height="574" alt="snippet2" src="https://github.com/user-attachments/assets/4ca0c657-38ca-4c41-963d-a786eacfc2d1" />
