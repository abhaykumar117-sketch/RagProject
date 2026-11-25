import os
import streamlit as st

import main


st.set_page_config(
    page_title="PDF AI Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #09111f 0%, #111b31 55%, #17152d 100%);
        color: #f8fafc;
        font-family: "Segoe UI", "Noto Sans", Arial, sans-serif;
    }
    [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"],
    [data-testid="stHeader"] {
        color: #f8fafc !important;
    }
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #f8fafc !important;
    }
    [data-testid="stCaptionContainer"] {
        color: #bac6dc !important;
    }
    [data-testid="stSidebar"] {
        background: #0a1324;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.055);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 16px;
        backdrop-filter: blur(12px);
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        font-family: "Segoe UI", "Noto Sans", Arial, sans-serif;
        font-size: 1rem;
        font-weight: 400;
        line-height: 1.75;
        letter-spacing: 0.005em;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {
        font-size: 1rem;
        font-weight: 400;
        line-height: 1.75;
    }
    [data-testid="stChatMessage"] h1 {
        font-size: 1.75rem;
        line-height: 1.3;
        font-weight: 650;
    }
    [data-testid="stChatMessage"] h2 {
        font-size: 1.45rem;
        line-height: 1.35;
        font-weight: 650;
    }
    [data-testid="stChatMessage"] h3 {
        font-size: 1.2rem;
        line-height: 1.4;
        font-weight: 600;
    }
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] th {
        font-weight: 650;
    }
    [data-testid="stChatMessage"] pre,
    [data-testid="stChatMessage"] code {
        font-family: Consolas, "Courier New", monospace;
    }
    [data-testid="stChatInput"] textarea {
        border-radius: 16px;
        background: #111b2d !important;
        color: #f8fafc !important;
        caret-color: #a5b4fc !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #aebbd1 !important;
        opacity: 1;
    }
    [data-testid="stChatInput"] {
        border: 1px solid rgba(129, 140, 248, 0.25);
        border-radius: 18px;
        background: #111b2d;
    }
    [data-testid="stBottom"] {
        background: linear-gradient(180deg, transparent, #0d1526 35%);
    }
    [data-testid="stChatInput"] button {
        color: #f8fafc !important;
        background: #4f46e5 !important;
        border-radius: 10px !important;
    }
    [data-testid="stChatInput"] button:disabled {
        color: #94a3b8 !important;
        background: #263248 !important;
    }
    .hero {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        padding: 20px 24px;
        border-radius: 20px;
        background:
            radial-gradient(circle at 85% 20%, rgba(14, 165, 233, 0.18), transparent 28%),
            linear-gradient(135deg, rgba(79, 70, 229, 0.19), rgba(14, 165, 233, 0.10));
        border: 1px solid rgba(129, 140, 248, 0.24);
        margin: 2px 0 16px;
        box-shadow: 0 18px 45px rgba(3, 7, 18, 0.22);
    }
    .hero h1 {
        margin: 0;
        font-size: 2.15rem;
        letter-spacing: -0.03em;
    }
    .hero p {
        margin: 6px 0 0;
        color: #b8c2d9;
    }
    .hero-badge {
        white-space: nowrap;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(34, 197, 94, 0.12);
        border: 1px solid rgba(74, 222, 128, 0.22);
        color: #dcfce7;
        font-size: 0.84rem;
    }
    .status-card {
        padding: 12px 14px;
        border-radius: 12px;
        background: rgba(34, 197, 94, 0.09);
        border: 1px solid rgba(74, 222, 128, 0.16);
        color: #dcfce7;
    }
    .agent-card {
        padding: 14px;
        border-radius: 14px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.13), rgba(14, 165, 233, 0.08));
        border: 1px solid rgba(129, 140, 248, 0.16);
        margin-bottom: 12px;
    }
    .agent-card strong {
        font-size: 1.02rem;
        color: #f8fafc;
    }
    .welcome-card {
        margin-top: 20px;
        padding: 22px 24px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.045);
        border: 1px solid rgba(148, 163, 184, 0.16);
        color: #dbe5f5;
    }
    .welcome-card h3 {
        color: #f8fafc;
        margin: 0 0 8px;
    }
    .welcome-card p {
        color: #bac6dc;
        margin: 0;
    }
    div.stButton > button {
        border-radius: 10px;
        border: 1px solid rgba(129, 140, 248, 0.16);
        background: rgba(255, 255, 255, 0.045);
        color: #e5e7eb;
        text-align: left;
        transition: all 0.18s ease;
    }
    div.stButton > button:hover {
        border-color: rgba(129, 140, 248, 0.55);
        background: rgba(99, 102, 241, 0.12);
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def load_agent():
    return main.build_rag_chain()


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("## 📄 PDF AI Agent")
    st.caption("Ask questions from your PDF")

    st.markdown(
        """
        <div class="agent-card">
        <strong>Document Knowledge Agent</strong><br>
        <span style="color:#aeb8cf">PDF search · Explanation · Study help</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("### Start a conversation")
    suggestions = [
        "Summarize this PDF",
        "What are the main topics in this PDF?",
        "Explain the first major topic",
        "Give me important definitions",
        "Create 10 exam questions",
        "Explain the key concepts in simple language",
    ]
    for prompt in suggestions:
        if st.button(prompt, use_container_width=True):
            st.session_state.pending_question = prompt

    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


st.markdown(
    """
    <div class="hero">
        <div>
            <h1>PDF AI Agent</h1>
            <p>Read, understand, and ask questions about your PDF.</p>
        </div>
        <div class="hero-badge">● Ready to help</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome-card">
            <h3>Welcome! I'm your PDF AI assistant.</h3>
            <p>Ask a question about the document or choose a study prompt
            from the sidebar. Answers include PDF page references when available.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "📄"):
        st.markdown(message["content"])

pending_question = st.session_state.pop("pending_question", None)
question = pending_question or st.chat_input("Ask a question about the PDF...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="📄"):
        status = st.status("Starting the PDF agent…", expanded=True)
        try:
            with status:
                st.write("Loading PDF knowledge and connecting the answer model…")
                retriever, chain, vectorstore = load_agent()
                status.update(
                    label="PDF agent is ready. Preparing your answer…",
                    state="running",
                )
                answer = main.query_rag(question, retriever, chain, vectorstore)
            status.update(label="Answer ready", state="complete", expanded=False)
            st.markdown(answer)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )
        except (FileNotFoundError, RuntimeError) as exc:
            status.update(label="PDF agent setup failed", state="error")
            error_message = f"⚠️ **Setup error:** {exc}"
            st.error(error_message)
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message}
            )
        except Exception as exc:
            status.update(label="Could not generate an answer", state="error")
            error_message = (
                "Could not generate an answer. Check your Groq API key/model "
                f"and connection, then try again.\n\nDetails: `{exc}`"
            )
            st.error(error_message)
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message}
            )
