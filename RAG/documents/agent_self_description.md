# Agent Self-Description

## Overview
This agent is a modular, production-ready AI assistant designed for enterprise and research use. It leverages local LLMs, advanced retrieval-augmented generation (RAG), and a suite of integrated tools to automate knowledge work, document search, and business operations—all with full privacy and offline capability.

---

## Architecture
- **Core Frameworks:**
  - LangChain (LLM orchestration, tool integration)
  - LangGraph (agent state management, memory)
  - Ollama (local LLM and embedding models)
  - ChromaDB (vector database for semantic search)
  - Streamlit (web UI)
- **Main Agent:**
  - `agent_complete.py` orchestrates all tools and LLM calls
  - Uses `ChatOllama` with `qwen3:4b` (128K context, thinking mode)
  - Conversation memory via `MemorySaver`
  - System prompt enforces direct tool execution, concise answers
- **Tool System:**
  - Tools are Python functions decorated with `@tool` (LangChain)
  - Tools are imported from the `tools/` directory
  - Supported tools: web search, database query, Gmail, Excel logging, RAG document search
- **Document Handling:**
  - Universal loader (`RAG/document_loader.py`) supports PDF, Excel, CSV, Word, Text, JSON
  - Documents are chunked and embedded using `nomic-embed-text` (768d, 8192 tokens)
  - Chunks stored in persistent ChromaDB (`data/vector_db/`)
  - Upload via UI (`app.py`), CLI (`upload_documents.py`), or directory scan

---

## Workflow
1. **User Input:**
   - Via Streamlit chat UI or CLI
2. **Agent Reasoning:**
   - LLM (qwen3:4b) interprets query, decides which tool(s) to use
   - System prompt: "Execute tool calls immediately without asking permission. Be concise and direct."
3. **Tool Execution:**
   - If RAG: semantic search in ChromaDB, returns relevant document chunks
   - If database: queries SQLite (`data/customers.db`)
   - If Gmail: sends/reads emails via Gmail API
   - If logging: writes to Excel (`logs/agent_logs.xlsx`)
   - If web: uses DuckDuckGo or custom web tool
4. **Response Generation:**
   - LLM synthesizes results, returns concise answer
   - Logs interaction to Excel
5. **Memory:**
   - Conversation history maintained for context

---

## Model Switching & Extensibility
- **LLM:**
  - Default: `qwen3:4b` (128K context, tool calling, multilingual)
  - Easily switchable to other Ollama models (e.g., phi4-mini, gemma3, deepseek)
- **Embeddings:**
  - Default: `nomic-embed-text` (768d, 8192 tokens)
  - Switchable via `RAG/embeddings_config.py`
- **Tools:**
  - Add new tools by creating Python functions in `tools/` and importing in `agent_complete.py`
- **Documents:**
  - Supports batch upload, directory scan, and UI upload
  - Re-index required after changing embedding model

---

## Error Handling & Logging
- **Error Handling:**
  - Graceful fallback if tool/module unavailable
  - Embedding fallback to FakeEmbeddings if model missing
  - User-friendly error messages in UI and CLI
- **Logging:**
  - All interactions logged to `logs/agent_logs.xlsx`
  - Errors and warnings printed to console and UI

---

## Privacy & Security
- 100% local processing
- No cloud APIs or external data transfer
- Gmail integration uses OAuth2, credentials stored in `config/`
- Vector DB and logs are local and persistent

---

## Directory Structure
- `agent_complete.py` – Main agent logic
- `app.py` – Streamlit UI
- `RAG/` – RAG system (loader, vector store, embeddings)
- `tools/` – Agent tools
- `data/` – Databases, vector DB
- `logs/` – Excel logs
- `config/` – Credentials
- `docs/` – Documentation
- `tests/` – Test scripts
- `versions/` – Old agent versions

---

## Supported Document Types
- PDF, Excel (.xlsx), CSV, Word (.docx), Text (.txt), JSON

---

## Example Agent Questions
- "What models are currently used?"
- "How does the agent process documents?"
- "Where are logs and documents stored?"
- "How do I upload a new document?"
- "What tools are available to the agent?"
- "How does the agent ensure privacy?"
- "How do I add a new tool?"
- "How do I change the LLM or embedding model?"

---

## Maintenance & Customization
- **Re-index documents after embedding model change**
- **Update models via `ollama pull <model>`**
- **Add tools in `tools/`, import in `agent_complete.py`**
- **Documentation in `docs/`**
- **Test scripts in `tests/`**

---

## Contact & Help
- See documentation in `docs/`
- Ask the agent directly in chat
- For setup issues, see `docs/OLLAMA_SETUP.md`, `docs/QUICK_GUIDE.md`, `docs/PROJECT_EXPLANATION.md`
