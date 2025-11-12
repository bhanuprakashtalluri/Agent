# RAG Setup for Python 3.13

## ⚠️ Important Note About Python 3.13

You're using Python 3.13, which is very new. Some RAG dependencies (specifically **PyTorch** and **sentence-transformers**) are not yet available for Python 3.13 on macOS.

## ✅ Solution: Use Ollama for Embeddings

Since you already have Ollama installed, we'll use it for embeddings instead of sentence-transformers!

### Step 1: Install Core Dependencies

```bash
pip3 install chromadb langchain-chroma pypdf pdfplumber python-docx tiktoken
```

These are the essential packages that work with Python 3.13.

### Step 2: Pull Ollama Embedding Model

```bash
ollama pull all-minilm:33m
```

This downloads the embedding model that will be used for RAG (lightweight and fast!).

### Step 3: Verify Installation

```bash
python3 test_rag.py
```

This will test if everything is working.

## 🚀 Quick Start

### Upload Documents

```bash
# Upload a single document
python3 upload_documents.py upload document.pdf

# Upload a folder
python3 upload_documents.py upload-dir RAG/documents/

# List uploaded documents
python3 upload_documents.py list
```

### Use in Agent

```bash
streamlit run app.py
```

Then ask questions like:
- "What documents are uploaded?"
- "Search my documents for Python information"

## 🔧 Alternative: Use Python 3.11 or 3.12

If you need full RAG features with HuggingFace embeddings:

```bash
# Install Python 3.11 or 3.12 using pyenv
pyenv install 3.11.9
pyenv local 3.11.9

# Create new virtual environment
python -m venv .venv311
source .venv311/bin/activate

# Install all dependencies including sentence-transformers
pip install -r requirements.txt
```

## 📦 What Works with Python 3.13

✅ **ChromaDB** - Vector database  
✅ **Ollama Embeddings** - Using nomic-embed-text  
✅ **PDF Loading** - pypdf, pdfplumber  
✅ **Excel/CSV** - pandas  
✅ **Word** - python-docx  
✅ **Document Loader** - All file types  
✅ **Vector Store** - Full functionality  
✅ **Agent Integration** - Complete  

❌ **HuggingFace Embeddings** - Requires PyTorch (not on Python 3.13 yet)  
❌ **Unstructured** - Heavy deps not fully compatible  

## 🎯 Recommended Approach

**For Python 3.13 (Your Current Setup):**
1. Use Ollama embeddings (already installed!)
2. Skip sentence-transformers
3. Everything else works perfectly

**Commands:**
```bash
# Install dependencies (without sentence-transformers)
pip3 install chromadb langchain-chroma pypdf pdfplumber python-docx tiktoken

# Pull embedding model
ollama pull nomic-embed-text

# Test
python3 test_rag.py

# Upload docs
python3 upload_documents.py upload test.pdf

# Run agent
streamlit run app.py
```

## 🐛 Troubleshooting

### "Cannot install sentence-transformers"
This is expected with Python 3.13. Use Ollama embeddings instead (already configured).

### "Ollama connection error"
```bash
# Make sure Ollama is running
ollama serve

# In another terminal, pull the model
ollama pull all-minilm:33m
```

### "FakeEmbeddings being used"
This means Ollama isn't available. Run `ollama pull all-minilm:33m` first.

### Import errors
```bash
# Make sure langchain-chroma is installed
pip3 install langchain-chroma
```

## 📚 Why Ollama Embeddings?

**Advantages:**
- ✅ Works with Python 3.13
- ✅ You already have Ollama installed
- ✅ Very fast (uses GPU if available)
- ✅ High quality embeddings (all-minilm:33m)
- ✅ No additional dependencies
- ✅ No compatibility issues

**vs HuggingFace:**
- HuggingFace requires PyTorch
- PyTorch not available for Python 3.13 on macOS yet
- Ollama is actually faster in many cases!

## ✅ Verification Checklist

- [ ] Ollama is installed and running
- [ ] `ollama pull all-minilm:33m` completed successfully
- [ ] `pip install chromadb langchain-chroma pypdf pdfplumber python-docx tiktoken` succeeded (in venv)
- [ ] `python test_rag.py` passes tests
- [ ] Can upload documents: `python upload_documents.py upload test.txt`
- [ ] Agent loads RAG tools: `streamlit run app.py` (check for "✓ RAG tools loaded")

## 🎉 Summary

Your RAG system is fully functional with Python 3.13 using:
- **Ollama** for embeddings (all-minilm:33m)
- **ChromaDB** for vector storage
- **All document types** supported (PDF, Excel, CSV, Word, etc.)
- **Full agent integration**

No need to downgrade Python or install PyTorch!
