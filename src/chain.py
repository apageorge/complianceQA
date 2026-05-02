"""
chain.py — RAG chain with conversation history
"""

from typing import List, Tuple, Dict
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
- Reference which part of the document your answer comes from.

Document context:
{context}

Question: {question}

Answer:""",
    input_variables=["context", "question"]
)


def build_chain(vectorstore: Chroma) -> RetrievalQA:
    """Build the RAG chain from a vectorstore."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,  # deterministic — critical for compliance
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": COMPLIANCE_PROMPT}
    )

    return chain


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
    chain: RetrievalQA,
    question: str,
    history: List[Dict],
    k: int = 4
) -> Tuple[str, List[Dict]]:
    if is_conversational(question):
        return (
            "I'm a compliance document assistant — I can answer questions about "
            "the regulatory documents you've uploaded. Try asking about obligations, "
            "outcomes, senior management requirements, or customer protection rules.",
            []  # empty sources
        )

    chain.retriever.search_kwargs["k"] = k

    # Inject history directly into the question string
    # RetrievalQA only reliably passes "query" through
    chat_history_str = format_chat_history(history)
    
    augmented_question = f"""Previous conversation:
{chat_history_str}

Current question: {question}"""

    result = chain.invoke({"query": augmented_question})

    answer = result["result"]
    
    # Don't show citations if the model couldn't find relevant content
    # or if the question wasn't document-related
    no_answer_phrases = [
        "not addressed in the provided",
        "not covered in the provided",
        "not in the provided",
        "cannot find",
        "no information",
        "not mentioned",
        "i don't have",
        "i do not have",
        "how are you",
    ]
    
    answer_lower = answer.lower()
    is_unanswered = any(phrase in answer_lower for phrase in no_answer_phrases)

    sources = []
    if not is_unanswered:
        seen_pages = set()
        for doc in result.get("source_documents", []):
            page = doc.metadata.get("page", "?")
            doc_name = doc.metadata.get("source_filename", doc.metadata.get("source", "document"))
            key = (doc_name, page)
            if key not in seen_pages:
                seen_pages.add(key)
                sources.append({
                    "page": page,
                    "doc": doc_name,
                    "snippet": doc.page_content.strip()
                })

    return answer, sources