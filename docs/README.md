# Documentation Overview

A production-ready agent built with LangChain, LangGraph, and Ollama. The assistant can search the web, query the bundled customer database, process emails, log every interaction, and run retrieval-augmented generation (RAG) over uploaded documents.

## Core Features

- Web search and content extraction via DuckDuckGo plus HTML-to-Markdown conversion
- Customer and order lookups against the bundled SQLite database
- Optional Gmail integration for reading, searching, and sending mail
- Retrieval-augmented document search across PDFs, Office files, CSV, and text
- Automatic logging of every conversation to an Excel workbook
- Streamlit chat interface that runs entirely on your machine

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.11+ | Create a virtual environment for isolation |
| Ollama | Provides the local LLM (`brew install ollama` on macOS) |
| (Optional) Google Cloud project | Needed only for Gmail features |

## Quick Start

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Install and start Ollama**
   ```bash
   brew install ollama              # macOS
   ollama serve                     # terminal 1
   ollama pull llama3.2:1b          # terminal 2
   ```
3. **Initialize sample data**
   ```bash
   python setup_database.py
   ```
4. **Launch the Streamlit app**
   ```bash
   streamlit run app.py
   ```
   Then open <http://localhost:8501> in your browser.

## Optional: Gmail Setup

1. Create a Google Cloud project and enable the Gmail API.
2. Generate OAuth client credentials (Desktop app) and download the JSON file.
3. Save the file as `config/gmail_credentials.json` in the project root.
4. On the first Gmail-enabled request the browser flow will run and the token will be saved to `config/gmail_token.json`.

> Skip this section if you do not need email capabilities. The agent runs without Gmail access.

## Project Layout

```
agent/
├── app.py                   # Streamlit UI
├── agent_complete.py        # Main orchestration logic
├── setup_database.py        # Seeds the SQLite database
├── tools/                   # Tool implementations (web, db, gmail, rag, logging)
├── RAG/                     # Document loader and vector store helpers
├── data/                    # SQLite DB, vector store, logs
├── docs/                    # Documentation (this folder)
└── config/                  # OAuth credentials and tokens
```

## Choosing an Agent Profile

The Streamlit sidebar exposes three presets:
- **Complete Agent** – Web, database, logging, RAG, and Gmail (if configured).
- **Full Agent** – Web plus database access, no Gmail or Excel logging.
- **Web Agent** – Web search and scraping only.

## Example Prompts

- "List all active customers"
- "Search the web for the latest LangChain announcements"
- "Email Sarah the most recent order summary" *(requires Gmail setup)*
- "Search my documents for quarterly revenue"

## Document (RAG) Workflow

```
python upload_documents.py upload sample.pdf            # single file
python upload_documents.py upload-dir RAG/documents/    # entire folder
python upload_documents.py list                         # list indexed docs
```

After uploading, use prompts such as "Search my documents for Python tutorials". Detailed guidance lives in `docs/RAG_GUIDE.md`.

## Excel Conversation Log

Every interaction is appended to `logs/agent_logs.xlsx` with timestamp, tools used, sources, model output, and status. Open the workbook directly or view the summary card in the Streamlit sidebar.

## Database Schema Reference

**customers**: `id`, `name`, `email`, `phone`, `status`, `account_balance`, `join_date`

**orders**: `id`, `customer_id`, `order_number`, `product`, `amount`, `status`, `order_date`

## Troubleshooting

- **Ollama not running**: `ollama serve`
- **Model missing**: `ollama pull llama3.2:1b`
- **Gmail issues**: verify the credentials file, delete `config/gmail_token.json`, and retry authentication
- **Excel errors**: confirm `openpyxl` is installed and the `logs/` directory is writable

## Additional Documentation

- Quick guide: `docs/QUICK_GUIDE.md`
- Architecture deep dive: `docs/PROJECT_EXPLANATION.md`
- Ollama setup tips: `docs/OLLAMA_SETUP.md`
- Optimization notes: `docs/OPTIMIZATION_SUMMARY.md`

Refer to the remaining files in this `docs/` directory for focused workflows (e.g., Gmail fixes, RAG operations, optimization strategies).

## Contributing

Pull requests and issue reports are welcome. Ideas include expanding the toolset, tuning caching strategies, adding analytics, or improving documentation.
