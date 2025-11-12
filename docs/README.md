A production-ready AI agent built with LangChain, LangGraph, and Ollama that can search the web, query databases, manage emails, and automatically log all interactions.

## ✨ Features

This AI agent includes:

1. **🔍 Web Search & Scraping** - DuckDuckGo search + web content extraction
2. **👥 Customer Database** - SQLite database with customer and order data
3. **📧 Gmail Integration** - Search, read, and send emails
4. **📚 RAG Document Search** - Upload and search PDFs, Excel, CSV, Word docs
5. **📊 Excel Logging** - Automatic logging of all interactions
6. **💬 Chat Interface** - Clean Streamlit UI with conversation history
7. **🔒 Privacy First** - Runs locally with Ollama (no cloud API costs)

## 📦 Installation

## 🚀 Quick Start

### 1. Install Python Dependencies

### 1. Install Ollama (Local AI)

```bash```bash

# macOSpip install -r requirements.txt

brew install ollama```

# Or download from https://ollama.ai### 2. Set up Gmail API (Optional but recommended)

```

To use Gmail features, you need to set up OAuth2 credentials:

### 2. Start Ollama & Pull Model

```bash#### Step 1: Create Google Cloud Project

# Terminal 1 - Start service (keep running)1. Go to [Google Cloud Console](https://console.cloud.google.com/)

ollama serve2. Create a new project or select existing one

3. Enable the Gmail API:

# Terminal 2 - Pull model   - Navigate to "APIs & Services" > "Library"

ollama pull llama3.2:1b   - Search for "Gmail API"

```   - Click "Enable"


### 3. Install Dependencies#### Step 2: Create OAuth2 Credentials

```bash1. Go to "APIs & Services" > "Credentials"

pip install -r requirements.txt2. Click "Create Credentials" > "OAuth client ID"

```3. Configure consent screen if prompted:

   - User Type: External

### 4. Setup Database   - App name: "AI Agent"

```bash   - Add your email as test user

python setup_database.py4. Application type: "Desktop app"

```5. Download the credentials JSON file

6. Save it as `gmail_credentials.json` in the project root

### 5. Run the App

```bash#### Step 3: First-time Authentication

streamlit run app.pyWhen you first use Gmail features, the agent will:

```1. Open a browser window for authentication

2. Ask you to login with your Google account

Visit http://localhost:8501 in your browser.3. Save the token to `gmail_token.json` for future use



## 📁 Project Structure**Note:** If you skip Gmail setup, the agent will work fine without email features.



```## 🚀 Usage

agent/

├── app.py                    # Streamlit UI### Run the Streamlit App

├── agent_complete.py         # Main agent with all tools

├── setup_database.py         # Database initialization```bash

├── requirements.txt          # Python dependenciesstreamlit run app.py

│```

├── config/                   # Configuration files

│   ├── gmail_credentials.json   # Gmail OAuth (create this)### Choose Your Agent Type

│   └── gmail_token.json         # Auto-generated token

│The app offers three agent configurations:

├── data/                     # Data storage

│   ├── customers.db             # SQLite database1. **Complete Agent (All Tools)** - Recommended

│   └── agent_logs.xlsx          # Interaction logs   - All features enabled

│   - Automatic Excel logging

├── tools/                    # Tool modules   - Filesystem caching

│   ├── visit_web.py             # Web scraping   - Gmail integration

│   ├── query_database.py        # Database queries

│   ├── gmail_tools.py           # Email operations2. **Full Agent (Web + Database)**

│   └── excel_logger.py          # Logging utility   - Web search and scraping

│   - Customer database access

├── docs/                     # Documentation   - No logging or Gmail

│   ├── PROJECT_EXPLANATION.md   # Detailed technical docs

│   └── OLLAMA_SETUP.md          # Ollama setup guide3. **Web Agent Only**

│   - Just web search and scraping

├── versions/                 # Previous agent versions   - Minimal features

│   ├── agent.py                 # Basic version

│   ├── agent2.py                # Web-only agent## 📂 Project Structure

│   └── agent3.py                # Web + Database agent

│```

└── cache/                    # Cached responsesagent/

```├── app.py                      # Streamlit UI

├── agent2.py                   # Web-only agent

## 🛠️ Tools Available├── agent3.py                   # Web + Database agent

├── agent_complete.py           # Complete agent with all tools

### Web Tools├── requirements.txt            # Python dependencies

- **DuckDuckGo Search** - Find information on the web├── customers.db                # SQLite database

- **Web Scraper** - Extract and read website content├── agent_logs.xlsx            # Excel log (auto-created)

├── gmail_credentials.json      # Gmail OAuth (you create this)

### Database Tools├── gmail_token.json           # Gmail token (auto-created)

- **Query Customer Info** - Search customers by name├── cache/                     # Cached markdown files (auto-created)

- **Query Orders** - Get order history for customers│   └── *.md

- **List All Customers** - View all customers with status└── tools/

    ├── visit_web.py           # Web scraping tool

### Gmail Tools (Optional)    ├── query_database.py      # Database query tools

- **Search Emails** - Use Gmail syntax to find emails    ├── filesystem_cache.py    # Cache management

- **Read Email** - Get full email content    ├── gmail_tools.py         # Gmail integration

- **Send Email** - Send emails to recipients    └── excel_logger.py        # Excel logging utility

```

## 📝 Example Queries

## 💡 Example Queries

### Customer Service

```### Customer Database

"Show me John Doe's information"- "List all customers"

"What orders does Jane Smith have?"- "Show me John Doe's information"

"List all active customers"- "What orders does Jane Smith have?"

"What's Alice Brown's account balance?"- "What's Alice Brown's account balance?"

```

### Web Search

### Web Research- "What's the latest news about Python?"

```- "Search for machine learning tutorials"

"Search for latest Python news"- "Find information about LangChain"

"Find tutorials on LangChain"

"What's new in AI this week?"### Gmail (if configured)

```- "Search for emails from john@example.com"

- "Find unread emails from today"

### Email Operations- "Search for emails with subject containing 'invoice'"

```

"Search for emails from john@example.com"### File Management

"Find unread emails from today"- "Save this response to cache"

"Read email with ID abc123"- "List all cached files"

```- "Read the cached file from yesterday"



### Document Search (RAG)

```
"What documents have been uploaded?"
"Search my documents for Python tutorials"
"Find sales data in my Excel files"
"What does the contract say about payments?"
```

### Mixed Queries

```
"Look up customer John Doe and email me his order history"
"Search for CRM best practices and show me our top customers"
"Search my documents about AI and also search the web for latest news"
```

## 📚 RAG Document Search

**NEW: Upload and search your documents!**

Supported file types:
- PDF documents (.pdf)
- Excel spreadsheets (.xlsx, .xls)
- CSV files (.csv)
- Word documents (.docx)
- Text files (.txt, .md)
- JSON files (.json)

**Quick Start:**
```bash
# Upload a document
python upload_documents.py upload document.pdf

# Upload entire folder
python upload_documents.py upload-dir RAG/documents/

# List uploaded documents
python upload_documents.py list
```

**Example Queries:**
- "What documents are in the system?"
- "Search my documents for Python information"
- "Find quarterly sales in my Excel files"

**See full documentation:** `docs/RAG_GUIDE.md`

## 📊 Excel Logging



## 🔐 Gmail Setup (Optional)All interactions are automatically logged to `agent_logs.xlsx` with:

- Timestamp

If you want email features:- User input

- Tools used

1. **Create Google Cloud Project**- Sources/URLs visited

   - Go to [Google Cloud Console](https://console.cloud.google.com/)- Output

   - Create new project- Status (Success/Error)

   - Enable Gmail API

View the log summary in the sidebar of the Streamlit app.

2. **Create OAuth Credentials**

   - Navigate to APIs & Services → Credentials## 🗄️ Database Schema

   - Create OAuth 2.0 Client ID (Desktop app)

   - Download credentials JSON### Customers Table

- id (PRIMARY KEY)

3. **Save Credentials**- name

   ```bash- email

   # Save downloaded file as:- phone

   config/gmail_credentials.json- status

   ```- account_balance

- join_date

4. **First Run Authentication**

   - Agent will open browser for authentication### Orders Table

   - Grant permissions- id (PRIMARY KEY)

   - Token saved automatically to `config/gmail_token.json`- customer_id (FOREIGN KEY)

- order_number

**Note:** The agent works perfectly fine without Gmail setup. Email features will simply be unavailable.- product

- amount

## 💾 Database Schema- status

- order_date

### Customers Table

- `id` - Primary key## 🔧 Troubleshooting

- `name` - Customer name

- `email` - Email address### Gmail Not Working

- `phone` - Phone number- Make sure `gmail_credentials.json` exists

- `status` - Active/Inactive- Check that Gmail API is enabled in Google Cloud Console

- `account_balance` - Account balance- Delete `gmail_token.json` and re-authenticate if issues persist

- `join_date` - Join date

### Excel Logging Errors

### Orders Table- Ensure `openpyxl` is installed: `pip install openpyxl`

- `id` - Primary key- Check write permissions in the project directory

- `customer_id` - Foreign key to customers

- `order_number` - Order number### Cache Directory Issues

- `product` - Product name- The `cache/` directory is auto-created

- `amount` - Order amount- Check write permissions

- `status` - Delivered/Shipped/Processing

- `order_date` - Order date## 🎨 Customization



## 📊 Excel Logging### Add More Customers

Edit `setup_database.py` and run:

All interactions are automatically logged to `data/agent_logs.xlsx`:```bash

python3 setup_database.py

**Columns:**```

- Timestamp

- User Input### Modify Agent Behavior

- Tools UsedEdit the system message in `agent_complete.py` to change how the agent uses tools.

- Sources/URLs

- Output### Add New Tools

- Status (Success/Error)1. Create a new tool in `tools/` directory

2. Import it in `agent_complete.py`

View summary in the sidebar or open the Excel file directly.3. Add to the `tools` list



## 🎯 Technology Stack## 📝 Notes



| Technology | Purpose |- The agent uses Groq's LLaMA model (configured in `.env`)

|------------|---------|- Memory is session-based using MemorySaver

| **LangChain** | LLM application framework |- Excel logs persist across sessions

| **LangGraph** | Agent orchestration & state management |- Cache files are stored indefinitely (manage manually if needed)

| **Ollama** | Local LLM (llama3.2:1b) |
| **Streamlit** | Web UI framework |
| **SQLite** | Embedded database |
| **Gmail API** | Email integration |
| **OpenPyXL** | Excel file operations |
| **DuckDuckGo** | Web search |
| **Markdownify** | HTML to Markdown conversion |

## 🔧 Configuration

### Change AI Model
Edit `agent_complete.py`:
```python
# Use different Ollama model
model = ChatOllama(model="llama3.1", temperature=0.6)

# Available models: llama3.2:1b, llama3.1, mistral, codellama
```

### Adjust Agent Behavior
Modify the system message in `agent_complete.py` to change how the agent uses tools.

### Add Custom Tools
1. Create new tool in `tools/` directory
2. Import in `agent_complete.py`
3. Add to `tools` list

## 🐛 Troubleshooting

### Ollama Connection Error
```bash
# Make sure Ollama is running
ollama serve

# Check if running
ps aux | grep ollama
```

### Model Not Found
```bash
# Pull the model
ollama pull llama3.2:1b

# List installed models
ollama list
```

### Database Not Found
```bash
# Recreate database
python setup_database.py
```

### Gmail Authentication Failed
```bash
# Delete token and re-authenticate
rm config/gmail_token.json

# Ensure credentials file exists
ls config/gmail_credentials.json
```

### Slow Performance
```bash
# Use smaller/faster model
ollama pull llama3.2:1b  # Fastest

# Or larger/better model
ollama pull llama3.1     # More capable but slower
```

## 📚 Documentation

- **Quick Guide** - [docs/QUICK_GUIDE.md](docs/QUICK_GUIDE.md)
- **Detailed Explanation** - [docs/PROJECT_EXPLANATION.md](docs/PROJECT_EXPLANATION.md)
- **Ollama Setup** - [docs/OLLAMA_SETUP.md](docs/OLLAMA_SETUP.md)
- **Optimization Summary** - [docs/OPTIMIZATION_SUMMARY.md](docs/OPTIMIZATION_SUMMARY.md)

## 🎓 Key Concepts

### Agent Architecture
The agent uses LangGraph to create a stateful AI that can:
- Decide which tools to use based on user queries
- Maintain conversation history
- Chain multiple tool calls together
- Synthesize results into coherent responses

### Tool Pattern
Each capability is a decorated function:
```python
@tool
def query_customer_info(name: str) -> str:
    """Search customer by name"""
    # Implementation
    return result
```

### Memory & State
```python
memory = MemorySaver()  # Persistent conversation memory
config = {"configurable": {"thread_id": "abc123"}}
```

## 🌟 Advantages

✅ **Cost Effective** - No API costs, run locally  
✅ **Privacy** - Data stays on your machine  
✅ **Unlimited Usage** - No rate limits  
✅ **Fast** - No network latency for AI  
✅ **Modular** - Easy to add/remove tools  
✅ **Observable** - Complete audit trail in Excel  
✅ **Production Ready** - Error handling & logging  

## 🔮 Future Enhancements

- [ ] File upload and analysis
- [ ] Export conversations to PDF
- [ ] Multi-user support with authentication
- [ ] API endpoints for programmatic access
- [ ] Analytics dashboard
- [ ] Custom report generation
- [ ] Integration with more services (Slack, Discord, etc.)

### Intent Detection & Tool Distinction
- [ ] Integrate NLP libraries (spaCy, NLTK, transformers) for intent classification
- [ ] Implement rule-based and context-aware parsing for tool selection
- [ ] Add context tracking and conversation history for better intent resolution
- [ ] Use confidence scoring and fallback to clarification when intent is ambiguous
- [ ] Leverage LLMs for intent extraction and tool routing
- [ ] Expand and refine training data for intent mapping

## 📄 License

MIT License - Feel free to use and modify for your needs.

## 🤝 Contributing

Contributions welcome! Feel free to:
- Add new tools
- Improve documentation
- Report bugs
- Suggest features

---

**Need Help?**
- Check [docs/PROJECT_EXPLANATION.md](docs/PROJECT_EXPLANATION.md) for detailed technical documentation
- See [docs/OLLAMA_SETUP.md](docs/OLLAMA_SETUP.md) for Ollama troubleshooting
- Review [docs/QUICK_GUIDE.md](docs/QUICK_GUIDE.md) for a quick reference

**Built with ❤️ using LangChain, LangGraph, and Ollama**
