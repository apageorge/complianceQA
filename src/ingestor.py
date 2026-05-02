"""
ingestor.py — PDF loading, chunking, embedding
"""

import tempfile
import os
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma


def ingest_pdfs(uploaded_files, chunk_size: int = 1000, chunk_overlap: int = 200) -> Chroma:
    """
    Takes a list of Streamlit UploadedFile objects.
    Loads, chunks, embeds and returns a Chroma vectorstore.
    """
    all_chunks = []

    for uploaded_file in uploaded_files:
        # Streamlit gives us a file-like object — PyPDFLoader needs a path
        # so we write to a temp file first
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            loader = PyPDFLoader(tmp_path)
            pages = loader.load()

            # Tag each page with the original filename for citations
            for page in pages:
                page.metadata["source_filename"] = uploaded_file.name

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = splitter.split_documents(pages)
            all_chunks.extend(chunks)

        finally:
            os.unlink(tmp_path)  # clean up temp file

    if not all_chunks:
        raise ValueError("No content could be extracted from the uploaded PDFs.")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        collection_name="compliance_docs"
    )

    return vectorstore
