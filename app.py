import streamlit as st
from agent_complete import call_complete_agent
from tools.excel_logger import get_log_summary, get_conversation_history, get_cached_response
import os
from pathlib import Path

# Try to import RAG components
try:
    from RAG.document_loader import DocumentLoader
    from RAG.vector_store import VectorStoreManager
    RAG_AVAILABLE = True
except ImportError:
    DocumentLoader = None
    VectorStoreManager = None
    RAG_AVAILABLE = False


with st.sidebar:
    # Improved sidebar layout
    # Fixed top: Features & Tools (smaller font, no image)

    if RAG_AVAILABLE:
        st.markdown("<div style='font-size:0.85em; margin-bottom:0.5em;'><b>📚 Document Management</b></div>", unsafe_allow_html=True)
        # --- Upload & Scan Section (Always Visible) ---
        st.markdown("<style>div[data-testid='stFileUploader'] input[type='file'] {font-size:0.78em; padding:0.18em 0.1em;} button, div[data-testid='stButton'] button {width:100%;font-size:0.78em;padding:0.22em 0.1em;margin-bottom:0.18em;border-radius:4px;}</style>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload files (PDF, Excel, CSV, Word, Text)",
            type=['pdf', 'xlsx', 'xls', 'csv', 'docx', 'txt', 'md', 'json'],
            accept_multiple_files=True,
            label_visibility="visible"
        )
        col1, col2 = st.columns([1,1], gap="small")
        with col1:
            process_clicked = st.button("Process Uploaded Files", key="process_files", help="Process and add uploaded documents to the database")
        with col2:
            scan_clicked = st.button("Scan Project Directory", key="scan_dir", help="Scan the RAG/documents directory for new files")
        # --- Document Processing Logic ---
        loader = DocumentLoader()
        vs = VectorStoreManager()
        total_docs = 0
        if uploaded_files and process_clicked:
            with st.spinner("Processing uploaded documents..."):
                for uploaded_file in uploaded_files:
                    try:
                        temp_path = Path("RAG/documents/uploads") / uploaded_file.name
                        temp_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        documents = loader.load_document(str(temp_path))
                        vs.add_documents(documents)
                        total_docs += len(documents)
                        st.success(f"✓ {uploaded_file.name}: {len(documents)} chunks")
                    except Exception as e:
                        st.error(f"✗ {uploaded_file.name}: {e}")
        if scan_clicked:
            doc_dir = Path("RAG/documents")
            if not doc_dir.exists():
                doc_dir.mkdir(parents=True, exist_ok=True)
                st.warning("Created RAG/documents/ directory. Please add files and scan again.")
            else:
                with st.spinner("Scanning directory..."):
                    try:
                        documents = loader.load_directory(str(doc_dir), recursive=True)
                        if documents:
                            vs.add_documents(documents)
                            total_docs += len(documents)
                            st.success(f"✓ Processed {len(documents)} document chunks")
                        else:
                            st.warning("No documents found in RAG/documents/")
                    except Exception as e:
                        st.error(f"Error: {e}")
        # --- Collapsible Document Stats & Search Section ---
        with st.expander("Document Stats & Search", expanded=False):
            try:
                stats = vs.get_stats()
                st.markdown("<div style='font-size:0.80em; margin-top:0.3em;'><b>Document Stats</b></div>", unsafe_allow_html=True)
                st.metric("Total Chunks", stats['document_count'])
                st.caption(f"Collection: {stats['collection_name']}")
                st.caption(f"Storage: {stats['persist_directory']}")
                # --- Search & Table Section ---
                st.markdown("<div style='font-size:0.80em; margin-top:0.3em;'><b>Search & List Documents</b></div>", unsafe_allow_html=True)
                filter_text = st.text_input("Filter documents by name:", "", key="doc_filter", label_visibility="visible")
                st.markdown("<style>div[data-testid='stTextInput'] input {font-size:0.78em; padding:0.18em 0.1em;}</style>", unsafe_allow_html=True)
                if stats['document_count'] > 0:
                    results = vs.similarity_search("", k=50)
                    doc_meta = []
                    for doc in results:
                        source = doc.metadata.get('source', 'Unknown')
                        doc_meta.append({
                            "name": Path(source).name,
                            "type": doc.metadata.get('type', 'Unknown'),
                            "size": doc.metadata.get('size', 'Unknown'),
                            "source": source
                        })
                    if filter_text:
                        doc_meta = [meta for meta in doc_meta if filter_text.lower() in meta['name'].lower()]
                    if doc_meta:
                        st.markdown("<table style='font-size:0.72em;width:100%;border-collapse:collapse;'><tr style='background:#f5f5f5;'><th align='left' style='padding:0.18em;'>Name</th><th align='left' style='padding:0.18em;'>Type</th><th align='left' style='padding:0.18em;'>Size</th><th align='left' style='padding:0.18em;'>Source</th></tr>" +
                            "".join([f"<tr><td style='padding:0.18em;'>{meta['name']}</td><td style='padding:0.18em;'>{meta['type']}</td><td style='padding:0.18em;'>{meta['size']}</td><td style='padding:0.18em;'>{meta['source']}</td></tr>" for meta in doc_meta]) + "</table>", unsafe_allow_html=True)
                    else:
                        st.info("No documents match the filter.")
            except Exception as e:
                st.error(f"Error loading document stats: {e}")
    st.markdown("---")

    # --- Session History Sidebar Section ---
    show_history = st.button("Show History", key="show_history", help="Display previous session history")
    if show_history:
        history = get_conversation_history(all_history=True)
        from collections import defaultdict
        import re, datetime
        # Group sessions by timestamp
        session_groups = defaultdict(list)
        for entry in history:
            match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", str(entry['timestamp']))
            session_key = match.group(1) if match else str(entry['timestamp'])
            session_groups[session_key].append(entry)
        sorted_sessions = sorted(session_groups.items(), reverse=True)
        # Prepare session summary list
        session_summaries = []
        for session_key, exchanges in sorted_sessions:
            dt = session_key.split()[1] if ' ' in session_key else session_key
            first_user = exchanges[0]['user_input'][:60] + ("..." if len(exchanges[0]['user_input']) > 60 else "")
            session_summaries.append({
                "label": f"{first_user} [{dt}]",
                "key": session_key,
                "exchanges": exchanges
            })
        st.markdown("<div style='font-size:0.85em;'><b>🗂️ Recent Sessions</b></div>", unsafe_allow_html=True)
        # Only apply compact style to session history buttons, not document management buttons
        if session_summaries:
            recent_sessions = session_summaries[:5]
            session_labels = [session["label"] for session in recent_sessions]
            selected_label = st.radio("Select a recent session:", session_labels, key="recent_session_radio", label_visibility="collapsed")
            # Find the selected session key
            for session in recent_sessions:
                if session["label"] == selected_label:
                    st.session_state.selected_session_key = session["key"]
                    break
            st.button("View All", key="view_all_sessions")
        else:
            st.info("No session history found.")
    # Note: session history UI is shown only when 'Show History' is clicked above.
    # The interactive recent sessions UI is intentionally not loaded by default to
    # avoid reading logs/history unless explicitly requested by the user.

    # Fixed bottom: Log Summary (smaller font)
    st.markdown("<hr style='margin:0.5em 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.85em;'><b>📊 Log Summary</b></div>", unsafe_allow_html=True)
    summary = get_log_summary()
    # Improved formatting for log summary
    if summary and summary.startswith("Log Summary:"):
        lines = summary.split("\n")
        summary_html = "<b>Log Summary:</b><br>"
        for line in lines[1:]:
            if line.strip():
                key_val = line.split(":", 1)
                if len(key_val) == 2:
                    key, val = key_val
                    summary_html += f"<b>{key.strip()}:</b> {val.strip()}<br>"
                else:
                    summary_html += line + "<br>"
    else:
        summary_html = summary.replace(" - ", "<br>") if summary else ""
    st.markdown(f"<div style='font-size:0.85em;text-align:left;'>{summary_html}</div>", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history

if st.session_state.messages:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
else:
    st.markdown("""
    <h2 style='margin-top:0.5em;'>👋 Welcome to your AI Agent!</h2>
    <div style='font-size:1.05em; margin-bottom:1em;'>Ask me anything, or use the tools below:</div>
    <div style='font-size:0.98em; margin-bottom:1.2em; display:flex; flex-wrap:wrap; gap:1.2em;'>
      <span>👥 <b>Customer database</b></span>
      <span>📧 <b>Gmail integration</b></span>
      <span>📚 <b>Document search (RAG)</b></span>
      <span>📊 <b>Excel logging</b></span>
    </div>
    """, unsafe_allow_html=True)

# Chat input
if query := st.chat_input("Ask me anything! I can search the web or check customer info."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            response = call_complete_agent(query)
            # Always display agent response
            st.write(response)

            # --- Auto-visualization for tabular sales/order/trend data ---
            import pandas as pd
            import re
            def parse_table(text):
                # Detects and parses markdown or pipe-delimited tables
                lines = text.splitlines()
                table_lines = [l for l in lines if '|' in l]
                if len(table_lines) < 2:
                    return None
                # Remove markdown header separator if present
                if re.match(r"^\s*\|?\s*-+\s*\|", table_lines[1]):
                    table_lines.pop(1)
                # Parse table
                data = [re.split(r"\s*\|\s*", l.strip().strip('|')) for l in table_lines]
                if len(data) < 2:
                    return None
                df = pd.DataFrame(data[1:], columns=data[0])
                return df

            # Only visualize if keywords are present
            keywords = ['order', 'sales', 'trend', 'amount', 'date', 'product', 'status']
            try:
                if any(k in query.lower() for k in keywords):
                    df = parse_table(str(response))
                    if df is not None:
                        # Try to convert numeric columns
                        for col in df.columns:
                            try:
                                df[col] = pd.to_numeric(df[col].str.replace('$','').str.replace(',',''))
                            except Exception:
                                pass
                        # Show chart if possible
                        numeric_cols = df.select_dtypes(include='number').columns
                        if 'Amount' in df.columns or 'amount' in df.columns:
                            st.bar_chart(df.set_index(df.columns[0])[numeric_cols])
                        elif len(numeric_cols) > 0:
                            st.line_chart(df.set_index(df.columns[0])[numeric_cols])
            except Exception as e:
                st.info(f"[Visualization error] {e}")