
import os
import sys
import tempfile

from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from sentence_transformers import SentenceTransformer
from groq import Groq


# Add backend directory to Python path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

sys.path.insert(0, str(BASE_DIR))


# Import project modules
from config import (
    EMBEDDING_MODEL_NAME,
    get_groq_api_key
)

from document_processor import process_pdf

from rag import answer_from_documents


# Initialize embedding model
embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)

print("Embedding model loaded successfully!")


# Initialize Groq client
groq_client = Groq(
    api_key=get_groq_api_key()
)

print("Groq client initialized successfully!")


# Initialize FastAPI application
app = FastAPI(
    title="Multimodal RAG Assistant",
    description="An AI assistant that answers questions from uploaded PDF documents",
    version="1.0.0"
)


# Home route
@app.get("/")
def home():

    return {
        "message": "Welcome to Multimodal RAG Assistant!",
        "status": "Backend is running successfully"
    }


# Process uploaded PDF
@app.post("/process-upload")
async def process_uploaded_pdf(
    file: UploadFile = File(...)
):

    # Step 1: Read uploaded file
    file_bytes = await file.read()

    # Step 2: Validate file extension
    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed!"
        )

    # Step 3: Validate PDF signature
    if not file_bytes.startswith(b"%PDF-"):

        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file!"
        )

    # Step 4: Save PDF temporarily
    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False
    ) as temp_file:

        temp_file.write(file_bytes)

        temp_pdf_path = temp_file.name

    try:

        # Step 5: Process uploaded PDF
        result = process_pdf(
            pdf_path=temp_pdf_path,
            embedding_model=embedding_model,
            groq_client=groq_client,
            original_filename=file.filename
        )

        # Step 6: Return processing details
        return {
            "message": "PDF processed successfully!",
            **result
        }

    finally:

        # Step 7: Delete temporary PDF
        if os.path.exists(temp_pdf_path):

            os.remove(temp_pdf_path)


# Request model for questions
class QuestionRequest(BaseModel):

    question: str

    document_id: str | None = None


# Answer user questions
@app.post("/ask")
def ask_question(request: QuestionRequest):

    # Step 1: Get the user's question
    user_question = request.question

    # Step 2: Get the selected document ID
    document_id = request.document_id

    # Step 3: Generate answer using RAG
    result = answer_from_documents(
        user_question=user_question,
        embedding_model=embedding_model,
        groq_client=groq_client,
        document_id=document_id
    )

    # Step 4: Return answer and sources
    return {
        "answer": result["answer"],
        "sources": result["sources"]
    }


# Connect frontend to FastAPI
FRONTEND_DIR = PROJECT_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True
    ),
    name="frontend"
)


print("FastAPI application initialized successfully!")
print("Frontend directory:", FRONTEND_DIR)


# Start FastAPI application
if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False
    )
