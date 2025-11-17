# Data Directory

Persistent application data lives in this folder. The main artifacts are:

- `customers.db`: Sample SQLite database seeded by `setup_database.py`.
- `vector_db/`: Chroma vector store used by the RAG pipeline (auto-created).
- `query_store.sqlite3`: Lightweight cache of prior LLM and SQL requests.
- `logs/` or Excel exports written by the agent (created on demand).

Avoid committing large generated files. You can safely delete subfolders to force a rebuild—the application will recreate them when required.
