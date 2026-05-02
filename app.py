import streamlit as st
import os
from src.ingestor import ingest_pdfs
from src.chain import build_chain, ask_question

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ComplianceQA",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
    background-color: #0f1117;
    color: #e8e6e0;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

/* App header */
.app-header {
    border-bottom: 1px solid #2a2d35;
    padding-bottom: 1.2rem;
    margin-bottom: 2rem;
}
.app-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #f0ede6;
    letter-spacing: -0.02em;
    margin: 0;
}
.app-subtitle {
    font-size: 0.75rem;
    color: #5c6070;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.3rem;
}

/* Status badge */
.status-badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 2px;
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 500;
}
.status-ready { background: #1a2e1a; color: #4caf7d; border: 1px solid #2d5e3a; }
.status-waiting { background: #1e1e1a; color: #8a8070; border: 1px solid #3a3830; }

/* Chat messages */
.msg-user {
    background: #1a1d24;
    border-left: 2px solid #c8a96e;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
    border-radius: 0 4px 4px 0;
}
.msg-assistant {
    background: #141720;
    border-left: 2px solid #4a7fa5;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
    border-radius: 0 4px 4px 0;
}
.msg-label {
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #5c6070;
    margin-bottom: 0.4rem;
}
.msg-text { font-size: 0.9rem; line-height: 1.7; color: #d4d0c8; }

/* Citations */
.citations-block {
    margin-top: 0.8rem;
    padding: 0.8rem 1rem;
    background: #0d1018;
    border: 1px solid #1e2230;
    border-radius: 4px;
}
.citations-label {
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #4a7fa5;
    margin-bottom: 0.5rem;
}
.citation-item {
    font-size: 0.78rem;
    color: #6a7a8a;
    padding: 0.3rem 0;
    border-bottom: 1px solid #1a1d24;
    line-height: 1.5;
}
.citation-item:last-child { border-bottom: none; }
.page-tag {
    display: inline-block;
    background: #1a2535;
    color: #4a7fa5;
    padding: 0 0.4rem;
    border-radius: 2px;
    font-size: 0.68rem;
    margin-right: 0.5rem;
}

/* Sidebar */
.sidebar-section {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #1e2230;
}
.sidebar-label {
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #5c6070;
    margin-bottom: 0.6rem;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #3a3d48;
}
.empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    display: block;
}
.empty-text {
    font-family: 'DM Serif Display', serif;
    font-size: 1.2rem;
    color: #4a4d58;
}
.empty-sub {
    font-size: 0.8rem;
    color: #2a2d35;
    margin-top: 0.5rem;
}

/* Suggested questions */
.suggest-label {
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #5c6070;
    margin-bottom: 0.8rem;
    margin-top: 2rem;
}

/* Input area */
.stTextInput > div > div > input {
    background: #1a1d24 !important;
    border: 1px solid #2a2d35 !important;
    border-radius: 4px !important;
    color: #e8e6e0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.9rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #4a7fa5 !important;
    box-shadow: 0 0 0 1px #4a7fa5 !important;
}

/* Buttons */
.stButton > button {
    background: #1a2535 !important;
    color: #4a7fa5 !important;
    border: 1px solid #2a3545 !important;
    border-radius: 2px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: #1f2d40 !important;
    border-color: #4a7fa5 !important;
}

/* File uploader */
.stFileUploader {
    background: #1a1d24 !important;
    border: 1px dashed #2a2d35 !important;
    border-radius: 4px !important;
}

/* Scrollable chat area */
.chat-scroll {
    max-height: 60vh;
    overflow-y: auto;
    padding-right: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "chain" not in st.session_state:
    st.session_state.chain = None
if "doc_names" not in st.session_state:
    st.session_state.doc_names = []
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = False
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="app-header">', unsafe_allow_html=True)
    st.markdown('<p class="app-title">⚖️ ComplianceQA</p>', unsafe_allow_html=True)
    st.markdown('<p class="app-subtitle">Regulatory Document Intelligence</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # API Key
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-label">OpenAI API Key</p>', unsafe_allow_html=True)
    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="sk-...",
        label_visibility="collapsed"
    )
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.session_state.api_key_set = True
        st.markdown('<span class="status-badge status-ready">● Key set</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-waiting">○ Key required</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Document upload
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-label">Regulatory Documents</p>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files and st.session_state.api_key_set:
        new_names = [f.name for f in uploaded_files]
        if new_names != st.session_state.doc_names:
            with st.spinner("Ingesting documents..."):
                try:
                    vectorstore = ingest_pdfs(uploaded_files)
                    chain = build_chain(vectorstore)
                    st.session_state.vectorstore = vectorstore
                    st.session_state.chain = chain
                    st.session_state.doc_names = new_names
                    st.session_state.messages = []  # reset chat for new docs
                except Exception as e:
                    st.error(f"Error ingesting documents: {e}")

    if st.session_state.doc_names:
        st.markdown('<span class="status-badge status-ready">● Documents loaded</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        for name in st.session_state.doc_names:
            st.markdown(f'<div class="citation-item">📄 {name}</div>', unsafe_allow_html=True)
    elif uploaded_files and not st.session_state.api_key_set:
        st.warning("Set your API key first, then re-upload.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Settings
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-label">Retrieval Settings</p>', unsafe_allow_html=True)
    k_chunks = st.slider("Chunks to retrieve", min_value=2, max_value=8, value=4)
    chunk_size = st.select_slider(
        "Chunk size",
        options=[500, 750, 1000, 1500, 2000],
        value=1000
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Clear chat
    if st.session_state.messages:
        if st.button("Clear conversation"):
            st.session_state.messages = []
            st.rerun()


# ── Main area ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    # Header
    st.markdown('<div class="app-header">', unsafe_allow_html=True)
    st.markdown('<p class="app-title">Compliance Assistant</p>', unsafe_allow_html=True)
    if st.session_state.doc_names:
        doc_list = " · ".join(st.session_state.doc_names)
        st.markdown(f'<p class="app-subtitle">Querying: {doc_list}</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="app-subtitle">Upload regulatory documents to begin</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat history
    if not st.session_state.messages:
        if st.session_state.chain:
            # Loaded but no questions yet
            st.markdown("""
            <div class="empty-state">
                <span class="empty-icon">⚖️</span>
                <p class="empty-text">Documents loaded. Ask your first question.</p>
                <p class="empty-sub">Try the suggested questions on the right →</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Nothing loaded
            st.markdown("""
            <div class="empty-state">
                <span class="empty-icon">📂</span>
                <p class="empty-text">No documents loaded</p>
                <p class="empty-sub">Upload a regulatory PDF in the sidebar to get started.<br>
                Try the FCA Consumer Duty guidance or EU AI Act.</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Render conversation
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-user">
                    <div class="msg-label">You</div>
                    <div class="msg-text">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-assistant">
                    <div class="msg-label">ComplianceQA</div>
                    <div class="msg-text">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)

                # Citations
                if msg.get("sources"):
                    citations_html = '<div class="citations-block"><div class="citations-label">📚 Source references</div>'
                    for src in msg["sources"]:
                        page = src.get("page", "?")
                        snippet = src.get("snippet", "")[:140].strip()
                        doc = src.get("doc", "")
                        citations_html += f"""
                        <div class="citation-item">
                            <span class="page-tag">p.{page}</span>
                            <span style="color:#4a5568; font-size:0.7rem;">{doc}</span><br>
                            <span style="padding-left: 2.5rem; display:block; margin-top:0.2rem;">…{snippet}…</span>
                        </div>"""
                    citations_html += '</div>'
                    st.markdown(citations_html, unsafe_allow_html=True)

    # Input
    # Input
    st.markdown("<br>", unsafe_allow_html=True)

    def handle_submit():
        """Callback — runs before rerun, clears input after grabbing value."""
        question = st.session_state.chat_input_field
        if question and st.session_state.chain:
            st.session_state.messages.append({"role": "user", "content": question})
            st.session_state.pending_question = question
        st.session_state.chat_input_field = ""  # clear the input

    with st.container():
        input_col, btn_col = st.columns([5, 1])
        with input_col:
            st.text_input(
                "Ask a question",
                placeholder="What are the main obligations under Consumer Duty?",
                label_visibility="collapsed",
                key="chat_input_field",
                disabled=not bool(st.session_state.chain),
                on_change=handle_submit  # triggers on Enter key too
            )
        with btn_col:
            st.button(
                "Ask →",
                disabled=not bool(st.session_state.chain),
                on_click=handle_submit
            )

    # Process any pending question from this rerun
    if st.session_state.get("pending_question") and st.session_state.chain:
        question = st.session_state.pending_question
        st.session_state.pending_question = None  # clear immediately

        with st.spinner("Retrieving and reasoning..."):
            try:
                answer, sources = ask_question(
                    st.session_state.chain,
                    question,
                    st.session_state.messages[:-1],
                    k=k_chunks
                )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Error: {e}",
                    "sources": []
                })
        st.rerun()

# ── Right column — suggested questions + info ─────────────────────────────────
with col2:
    st.markdown('<p class="suggest-label">Suggested Questions</p>', unsafe_allow_html=True)

    suggested = [
        "What are the main obligations on firms?",
        "What does this say about conflicts of interest?",
        "What are the requirements around customer vulnerability?",
        "What are the penalties for non-compliance?",
        "What governance structures are required?",
        "What records must be kept and for how long?",
        "How should firms handle complaints?",
        "What are the requirements for senior management?",
    ]

    for q in suggested:
        if st.button(q, key=f"suggest_{q}", disabled=not bool(st.session_state.chain)):
            st.session_state.messages.append({"role": "user", "content": q})
            with st.spinner("Thinking..."):
                try:
                    answer, sources = ask_question(
                        st.session_state.chain,
                        q,
                        st.session_state.messages[:-1],
                        k=k_chunks
                    )
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                except Exception as e:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Error: {e}",
                        "sources": []
                    })
            st.rerun()

    # How it works
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="suggest-label">How It Works</p>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.78rem; color:#4a5060; line-height:1.8;">
        <div style="margin-bottom:0.4rem;">① PDF → chunked into passages</div>
        <div style="margin-bottom:0.4rem;">② Passages embedded as vectors</div>
        <div style="margin-bottom:0.4rem;">③ Your question → top-k similar chunks retrieved</div>
        <div style="margin-bottom:0.4rem;">④ GPT-4o-mini answers from retrieved context only</div>
        <div>⑤ Source pages cited for every answer</div>
    </div>
    """, unsafe_allow_html=True)
