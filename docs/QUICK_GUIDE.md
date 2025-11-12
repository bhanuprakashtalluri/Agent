# AI Agent - Quick Guide

## What is This?

A **smart AI assistant** that can:
- 🔍 Search the web and read websites
- 👥 Query customer database
- 📧 Manage Gmail emails
- 📊 Auto-log all interactions to Excel

## Quick Start

```bash
# 1. Install Ollama (local AI model)
brew install ollama

# 2. Start Ollama and pull model
ollama serve  # Keep running in background
ollama pull llama3.2:1b  # In another terminal

# 3. Install Python packages
pip install -r requirements.txt

# 4. Setup database
python setup_database.py

# 5. Run the app
streamlit run app.py
```

## Architecture Overview

```
User → Streamlit UI → Agent → Tools → Data Sources
                        ↓
                   Excel Logger
```

### Components

**1. Agents (Brain)**
- `agent2.py` - Web search only
- `agent3.py` - Web + Database
- `agent_complete.py` - All features + logging

**2. Tools (Hands)**
- `tools/visit_web.py` - Scrape websites
- `tools/query_database.py` - Query SQLite DB
- `tools/gmail_tools.py` - Email operations
- `tools/excel_logger.py` - Auto-logging

**3. UI**
- `app.py` - Streamlit chat interface

## Key Concepts

### 1. **LangGraph Agent**
Creates AI agents that can use tools intelligently.

```python
agent = create_agent(model, tools, checkpointer=memory)
```

### 2. **Local LLM (Ollama)**
Runs AI model on your machine - free, private, fast.

```python
model = ChatOllama(model="llama3.2:1b")
```

### 3. **Tool Pattern**
Functions the AI can call when needed.

```python
@tool
def query_customer_info(name: str) -> str:
    """Search customer by name"""
    # Query database
    return result
```

### 4. **Memory**
Remembers conversation history.

```python
memory = MemorySaver()
config = {"configurable": {"thread_id": "abc123"}}
```

## Tools Explained

### Web Tools
- **DuckDuckGoSearchResults** - Search engine
- **visit_web(url)** - Extract content from websites

### Database Tools
- **query_customer_info(name)** - Get customer details
- **query_customer_orders(name)** - Get order history
- **list_all_customers()** - List all customers

### Gmail Tools (Optional)
- **search_gmail(query)** - Search emails
- **read_gmail(id)** - Read email content
- **send_gmail(to, subject, body)** - Send email

## Example Queries

**Customer Service:**
```
"Show me John Doe's orders"
"List all active customers"
"What's Alice Brown's account balance?"
```

**Web Research:**
```
"Search for Python tutorials"
"Find latest AI news"
"What's new in LangChain?"
```

**Email (if configured):**
```
"Search emails from john@example.com"
"Find unread emails today"
```

## Files Structure

```
agent/
├── app.py                    # Streamlit UI
├── agent2.py                 # Web agent
├── agent3.py                 # Web + DB agent
├── agent_complete.py         # Full agent + logging
├── setup_database.py         # Creates sample DB
├── requirements.txt          # Dependencies
├── config/                   # Configuration
│   ├── gmail_credentials.json
│   └── gmail_token.json
├── data/                     # Data storage
│   ├── customers.db              # SQLite database
│   └── agent_logs.xlsx           # Auto-generated logs
├── docs/                     # Documentation
│   ├── PROJECT_EXPLANATION.md   # Detailed docs
│   ├── OLLAMA_SETUP.md          # Ollama guide
│   ├── QUICK_GUIDE.md           # This file
│   └── OPTIMIZATION_SUMMARY.md  # Optimization details
├── versions/                 # Previous versions
│   ├── versiondata.md
│   ├── agent.py
│   ├── agent2.py
│   └── agent3.py
└── tools/                    # Tool modules
    ├── visit_web.py
    ├── query_database.py
    ├── gmail_tools.py
    └── excel_logger.py
```

## How It Works

1. **User asks question** → Streamlit interface
2. **Agent receives** → Wrapped in messages
3. **LLM decides** → Which tools to use
4. **Tools execute** → Query DB, search web, etc.
5. **Agent synthesizes** → Combines results
6. **Response shown** → In chat UI
7. **Auto-logged** → To Excel (complete agent)

## Design Patterns

### Tool Decorator
```python
@tool
def my_tool(param: str) -> str:
    """What this tool does"""
    return result
```

### System Message
```python
SystemMessage(content="You are a helpful assistant...")
```
Guides agent behavior and tool usage.

### Graceful Degradation
```python
try:
    from tools.gmail_tools import search_gmail
    gmail_available = True
except:
    gmail_available = False
```
Works even if some features fail.

## Technology Stack

| Tech | Purpose |
|------|---------|
| LangChain | LLM framework |
| LangGraph | Agent orchestration |
| Ollama | Local LLM |
| Streamlit | Web UI |
| SQLite | Database |
| Gmail API | Email integration |
| OpenPyXL | Excel logging |

## Gmail Setup (Optional)

1. Go to Google Cloud Console
2. Create project & enable Gmail API
3. Create OAuth credentials (Desktop app)
4. Download as `gmail_credentials.json`
5. First run will authenticate in browser

## Advantages

✅ **Free** - Local LLM, no API costs  
✅ **Private** - Data stays on your machine  
✅ **Fast** - No network latency  
✅ **Modular** - Easy to add tools  
✅ **Observable** - Excel logs everything  
✅ **User-friendly** - Chat interface  

## Common Issues

**Ollama not found:**
```bash
brew install ollama
ollama serve
```

**Model missing:**
```bash
ollama pull llama3.2:1b
```

**Database not found:**
```bash
python setup_database.py
```

## Next Steps

1. **Run the app** - `streamlit run app.py`
2. **Try queries** - Test different agent capabilities
3. **Check logs** - Open `data/agent_logs.xlsx`
4. **Add tools** - Create custom tools in `tools/`
5. **Read detailed docs** - See `PROJECT_EXPLANATION.md` (in same folder)

---

**For detailed documentation, see:** `PROJECT_EXPLANATION.md`  
**For Ollama setup help, see:** `OLLAMA_SETUP.md`  
**For optimization details, see:** `OPTIMIZATION_SUMMARY.md`
