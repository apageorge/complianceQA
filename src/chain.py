"""
chain.py — RAG chain with conversation history, doc filtering, and compare mode
"""

from typing import List, Tuple, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import RetrievalQA
from langchain_community.vectorstores import Chroma


COMPLIANCE_PROMPT = PromptTemplate(
    template="""You are a precise financial compliance assistant. Answer questions 
accurately using ONLY the regulatory document excerpts provided below.

Rules:
- Base your answer ONLY on the provided context. Do not use prior knowledge.
- If the answer is not in the context, respond: "This is not addressed in the provided documents."
- Be concise and professional — accuracy matters in a compliance context.
- Note: FCA documents use specific terminology. "Governance" appears as "board oversight"
  or "governing body". "Senior management" relates to SM&CR.
- Reference which part of the document your answer comes from.

Document context:
{context}

Question: {question}

Answer:""",
    input_variables=["context", "question"]
)

COMPARE_PROMPT = PromptTemplate(
    template="""You are a precise financial compliance analyst comparing two regulatory documents.

Your task: Compare how the two documents address the topic in the question.
Structure your answer as:
- **Document A ({doc_a}):** what it says
- **Document B ({doc_b}):** what it says  
- **Key differences:** what changed or differs between them
- **Significance:** why the differences matter (if any)

Rules:
- Only use information from the provided excerpts. Do not use prior knowledge.
- If a document does not address the topic, say so explicitly.
- Be precise — this is a compliance context.

Excerpts from {doc_a}:
{context_a}

Excerpts from {doc_b}:
{context_b}

Question: {question}

Comparison:""",
    input_variables=["doc_a", "doc_b", "context_a", "context_b", "question"]
)
# ── Helpers ───────────────────────────────────────────────────────────────────

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)



def build_chain(vectorstore: Chroma) -> RetrievalQA:
    """Build the base RAG chain — used for single-doc and multi-doc queries."""
    
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

    chain = RetrievalQA.from_chain_type(
        llm=get_llm(),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": COMPLIANCE_PROMPT}
    )

    return chain

def build_sources(docs) -> List[Dict]:
    """Deduplicate and format source documents into citation dicts."""
    sources = []
    seen = set()
    for doc in docs:
        page = doc.metadata.get("page", "?")
        doc_name = doc.metadata.get("source_filename", doc.metadata.get("source", "document"))
        key = (doc_name, page)
        if key not in seen:
            seen.add(key)
            sources.append({
                "page": page,
                "doc": doc_name,
                "snippet": doc.page_content.strip()
            })
    return sources


def is_unanswered(answer: str) -> bool:
    """Check if the model couldn't find a relevant answer."""
    phrases = [
        "not addressed in the provided",
        "not covered in the provided",
        "not in the provided",
        "cannot find",
        "no information",
        "not mentioned",
        "i don't have",
        "i do not have",
    ]
    return any(p in answer.lower() for p in phrases)


def format_chat_history(messages: List[Dict]) -> str:
    """Format previous messages into a string for the prompt."""
    if not messages:
        return "No previous conversation."

    lines = []
    for msg in messages[-6:]:  # last 3 exchanges (6 messages) to keep context window sane
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")

    return "\n".join(lines)

CONVERSATIONAL_PATTERNS = [
    "how are you", "what are you", "who are you", "hello", "hi ",
    "hey", "thanks", "thank you", "goodbye", "bye", "what can you do"
]

def is_conversational(question: str) -> bool:
    q = question.lower().strip()
    return any(q.startswith(p) or p in q for p in CONVERSATIONAL_PATTERNS)



def ask_question(
    chain: RetrievalQA,  # not used anymore, kept for compatibility
    question: str,
    history: List[Dict],
    k: int = 4,
    selected_docs: Optional[List[str]] = None,
    vectorstore: Optional[Chroma] = None,
) -> Tuple[str, List[Dict]]:

    if is_conversational(question):
        return (
            "I'm a compliance document assistant — ask about the uploaded documents.",
            []
        )

    llm = get_llm()

    # ── STEP 1: PER-DOCUMENT RETRIEVAL ─────────────────────────────
    all_docs = []

    if selected_docs and vectorstore:
        k_per_doc = max(2, k // len(selected_docs))

        for doc_name in selected_docs:
            docs = vectorstore.similarity_search(
                question,
                k=k_per_doc,
                filter={"doc_id": doc_name}
            )
            all_docs.extend(docs)
    else:
        all_docs = vectorstore.similarity_search(question, k=k)

    # ── STEP 2: GROUP BY DOCUMENT ──────────────────────────────────
    docs_by_source = {}

    for d in all_docs:
        src = d.metadata.get("source_filename", "document")
        docs_by_source.setdefault(src, []).append(d.page_content)

    # ── STEP 3: STRUCTURED CONTEXT ─────────────────────────────────
    context_blocks = []
    for src, texts in docs_by_source.items():
        combined = "\n\n".join(texts)
        context_blocks.append(f"Document: {src}\n{combined}")

    context = "\n\n---\n\n".join(context_blocks)

    # ── STEP 4: HISTORY ────────────────────────────────────────────
    chat_history_str = format_chat_history(history)

    # ── STEP 5: STRONG SYNTHESIS PROMPT ────────────────────────────
    prompt = f"""
You are a precise financial compliance assistant.

You are given excerpts from MULTIPLE regulatory documents.

Instructions:
- Use information from ALL documents where relevant
- Do not rely on only one document if others contain useful information
- Combine and synthesise insights across documents
- If documents differ, explain clearly
- If not found, say: "This is not addressed in the provided documents."

Previous conversation:
{chat_history_str}

Context:
{context}

Question: {question}

Answer:
"""

    response = llm.invoke(prompt)
    answer = response.content

    sources = [] if is_unanswered(answer) else build_sources(all_docs)

    return answer, sources

def compare_documents(
    vectorstore: Chroma,
    question: str,
    doc_a: str,
    doc_b: str,
    k: int = 4,
) -> Tuple[str, List[Dict]]:
    """
    Compare how two specific documents address a question.
    Retrieves from each doc separately then synthesises.
    Returns (answer_text, list_of_source_dicts).
    """
    llm = get_llm()

    # Retrieve from doc A
    docs_a = vectorstore.similarity_search(
        question,
        k=k,
        filter={"doc_id": doc_a}
    )
    context_a = "\n\n".join(d.page_content for d in docs_a) if docs_a \
        else "No relevant content found in this document."

    # Retrieve from doc B
    docs_b = vectorstore.similarity_search(
        question,
        k=k,
        filter={"doc_id": doc_b}
    )
    context_b = "\n\n".join(d.page_content for d in docs_b) if docs_b \
        else "No relevant content found in this document."

    # Build and invoke compare prompt
    prompt = COMPARE_PROMPT.format(
        doc_a=doc_a,
        doc_b=doc_b,
        context_a=context_a,
        context_b=context_b,
        question=question
    )

    response = llm.invoke(prompt)
    answer = response.content

    # Combine sources from both docs
    all_sources = build_sources(docs_a) + build_sources(docs_b)

    return answer, all_sources
