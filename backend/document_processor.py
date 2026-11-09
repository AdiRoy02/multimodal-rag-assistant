
import os
import uuid
import base64
import chromadb

from bs4 import BeautifulSoup
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Text
from unstructured.chunking.title import chunk_by_title

from config import (
    VISION_MODEL_NAME,
    CHROMA_COLLECTION_NAME
)


# Initialize ChromaDB client
chroma_client = chromadb.Client()

# Create ChromaDB collection
final_collection = chroma_client.create_collection(
    name=CHROMA_COLLECTION_NAME
)

print("New Collection created!")
print("Collection name:", final_collection.name)
print("Initial record count:", final_collection.count())


# Extract elements from PDF
def extract_pdf_elements(pdf_path):

    if not os.path.exists(pdf_path):
        raise FileNotFoundError("PDF file not found!")

    elements = partition_pdf(
        filename=pdf_path,
        strategy="hi_res",
        infer_table_structure=True,
        extract_image_block_types=["Image"],
        extract_image_block_to_payload=True
    )

    return elements


# Separate text, tables and images
def separate_pdf_modalities(elements):

    content = {
        "text": [],
        "tables": [],
        "images": []
    }

    for element in elements:

        category = getattr(element, "category", None)
        metadata = getattr(element, "metadata", None)

        if category not in ["Table", "Image"]:

            text = getattr(element, "text", "")

            if text and text.strip():
                content["text"].append(text)

        elif category == "Table":

            table_html = getattr(
                metadata,
                "text_as_html",
                None
            )

            if table_html:
                content["tables"].append(table_html)

        elif category == "Image":

            image_base64 = getattr(
                metadata,
                "image_base64",
                None
            )

            if image_base64:
                content["images"].append(image_base64)

    return content


# Convert HTML tables into readable text
def process_table(table_html):

    soup = BeautifulSoup(table_html, "html.parser")

    rows = []

    for row in soup.find_all("tr"):

        cells = row.find_all(["th", "td"])

        row_text = [
            cell.get_text(strip=True)
            for cell in cells
        ]

        rows.append(" | ".join(row_text))

    return "\n".join(rows)


# Prepare text and tables for chunking
def prepare_elements_for_chunking(elements):

    prepared_elements = []

    for element in elements:

        category = getattr(element, "category", None)
        metadata = getattr(element, "metadata", None)

        if category == "Image":
            continue

        elif category == "Table":

            table_html = getattr(
                metadata,
                "text_as_html",
                None
            )

            if table_html:

                table_text = process_table(table_html)

                if table_text.strip():
                    prepared_elements.append(
                        Text(text=table_text)
                    )

        else:

            if getattr(element, "text", "").strip():
                prepared_elements.append(element)

    return prepared_elements


# Save extracted images
def save_extracted_images(images, pdf_name, document_id):

    image_paths = []

    image_folder = os.path.join(
        "extracted_images",
        document_id
    )

    os.makedirs(image_folder, exist_ok=True)

    for i, image_data in enumerate(images):

        image_bytes = base64.b64decode(image_data)

        image_path = os.path.join(
            image_folder,
            f"image_{i}.jpg"
        )

        with open(image_path, "wb") as image_file:
            image_file.write(image_bytes)

        image_paths.append(image_path)

    return image_paths


# Generate image descriptions using Groq Vision
def describe_image(image_path, groq_client):

    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    image_base64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    image_data_url = f"data:image/jpeg;base64,{image_base64}"

    response = groq_client.chat.completions.create(
        model=VISION_MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        Describe the important information visible in this image.
                        Identify diagrams, labels, text, objects, and their relationships.
                        Focus on information useful for answering questions about the document.
                        Do not guess unclear information.
                        """
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url
                        }
                    }
                ]
            }
        ],
        max_completion_tokens=512
    )

    return response.choices[0].message.content


# Split image descriptions into smaller chunks
def split_image_description(
    description,
    embedding_model,
    max_tokens=240
):

    paragraphs = description.split("\n")

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        candidate = current_chunk + "\n" + paragraph

        token_count = len(
            embedding_model.tokenizer(
                candidate,
                truncation=False
            )["input_ids"]
        )

        if token_count <= max_tokens:

            current_chunk = candidate

        else:

            if current_chunk:
                chunks.append(current_chunk.strip())

            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


# Generate a unique document ID
def generate_document_id():

    document_id = f"doc_{uuid.uuid4().hex}"

    return document_id


# Generate text chunk IDs
def generate_text_chunk_ids(document_id, total_chunks):

    chunk_ids = []

    for i in range(total_chunks):

        chunk_id = f"{document_id}_chunk_{i}"

        chunk_ids.append(chunk_id)

    return chunk_ids


# Generate image chunk IDs
def generate_image_chunk_ids(
    document_id,
    image_chunks_by_image
):

    image_ids = []

    for image_index, chunks in enumerate(image_chunks_by_image):

        for chunk_index in range(len(chunks)):

            chunk_id = (
                f"{document_id}_image_{image_index}"
                f"_chunk_{chunk_index}"
            )

            image_ids.append(chunk_id)

    return image_ids


# Generate text chunk metadata
def generate_text_chunk_metadata(
    document_id,
    pdf_name,
    total_chunks
):

    metadata_list = []

    for i in range(total_chunks):

        metadata = {
            "document_id": document_id,
            "source": pdf_name,
            "chunk_index": i,
            "content_type": "text"
        }

        metadata_list.append(metadata)

    return metadata_list


# Generate image chunk metadata
def generate_image_chunk_metadata(
    document_id,
    pdf_name,
    image_chunks_by_image,
    image_paths
):

    metadata_list = []

    for image_index, chunks in enumerate(image_chunks_by_image):

        for chunk_index in range(len(chunks)):

            metadata = {
                "document_id": document_id,
                "source": pdf_name,
                "content_type": "image_description",
                "image_id": f"image_{image_index}",
                "chunk_index": chunk_index,
                "image_path": image_paths[image_index]
            }

            metadata_list.append(metadata)

    return metadata_list


# Process all images extracted from a PDF
def process_pdf_images(
    images,
    pdf_name,
    document_id,
    groq_client,
    embedding_model
):

    if not images:

        return {
            "image_paths": [],
            "image_descriptions": [],
            "image_chunks": [],
            "image_embeddings": [],
            "image_ids": [],
            "image_metadata": []
        }

    image_paths = save_extracted_images(
        images,
        pdf_name,
        document_id
    )

    image_descriptions = []

    for image_path in image_paths:

        description = describe_image(
            image_path,
            groq_client
        )

        image_descriptions.append(description)

    image_chunks_by_image = []

    for description in image_descriptions:

        chunks = split_image_description(
            description,
            embedding_model,
            max_tokens=240
        )

        image_chunks_by_image.append(chunks)

    all_image_chunks = []

    for chunks in image_chunks_by_image:
        all_image_chunks.extend(chunks)

    image_embeddings = embedding_model.encode(
        all_image_chunks
    )

    image_ids = generate_image_chunk_ids(
        document_id,
        image_chunks_by_image
    )

    image_metadata = generate_image_chunk_metadata(
        document_id,
        pdf_name,
        image_chunks_by_image,
        image_paths
    )

    return {
        "image_paths": image_paths,
        "image_descriptions": image_descriptions,
        "image_chunks": all_image_chunks,
        "image_embeddings": image_embeddings,
        "image_ids": image_ids,
        "image_metadata": image_metadata
    }


# Process PDF text and tables
def process_pdf_text(
    elements,
    pdf_name,
    document_id,
    embedding_model
):

    prepared_elements = prepare_elements_for_chunking(elements)

    document_chunks = chunk_by_title(
        prepared_elements,
        max_characters=1200,
        new_after_n_chars=1000,
        combine_text_under_n_chars=200
    )

    chunk_texts = [
        chunk.text
        for chunk in document_chunks
    ]

    document_embeddings = embedding_model.encode(
        chunk_texts
    )

    chunk_ids = generate_text_chunk_ids(
        document_id,
        len(chunk_texts)
    )

    chunk_metadata = generate_text_chunk_metadata(
        document_id,
        pdf_name,
        len(chunk_texts)
    )

    return {
        "chunks": chunk_texts,
        "embeddings": document_embeddings,
        "ids": chunk_ids,
        "metadata": chunk_metadata
    }


# Process PDF and store text and image data in ChromaDB
def process_pdf(
    pdf_path,
    embedding_model,
    groq_client,
    original_filename=None
):

    document_id = generate_document_id()

    pdf_name = original_filename or os.path.basename(pdf_path)

    elements = extract_pdf_elements(pdf_path)

    content = separate_pdf_modalities(elements)

    text_results = process_pdf_text(
        elements,
        pdf_name,
        document_id,
        embedding_model
    )

    image_results = process_pdf_images(
        content["images"],
        pdf_name,
        document_id,
        groq_client,
        embedding_model
    )

    # Store text and table chunks
    if text_results["ids"]:

        final_collection.add(
            ids=text_results["ids"],
            documents=text_results["chunks"],
            embeddings=text_results["embeddings"].tolist(),
            metadatas=text_results["metadata"]
        )

    # Store image description chunks
    if image_results["image_ids"]:

        final_collection.add(
            ids=image_results["image_ids"],
            documents=image_results["image_chunks"],
            embeddings=image_results["image_embeddings"].tolist(),
            metadatas=image_results["image_metadata"]
        )

    print("PDF processing and storage completed!")
    print("Document ID:", document_id)
    print("Filename:", pdf_name)

    print("\nText chunks stored:", len(text_results["chunks"]))
    print("Image chunks stored:", len(image_results["image_chunks"]))

    print("\nTotal ChromaDB records:", final_collection.count())

    return {
        "document_id": document_id,
        "filename": pdf_name,
        "text_chunks": len(text_results["chunks"]),
        "image_chunks": len(image_results["image_chunks"])
    }
