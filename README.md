# ⚖️ ComplianceQA

A RAG-powered assistant for financial regulatory documents. Ask natural language questions against FCA guidelines, Basel documentation, or any compliance PDF — with source citations for every answer.

**[Live Demo →](https://complianceapp-apgeorge.streamlit.app/)** 

---

## What It Does

Upload regulatory PDFs. Ask compliance questions. Get grounded answers with page-level citations — no hallucination, no guessing. If the answer isn't in the document, it says so.

Built for financial compliance use cases: FCA Consumer Duty, Basel III/IV, EU AI Act, internal policy documents.

---

## Architecture

```
PDF Upload
    │
    ▼
PyPDFLoader → RecursiveCharacterTextSplitter
    │           (chunk_size=1000, overlap=200)
    ▼
OpenAI text-embedding-3-small
    │
    ▼
ChromaDB (local vector store)
    │
    ◄──────────────────────────────────────┐
    │                                       │
User Question                    Conversation History
    │                                       │
    ▼                                       │
Similarity Search (top-k chunks) ──────────┘
    │
    ▼
GPT-4o-mini
(temperature=0, grounded prompt)
    │
    ▼
Answer + Page Citations
```

---

## Key Engineering Decisions

| Decision | Rationale |
|---|---|
| `chunk_size=1000, overlap=200` | Regulatory docs are dense; overlap prevents losing answers that span chunk boundaries |
| `temperature=0` | Compliance needs deterministic answers — creativity is a liability here |
| Strict grounding prompt | Model explicitly told to say "not in document" rather than use prior knowledge |
| `return_source_documents=True` | Every answer is auditable — traceable to specific pages |
| Deduped citations | Multiple retrieved chunks from same page collapsed to one citation |
| Last 6 messages in history | Keeps conversation context without bloating the context window |

---

## Setup — Local

```bash
# 1. Clone and install
git clone https://github.com/apageorge/complianceqa
cd complianceqa
pip install -r requirements.txt

# 2. Run
streamlit run app.py
```

Enter your OpenAI API key in the sidebar when the app opens.

**Suggested test documents (free/public):**
- FCA Consumer Duty: https://www.fca.org.uk/publication/policy/ps22-9.pdf
- EU AI Act: https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689


---

## Stack

Python · LangChain · ChromaDB · OpenAI · Streamlit

---

*Domain: financial compliance and regulatory intelligence.*
