
from config import CHAT_MODEL_NAME
from document_processor import final_collection


# Get all records belonging to a selected document
def get_document_records(document_id):

    records = final_collection.get(
        where={
            "document_id": document_id
        },
        include=["documents", "metadatas"]
    )

    return records


# Search within a selected PDF
def search_document(
    user_question,
    document_id,
    embedding_model
):

    # Step 1: Convert question into an embedding
    question_embedding = embedding_model.encode(
        user_question
    )

    # Step 2: Search within the selected PDF
    search_results = final_collection.query(
        query_embeddings=[
            question_embedding.tolist()
        ],
        n_results=3,
        where={
            "document_id": document_id
        }
    )

    return search_results


# Search across all uploaded PDFs
def search_documents(
    user_question,
    embedding_model,
    n_results=3
):

    # Step 1: Convert question into an embedding
    question_embedding = embedding_model.encode(
        user_question
    )

    # Step 2: Search across all uploaded PDFs
    search_results = final_collection.query(
        query_embeddings=[
            question_embedding.tolist()
        ],
        n_results=n_results
    )

    return search_results


# Prepare context from retrieved results
def prepare_context(search_results):

    retrieved_context = ""

    for i, document in enumerate(search_results["documents"][0]):

        metadata = search_results["metadatas"][0][i]

        content_type = metadata.get(
            "content_type",
            "text"
        )

        retrieved_context += f"""
        Context {i + 1}
        Content Type: {content_type}

        {document}
        """

    return retrieved_context


# Create the RAG prompt
def create_rag_prompt(user_question, retrieved_context):

    prompt = f"""
    You are a helpful AI assistant that answers questions
    based on the user's uploaded PDF documents.

    Use ONLY the information provided in the context.

    Context:
    {retrieved_context}

    User Question:
    {user_question}

    Instructions:
    1. Answer using only the provided context.
    2. Do not add information from your own knowledge.
    3. If the answer is not available in the context,
       clearly say that the PDF does not provide enough information.
    4. Explain the answer in simple and clear language.
    5. Do not make assumptions.

    Answer:
    """

    return prompt


# Extract source filenames from search results
def get_sources(search_results):

    sources = []

    for metadata in search_results["metadatas"][0]:

        source = metadata.get("source")

        if source and source not in sources:
            sources.append(source)

    return sources


# Generate an answer from uploaded documents
def answer_from_documents(
    user_question,
    embedding_model,
    groq_client,
    document_id=None
):

    # Step 1: Retrieve relevant chunks
    if document_id:

        search_results = search_document(
            user_question,
            document_id,
            embedding_model
        )

    else:

        search_results = search_documents(
            user_question,
            embedding_model,
            n_results=3
        )

    # Step 2: Prepare context
    retrieved_context = prepare_context(
        search_results
    )

    # Step 3: Extract source filenames
    sources = get_sources(
        search_results
    )

    # Step 4: Create RAG prompt
    prompt = create_rag_prompt(
        user_question,
        retrieved_context
    )

    # Step 5: Generate answer using Groq
    response = groq_client.chat.completions.create(
        model=CHAT_MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Step 6: Extract answer
    answer = response.choices[0].message.content

    # Step 7: Return answer and sources
    return {
        "answer": answer,
        "sources": sources
    }
