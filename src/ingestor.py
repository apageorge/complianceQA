"""
ingestor.py — PDF loading, chunking, embedding
"""

import tempfile
import os
from typing import List, Tuple

from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma


def load_pdf(uploaded_file, tmp_path: str) -> List[Document]:
    """
    Load a PDF using pypdf directly — more reliable than PyPDFLoader
    for varied document formats.
    """
    reader = PdfReader(tmp_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():  # skip blank pages
            pages.append(Document(
                page_content=text,
                metadata={
                    "page": i + 1,
                    "source_filename": uploaded_file.name,
                    "doc_id": uploaded_file.name,  # used for filtering
                }
            ))
    return pages

def ingest_pdfs(uploaded_files, chunk_size: int = 1000, chunk_overlap: int = 200) -> Tuple[Chroma, List[str]]:
    """
    Takes a list of Streamlit UploadedFile objects.
    Returns (vectorstore, list_of_doc_names).

    Each chunk is tagged with doc_id metadata so we can filter
    retrieval to specific documents later.
    """
    all_chunks = []
    doc_names = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    for uploaded_file in uploaded_files:
        # Streamlit gives us a file-like object — PyPDFLoader needs a path
        # so we write to a temp file first
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            pages = load_pdf(uploaded_file, tmp_path)
            if not pages:
                continue

            chunks = splitter.split_documents(pages)
            all_chunks.extend(chunks)
            doc_names.append(uploaded_file.name)

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

    return vectorstore,doc_names
