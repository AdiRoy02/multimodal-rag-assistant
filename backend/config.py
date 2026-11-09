
import os

# Groq chat model
CHAT_MODEL_NAME = "openai/gpt-oss-20b"

# Groq vision model
VISION_MODEL_NAME = "qwen/qwen3.8-27b"

# Embedding model
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# ChromaDB collection
CHROMA_COLLECTION_NAME = "multimodal_documents"


def get_groq_api_key():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Please provide your API key."
        )

    return api_key
