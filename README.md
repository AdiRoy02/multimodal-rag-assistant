Multimodal RAG Assistant

An AI-powered application that allows users to upload PDF documents and ask questions about their contents using Retrieval-Augmented Generation (RAG).

The system processes text, tables, and images from PDF documents to provide context-aware answers.

Features

- PDF document upload and processing
- Text and table extraction
- Image extraction and description using a vision model
- Semantic search using vector embeddings
- Context-aware question answering
- Interactive web-based chat interface

Tech Stack

- Backend: Python, FastAPI
- Frontend: HTML, CSS, JavaScript
- LLM: Groq API (GPT-OSS 20B)
- Vision Model: Qwen
- Embeddings: Sentence Transformers
- Vector Database: ChromaDB
- PDF Processing: Unstructured

Project Structure

multimodal-rag-assistant/
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── document_processor.py
│   └── rag.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── .gitignore
└── README.md

How It Works

1. Upload a PDF document.
2. Extract text, tables, and images.
3. Generate descriptions for extracted images.
4. Split the content into chunks and generate embeddings.
5. Store the embeddings in ChromaDB.
6. Retrieve relevant content when a question is asked.
7. Generate an answer using the Groq LLM.

API Endpoints

- "GET /" – Backend status
- "POST /process-upload" – Upload and process PDF documents
- "POST /ask" – Ask questions about uploaded documents
- "GET /docs" – Interactive API documentation

Setup

1. Clone the repository

git clone https://github.com/AdiRoy02/multimodal-rag-assistant.git
cd multimodal-rag-assistant

2. Configure the Groq API key

Set the "GROQ_API_KEY" environment variable before starting the backend.

3. Start the application

cd backend
python app.py

Open the frontend at "http://localhost:8001/static/".

Current Limitation

ChromaDB currently uses in-memory storage, so uploaded document data is lost when the application runtime restarts.

Future Improvements

- Persistent vector storage
- Cloud deployment
- User authentication
- Chat history management

---

Status: Under Development
