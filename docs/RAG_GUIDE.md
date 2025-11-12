# RAG (Retrieval Augmented Generation) Setup Guide

## 📚 Overview

Your AI agent now includes **RAG capabilities** to search and retrieve information from uploaded documents. The system supports:

- **PDF documents** (.pdf)
- **Excel spreadsheets** (.xlsx, .xls)
- **CSV files** (.csv)
- **Word documents** (.docx)
- **Text files** (.txt, .md)
- **JSON files** (.json)

## 🚀 Quick Start

### 1. Install RAG Dependencies

```bash
pip install chromadb sentence-transformers pypdf pdfplumber python-docx unstructured tiktoken
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### 2. Upload Documents

#### Upload a single document:
```bash
python upload_documents.py upload path/to/document.pdf
```

#### Upload all documents from a folder:
```bash
python upload_documents.py upload-dir RAG/documents/
```

#### List uploaded documents:
```bash
python upload_documents.py list
```

#### Show supported formats:
```bash
python upload_documents.py formats
```

### 3. Use in Chat

Once documents are uploaded, ask questions:
- "Search my documents for information about Python"
- "What documents have been uploaded?"
- "Find information about sales in my Excel files"

## 📋 Detailed Usage

### Document Upload Commands

```bash
# Upload single file with chunking (recommended)
python upload_documents.py upload document.pdf

# Upload without chunking (for small documents)
python upload_documents.py upload document.pdf --no-chunk

# Upload entire directory (recursive)
python upload_documents.py upload-dir RAG/documents/

# Upload directory without subdirectories
python upload_documents.py upload-dir RAG/documents/ --no-recursive

# List all documents in database
python upload_documents.py list

# Clear entire database (warning: irreversible!)
python upload_documents.py clear

# Show supported file formats
python upload_documents.py formats
```

### Example Queries in Chat Interface

**Check what's available:**
```
"What documents are in the system?"
"Show me document statistics"
"List all uploaded files"
```

**Search for information:**
```
"Search for Python tutorials in my documents"
"Find information about quarterly sales"
"What does my contract say about payments?"
"Search Excel files for customer data"
```

**Combined queries:**
```
"Search my documents for Python info and also search the web for latest news"
"Find customer Smith in the database and search our documents for their contract"
```

## 🏗️ Architecture

### Project Structure

```
agent/
├── RAG/
│   ├── __init__.py               # Module initialization
│   ├── document_loader.py        # Universal document loader
│   ├── vector_store.py           # Vector database manager
│   ├── embeddings_config.py      # Embedding model configuration
│   └── documents/                # Store your documents here
│       ├── pdfs/
│       ├── excel/
│       └── others/
├── tools/
│   └── rag_tools.py              # RAG tools for agent
├── data/
│   └── vector_db/                # ChromaDB storage (auto-created)
├── upload_documents.py           # Document upload utility
└── agent_complete.py             # Main agent (now includes RAG)
```

### How It Works

1. **Document Loading**: Files are parsed based on type
2. **Text Chunking**: Large documents split into manageable chunks (1000 chars)
3. **Embedding**: Text converted to vector embeddings using HuggingFace
4. **Storage**: Vectors stored in ChromaDB (local, persistent)
5. **Retrieval**: Similarity search finds relevant chunks
6. **Agent Integration**: Results provided to AI for answering questions

## 🔧 Configuration

### Embedding Models

By default, the system uses **HuggingFace embeddings** (free, local, no setup required).

To use **Ollama embeddings** instead:

```bash
# Pull the embedding model
ollama pull nomic-embed-text

# Modify RAG/embeddings_config.py
# Change default from 'huggingface' to 'ollama'
```

### Vector Store Settings

Edit `RAG/vector_store.py` to customize:

```python
# Chunk size and overlap
chunk_size=1000      # Characters per chunk
chunk_overlap=200    # Overlap between chunks

# Search parameters
k=4                  # Number of results to return
```

### Storage Location

Default: `data/vector_db/`

To change, modify `tools/rag_tools.py`:

```python
VectorStoreManager(
    persist_directory="your/custom/path",
    collection_name="documents"
)
```

## 📊 Document Processing Details

### PDF Files
- Uses PyPDFLoader for standard PDFs
- Falls back to UnstructuredPDFLoader for complex PDFs
- Preserves page numbers in metadata

### Excel/CSV Files
- Each Excel sheet becomes a separate document
- Includes summary statistics (rows, columns)
- Preserves data structure and formatting

### Word Documents
- Extracts all paragraphs
- Maintains document structure
- Requires `python-docx` package

### Text/Markdown
- Direct loading without processing
- Preserves formatting

## 🎯 Best Practices

### Document Organization

```
RAG/documents/
├── pdfs/
│   ├── contracts/
│   ├── reports/
│   └── manuals/
├── excel/
│   ├── sales_data.xlsx
│   └── customer_lists.xlsx
└── others/
    ├── notes.txt
    └── meeting_notes.md
```

### Chunking Strategy

- **Use chunking** (default) for long documents (>10 pages)
- **No chunking** for short documents or when context is critical
- Overlap ensures no information is lost at boundaries

### Query Tips

**Be specific:**
✅ "Search for Python error handling in my documents"
❌ "Python"

**Use context:**
✅ "Find sales figures for Q4 in my Excel files"
❌ "Sales"

**Combine tools:**
✅ "Search my documents about AI, then search the web for latest news"

## 🐛 Troubleshooting

### "No documents uploaded"
- Run `python upload_documents.py list` to verify
- Upload documents using `upload` or `upload-dir` commands

### ChromaDB errors
```bash
# Clear and reinstall
pip uninstall chromadb
pip install chromadb
```

### PDF loading fails
```bash
# Install additional dependencies
pip install pdfplumber unstructured
```

### Word documents not supported
```bash
pip install python-docx
```

### Slow embedding generation
- First run downloads HuggingFace model (~90MB)
- Subsequent runs are fast
- Consider using Ollama embeddings for GPU acceleration

### Out of memory errors
- Reduce chunk_size in `vector_store.py`
- Process documents in smaller batches
- Use `--no-chunk` for very small documents

## 📈 Performance

**Embedding Model:**
- HuggingFace: ~100 docs/min (CPU)
- Ollama: ~500 docs/min (GPU)

**Search Speed:**
- Typically < 500ms for 1000s of documents
- ChromaDB handles millions of vectors efficiently

**Storage:**
- ~1MB per 100 document chunks
- Persistent across restarts

## 🔐 Privacy & Security

✅ **Completely Local** - All data stays on your machine
✅ **No Cloud API** - No data sent to external services
✅ **Persistent Storage** - Documents available after restart
✅ **Secure** - ChromaDB stored locally in `data/vector_db/`

## 🚀 Advanced Usage

### Programmatic Document Upload

```python
from RAG.document_loader import DocumentLoader
from RAG.vector_store import VectorStoreManager

# Initialize
loader = DocumentLoader()
vs = VectorStoreManager()

# Load and add documents
documents = loader.load_document("path/to/file.pdf")
vs.add_documents(documents)

# Search
results = vs.similarity_search("my query", k=5)
for doc in results:
    print(doc.page_content)
```

### Custom Metadata Filters

```python
# Search only PDFs
results = vs.similarity_search(
    "query",
    k=5,
    filter_dict={'type': 'pdf'}
)

# Search specific source
results = vs.similarity_search(
    "query",
    filter_dict={'source': 'contract.pdf'}
)
```

### Batch Processing

```python
# Load entire directory
documents = loader.load_directory("RAG/documents/", recursive=True)

# Add in batches
batch_size = 100
for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    vs.add_documents(batch)
    print(f"Processed {i+batch_size}/{len(documents)}")
```

## 📚 Additional Resources

- **ChromaDB Documentation**: https://docs.trychroma.com/
- **LangChain RAG Guide**: https://python.langchain.com/docs/use_cases/question_answering/
- **Sentence Transformers**: https://www.sbert.net/

## 🤝 Integration with Agent

The RAG system automatically integrates with your agent:

**Available Tools:**
- `search_documents` - Search uploaded documents
- `list_document_sources` - List all uploaded documents  
- `get_document_stats` - Get database statistics

**Agent System Message:**
The agent is automatically configured to use RAG tools when appropriate.

**Logging:**
All RAG queries are logged to `agent_logs.xlsx` like other tool usage.

---

**Need Help?**
- Check document upload status: `python upload_documents.py list`
- View supported formats: `python upload_documents.py formats`
- Clear and restart: `python upload_documents.py clear`

**Built with:** LangChain, ChromaDB, HuggingFace Transformers
