# AI Agent Project - Complete Technical Documentation

## **Project Overview**

This is a **LangChain-based AI agent system** that can interact with multiple data sources and services. It's a modular, scalable chatbot assistant built with **LangGraph** and **Ollama** (local LLM).

---

## **🎯 Core Concepts**

### **1. Agent Architecture (LangGraph)**
- **LangGraph** is used to create stateful AI agents that can use tools
- **create_agent()** - Creates an agent that can reason about which tools to use
- **MemorySaver** - Provides conversation memory across interactions
- **Checkpointer** - Maintains state with thread IDs for multi-turn conversations

### **2. Local LLM with Ollama**
- Uses **ChatOllama**
- Runs **llama3.2:1b** model locally - completely free, no API limits
- Temperature set to 0.6 for balanced creativity/consistency
- **Why Ollama?**
  - ✅ Free, No limits, Privacy, Offline support

### **3. Tool-based Architecture**
The agent can invoke specialized tools based on user queries. Each tool is a Python function decorated with `@tool`.

**How it works:**
1. User asks a question
2. LLM analyzes the question
3. LLM decides which tool(s) to use
4. Tools execute and return results
5. LLM synthesizes final answer

---

## **🛠️ Tools & Modules**

### **1. Web Research Tools**
📁 `tools/visit_web.py`

#### **DuckDuckGoSearchResults**
- Built-in LangChain tool for web search
- Returns search results in JSON format
- Provides URLs, snippets, and titles

#### **visit_web(url: str)**
Custom tool to scrape and extract content from URLs

**Features:**
- Converts HTML to clean markdown using `markdownify`
- Adds proper headers to avoid bot detection (User-Agent, Accept headers)
- Truncates content to 10,000 chars to avoid overwhelming the LLM
- Cleans up excessive newlines
- Error handling for timeouts and connection issues

**Example Usage:**
```python
result = visit_web("https://example.com")
# Returns markdown content of the page
```

---

### **2. Database Tools**
📁 `tools/query_database.py`

#### **SQLite Database** (`customers.db`)

**Schema:**

**Customers Table:**
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `name` TEXT NOT NULL
- `email` TEXT NOT NULL
- `phone` TEXT
- `status` TEXT (Active/Inactive)
- `account_balance` REAL
- `join_date` TEXT

**Orders Table:**
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `customer_id` INTEGER (FOREIGN KEY → customers.id)
- `order_number` TEXT
- `product` TEXT
- `amount` REAL
- `status` TEXT (Delivered/Shipped/Processing)
- `order_date` TEXT

#### **Three Query Tools:**

**1. query_customer_info(customer_name: str)**
```python
# Search customer by name (partial match supported)
query_customer_info("John")
# Returns: Customer ID, name, email, phone, status, balance, join date
```

**2. query_customer_orders(customer_name: str)**
```python
# Get order history for a customer
query_customer_orders("Jane Smith")
# Returns: All orders with order number, product, amount, status, date
```

**3. list_all_customers()**
```python
# List all customers with their status
list_all_customers()
# Returns: All customer names, emails, status, account balance
```

**Database Features:**
- SQL parameterization (prevents SQL injection)
- Partial name matching with LIKE operator
- Relational queries with JOINs
- Error handling for all queries

---

### **3. Gmail Integration**
📁 `tools/gmail_tools.py`

Uses **Google Gmail API** with OAuth2 authentication

#### **Authentication Flow:**

**get_gmail_service()**
- Handles OAuth2 flow
- Saves credentials to `gmail_token.json`
- Auto-refreshes expired tokens
- First-time: Opens browser for authentication
- Subsequent: Uses saved token

**OAuth2 Scopes:**
- `gmail.readonly` - Read emails
- `gmail.send` - Send emails

#### **Three Gmail Tools:**

**1. search_gmail(query: str, max_results: int = 10)**
Search emails with Gmail search syntax

**Examples:**
```python
search_gmail("from:john@example.com")        # Emails from specific sender
search_gmail("subject:invoice")              # Emails with subject
search_gmail("is:unread after:2024/01/01")  # Unread emails after date
search_gmail("has:attachment")               # Emails with attachments
```

**Returns:** From, Subject, Date, Snippet for each email

**2. read_gmail(email_id: str)**
```python
# Read full email content
read_gmail("18c3f4a5b2e6d1f8")
# Returns: Full email with headers and body
```

**3. send_gmail(to: str, subject: str, body: str)**
```python
# Send an email
send_gmail("user@example.com", "Meeting", "Let's meet tomorrow")
# Returns: Confirmation with message ID
```

**Email Format:**
- Uses `email.mime.text.MIMEText` for message creation
- Base64 encoding for Gmail API
- Proper header formatting

---

### **4. Excel Logging**
📁 `tools/excel_logger.py`

Automatic logging of all agent interactions

#### **initialize_excel_log()**
Creates `agent_logs.xlsx` with:
- Styled headers (blue background, white text)
- Proper column widths
- Column headers: Timestamp, User Input, Tools Used, Sources/URLs, Output, Status

#### **log_interaction()**
Logs every interaction with:
- **Timestamp** - YYYY-MM-DD HH:MM:SS format
- **User Input** - Truncated to 500 chars
- **Tools Used** - Comma-separated list
- **Sources/URLs** - Extracted from agent messages (regex pattern)
- **Output** - Truncated to 1000 chars
- **Status** - Color-coded (Green for Success, Red for Error)

**Features:**
- URL extraction using regex: `r'https?://[^\s<>"{}|\\^`\[\]]+'`
- Text wrapping for readability
- Automatic deduplication of URLs
- Limits to first 5 URLs per interaction
- Color-coded status cells with fills and fonts

#### **get_log_summary()**
Provides statistics:
```python
get_log_summary()
# Returns:
# - Total Queries: 42
# - Successful: 38
# - Errors: 4
# - Log File: /path/to/agent_logs.xlsx
```

---

## **📦 Key Dependencies**

From `requirements.txt`:

| Library | Version | Purpose |
|---------|---------|---------|
| `dotenv` | - | Load environment variables |
| `streamlit` | - | Web UI framework |
| `langgraph` | - | Graph-based agent orchestration |
| `langchain` | - | Core framework for LLM applications |
| `langchain-community` | - | Community tools (DuckDuckGo) |
| `langchain-ollama` | - | Ollama LLM integration |
| `duckduckgo-search` | - | Web search functionality |
| `markdownify` | - | HTML to Markdown conversion |
| `requests` | - | HTTP requests for web scraping |
| `openpyxl` | - | Excel file operations |
| `pandas` | - | Data manipulation |
| `google-auth-oauthlib` | - | Google OAuth2 authentication |
| `google-auth-httplib2` | - | HTTP transport for Google Auth |
| `google-api-python-client` | - | Gmail API client |

---

## **🤖 Agent Variants**

### **1. agent.py** (Basic)
**Purpose:** Original version for testing

**Configuration:**
```python
model = ChatGroq(model="llama-3.3-70b-versatile")
tools = [search]
```

**Features:**
- Uses cloud API (ChatGroq)
- Only DuckDuckGo search tool
- Minimal functionality
- Basic conversation

---

### **2. agent2.py** (Web Agent)
**Purpose:** Web research and scraping

**Configuration:**
```python
model = ChatOllama(model="llama3.2:1b")
tools = [search, visit_web]
```

**Features:**
- Local LLM (Ollama)
- Web search + web scraping
- Good for research queries
- No database or Gmail

**System Message:**
```
"You are a helpful research assistant. When answering questions:
1. First use duckduckgo_results_json to search and find relevant URLs
2. Then use visit_web to visit the most relevant URL
3. Provide a comprehensive answer based on the content"
```

**Use Cases:**
- "What's the latest news about Python?"
- "Find information about LangChain"
- "Search for machine learning tutorials"

---

### **3. agent3.py** (Full Agent)
**Purpose:** Customer service + research

**Configuration:**
```python
model = ChatOllama(model="llama3.2:1b")
tools = [search, visit_web, query_customer_info, 
         query_customer_orders, list_all_customers]
```

**Features:**
- Web tools + database tools
- Customer service capabilities
- Research capabilities
- No Gmail or logging

**System Message:**
```
"You are a helpful research and customer service assistant.
Database Tools - For customer information
Web Search Tools - For current information"
```

**Use Cases:**
- "List all customers"
- "Show me John Doe's orders"
- "What's Alice Brown's account balance?"
- "Search for Python tutorials"

---

### **4. agent_complete.py** (Complete Agent) ⭐
**Purpose:** Production-ready full-featured agent

**Configuration:**
```python
model = ChatOllama(model="llama3.2:1b")
tools = [search, visit_web, query_customer_info, 
         query_customer_orders, list_all_customers,
         search_gmail, read_gmail, send_gmail]
```

**Features:**
- ✅ All tools enabled
- ✅ Automatic Excel logging
- ✅ Graceful degradation if Gmail unavailable
- ✅ Production-ready with error handling
- ✅ Comprehensive system message

**Unique Features:**
1. **Conditional Gmail loading:**
```python
try:
    from tools.gmail_tools import search_gmail, read_gmail, send_gmail
    gmail_tools_available = True
except:
    print("Agent will work without Gmail features")
```

2. **Automatic logging:**
```python
log_interaction(
    user_input=query,
    tools_used=tools_used,
    agent_messages=messages,
    output=final_output,
    status="Success"
)
```

3. **Error handling:**
```python
try:
    response = agent.invoke(...)
    return final_output
except Exception as e:
    log_interaction(..., status="Error")
    return error_msg
```

**Use Cases:**
- Everything from all other agents
- Email management
- Full conversation logging
- Production deployments

---

## **🖥️ User Interface (app.py)**

Built with **Streamlit** for web-based chat interface

### **Main Components:**

#### **1. Title and Header**
```python
st.title("🤖 AI Assistant Agent")
```

#### **2. Sidebar Configuration**
```python
with st.sidebar:
    agent_type = st.radio("Select Agent Type:", [
        "Complete Agent (All Tools)",
        "Full Agent (Web + Database)",
        "Web Agent Only"
    ])
```

**Capabilities Display:**
- Shows available tools for selected agent
- Log summary button
- Visual feedback

#### **3. Chat Interface**
```python
# Session state for message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if query := st.chat_input("Ask me anything!"):
    # Process and display
```

#### **4. Agent Selection Logic**
```python
if agent_type == "Complete Agent (All Tools)":
    response = call_complete_agent(query)
elif agent_type == "Full Agent (Web + Database)":
    response = call_full_agent(query)
else:
    response = call_web_agent(query)
```

### **Streamlit Features Used:**
- `st.chat_message()` - Chat UI components
- `st.chat_input()` - Input field
- `st.spinner()` - Loading indicator
- `st.session_state` - Persistent state
- `st.sidebar` - Side panel
- `st.radio()` - Radio buttons
- `st.button()` - Action buttons
- `st.info()` - Info messages

---

## **💾 Data Persistence**

### **1. SQLite Database** (`customers.db`)

**Creation:**
```python
# setup_database.py creates the database
python setup_database.py
```

**Sample Data:**
- 5 customers (John Doe, Jane Smith, Bob Johnson, Alice Brown, Charlie Wilson)
- 6 orders across different customers
- Realistic status values (Active/Inactive, Delivered/Shipped/Processing)

**Location:** Project root directory

---

### **2. Filesystem Cache** (Planned)
- `cache/` directory for markdown files
- Mentioned in README but not yet implemented
- Would store agent responses for reuse

---

### **3. Excel Logs** (`agent_logs.xlsx`)

**Features:**
- Auto-created with styled headers
- Persistent across sessions
- Formatted with colors and alignment
- Growing file (all logs appended)

**Column Layout:**
| A (20) | B (40) | C (25) | D (50) | E (60) | F (12) |
|--------|--------|--------|--------|--------|--------|
| Timestamp | User Input | Tools Used | Sources/URLs | Output | Status |

**Colors:**
- Headers: Blue background (#4472C4), white text
- Success: Light green background (#C6EFCE), dark green text (#006100)
- Error: Light red background (#FFC7CE), dark red text (#9C0006)

---

### **4. Gmail Tokens**

**gmail_credentials.json** (User provides)
- OAuth2 client secrets from Google Cloud Console
- Contains client_id, client_secret, redirect_uris
- Must be created manually by user

**gmail_token.json** (Auto-generated)
- Access tokens and refresh tokens
- Generated after first OAuth flow
- Auto-refreshed when expired
- Stored in project root

---

## **🔄 Agent Execution Flow**

### **Step-by-Step Process:**

```
1. User Input
   ↓
2. Streamlit captures input
   ↓
3. Message wrapped in HumanMessage + SystemMessage
   ↓
4. Agent receives message bundle
   ↓
5. LLM analyzes query
   ↓
6. LLM decides which tool(s) to invoke
   ↓
7. Tools execute (database query, web search, etc.)
   ↓
8. Tool results returned to agent
   ↓
9. LLM synthesizes final answer
   ↓
10. Response sent back to Streamlit
   ↓
11. Excel logging happens (complete agent only)
   ↓
12. Response displayed in chat UI
   ↓
13. Message added to session history
```

### **Message Flow Example:**

**User:** "Show me John Doe's orders"

**1. System Message:**
```python
SystemMessage(content="You are a helpful assistant with database tools...")
```

**2. Human Message:**
```python
HumanMessage(content="Show me John Doe's orders")
```

**3. AI Message (Tool Call):**
```python
AIMessage(
    content="",
    tool_calls=[{
        "name": "query_customer_orders",
        "args": {"customer_name": "John Doe"}
    }]
)
```

**4. Tool Message:**
```python
ToolMessage(
    content="Orders for John Doe:\n\nOrder: ORD-001\nProduct: Laptop..."
)
```

**5. AI Message (Final):**
```python
AIMessage(content="John Doe has 2 orders: A laptop for $1200 and a mouse for $25")
```

---

## **🎯 Design Patterns Used**

### **1. Tool Pattern**
**Implementation:**
```python
@tool
def query_customer_info(customer_name: str) -> str:
    """Docstring explains tool purpose"""
    # Tool implementation
    return result
```

**Benefits:**
- LangChain automatically handles tool calling
- Type hints provide structure
- Docstrings guide LLM on when to use tool

---

### **2. Configuration Object Pattern**
```python
config = {"configurable": {"thread_id": "abc123"}}
agent.invoke({"messages": [...]}, config=config)
```

**Purpose:**
- Enables conversation memory
- Thread ID tracks conversation context
- Different threads = different conversations

---

### **3. System Message Pattern**
```python
SystemMessage(content="""You are a helpful assistant. 
When answering:
1. Use database tools for customer queries
2. Use web tools for research
3. Always cite sources""")
```

**Purpose:**
- Guides agent behavior
- Provides instructions
- Sets expectations

---

### **4. Graceful Degradation Pattern**
```python
gmail_tools_available = False
try:
    from tools.gmail_tools import search_gmail, read_gmail, send_gmail
    gmail_tools_available = True
    print("✓ Gmail tools loaded successfully")
except Exception as e:
    print(f"⚠ Gmail tools not available: {e}")
    print("Agent will work without Gmail features")

if gmail_tools_available:
    tools.extend([search_gmail, read_gmail, send_gmail])
```

**Benefits:**
- Agent works even if some features fail
- Better user experience
- No crashes due to missing dependencies

---

### **5. Factory Pattern**
```python
# app.py selects agent based on configuration
if agent_type == "Complete Agent":
    response = call_complete_agent(query)
elif agent_type == "Full Agent":
    response = call_full_agent(query)
else:
    response = call_web_agent(query)
```

**Benefits:**
- Single interface, multiple implementations
- Easy to add new agent types
- Separation of concerns

---

### **6. Decorator Pattern**
```python
@tool
def my_custom_tool(param: str) -> str:
    """Tool description"""
    return result
```

**Purpose:**
- Adds LangChain tool functionality
- Preserves original function
- Provides metadata

---

## **🔐 Security & Authentication**

### **Gmail OAuth2 Flow:**

**Step 1: Setup (One-time)**
```
1. Go to Google Cloud Console
2. Create project
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop app)
5. Download credentials JSON
6. Save as gmail_credentials.json
```

**Step 2: First Authentication**
```
1. Agent tries to access Gmail
2. Opens browser window
3. User logs in with Google account
4. User grants permissions
5. Token saved to gmail_token.json
```

**Step 3: Subsequent Uses**
```
1. Agent loads token from gmail_token.json
2. If expired, auto-refresh using refresh_token
3. If refresh fails, re-authenticate
```

**Security Features:**
- OAuth2 (industry standard)
- Token-based authentication
- No password storage
- Scoped permissions (only Gmail access)
- Automatic token refresh

---

### **SQL Injection Prevention**
```python
# ✅ SAFE - Parameterized query
cursor.execute(
    "SELECT * FROM customers WHERE name LIKE ?", 
    (f"%{customer_name}%",)
)

# ❌ UNSAFE - String concatenation (DON'T DO THIS)
cursor.execute(f"SELECT * FROM customers WHERE name LIKE '%{customer_name}%'")
```

---

## **📊 Key Technical Concepts**

### **1. Markdown Conversion**
**Why Markdown?**
- Cleaner than raw HTML for LLMs
- Preserves structure without complex tags
- Better token efficiency
- Easier to parse and understand

**Implementation:**
```python
from markdownify import markdownify
markdown_content = markdownify(response.text).strip()
```

---

### **2. Content Truncation**
**Why Truncate?**
- LLMs have token limits (context window)
- Too much content = poor performance
- Cost optimization (for cloud APIs)

**Implementation:**
```python
if len(markdown_content) > 10000:
    markdown_content = markdown_content[:10000] + "\n\n[Content truncated...]"
```

---

### **3. Stateful Conversations**
**How it works:**
```python
memory = MemorySaver()
agent = create_agent(model, tools, checkpointer=memory)
config = {"configurable": {"thread_id": "abc123"}}
```

**Benefits:**
- Remembers previous interactions
- Can reference earlier messages
- Maintains context across turns
- Different threads = isolated conversations

---

### **4. Token Efficiency**
**Strategies used:**
- Truncate long content
- Convert HTML to markdown
- Clean excessive newlines
- Limit search results
- Summarize database results

---

### **5. Error Handling**
**Patterns used:**

**Try-Except Blocks:**
```python
try:
    result = risky_operation()
    log_interaction(..., status="Success")
except Exception as e:
    log_interaction(..., status="Error")
    return f"Error: {str(e)}"
```

**Timeout Handling:**
```python
response = requests.get(url, timeout=30, headers=headers)
```

**Graceful Degradation:**
```python
if not os.path.exists(CREDENTIALS_PATH):
    return None, "Gmail credentials not found"
```

---

## **💡 Usage Patterns & Examples**

### **Customer Service Queries:**

```python
# Query 1: Basic customer lookup
"Show me John Doe's information"
# → Uses: query_customer_info("John Doe")

# Query 2: Order history
"What orders does Jane Smith have?"
# → Uses: query_customer_orders("Jane Smith")

# Query 3: List all
"List all active customers"
# → Uses: list_all_customers()

# Query 4: Account balance
"What's Alice Brown's account balance?"
# → Uses: query_customer_info("Alice Brown")
```

---

### **Web Research Queries:**

```python
# Query 1: News search
"What's the latest news on AI?"
# → Uses: duckduckgo_results_json(), then visit_web()

# Query 2: Tutorial search
"Find Python tutorials"
# → Uses: duckduckgo_results_json()

# Query 3: Documentation
"Search for LangChain documentation"
# → Uses: duckduckgo_results_json(), visit_web()
```

---

### **Email Tasks:**

```python
# Query 1: Search by sender
"Search for emails from john@example.com"
# → Uses: search_gmail("from:john@example.com")

# Query 2: Unread emails
"Find unread emails today"
# → Uses: search_gmail("is:unread after:2025/11/10")

# Query 3: Read email
"Read email with ID 18c3f4a5b2e6d1f8"
# → Uses: read_gmail("18c3f4a5b2e6d1f8")

# Query 4: Send email
"Send email to boss@company.com about meeting tomorrow"
# → Uses: send_gmail("boss@company.com", "Meeting", "...")
```

---

### **Mixed/Complex Queries:**

```python
# Query 1: Database + Email
"Look up customer John Doe and email me his order history"
# → Uses: query_customer_orders("John Doe"), then send_gmail()

# Query 2: Web + Database
"Search for best CRM practices and show me our top customers"
# → Uses: duckduckgo_results_json(), visit_web(), list_all_customers()

# Query 3: Multi-tool chain
"Find Alice Brown's orders and search for product reviews online"
# → Uses: query_customer_orders(), duckduckgo_results_json(), visit_web()
```

---

## **🚀 System Requirements**

### **Required:**
1. **Python 3.8+** - Core language
2. **Ollama** - For local LLM
3. **SQLite** - Built into Python (no separate install)
4. **pip** - Package manager

### **Optional:**
5. **Gmail OAuth credentials** - For email features
6. **Excel viewer** - To view logs (Excel, LibreOffice, etc.)

### **Installation Steps:**

```bash
# 1. Install Ollama
brew install ollama  # macOS
# or visit https://ollama.ai

# 2. Start Ollama service
ollama serve

# 3. Pull model (in new terminal)
ollama pull llama3.2:1b

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Set up database
python setup_database.py

# 6. (Optional) Set up Gmail
# - Create credentials in Google Cloud Console
# - Save as gmail_credentials.json

# 7. Run application
streamlit run app.py
```

---

## **🎨 Strengths of This Architecture**

### **1. Modularity** ⭐
- Each tool is independent
- Easy to add/remove tools
- Clear separation of concerns
- Tools can be tested in isolation

### **2. Cost-Effectiveness** 💰
- Local LLM = $0 API costs
- No per-query charges
- Unlimited usage
- No rate limits

### **3. Extensibility** 🔧
- Simple to add new agents
- Easy to create new tools
- Flexible system messages
- Pluggable architecture

### **4. Observability** 👁️
- Excel logging for debugging
- Tool call tracking
- URL extraction
- Status monitoring
- Complete audit trail

### **5. User-Friendly** 😊
- Streamlit UI is intuitive
- Chat interface familiar
- Visual feedback
- Agent selection dropdown
- Log summary in sidebar

### **6. Privacy** 🔒
- LLM runs locally
- Data stays on machine
- No cloud AI provider access
- Only web searches go online

### **7. Robustness** 💪
- Error handling throughout
- Graceful degradation
- Timeout management
- Fallback behaviors
- Informative error messages

### **8. Performance** ⚡
- Local LLM = fast responses
- No network latency for inference
- Efficient tool execution
- Minimal dependencies

---

## **🔮 Potential Enhancements**

### **Future Improvements:**

1. **Filesystem Cache Implementation**
   - Save/retrieve markdown responses
   - Cache web content
   - Speed up repeated queries

2. **More Database Operations**
   - Add/update/delete customers
   - Create new orders
   - Generate reports

3. **Advanced Gmail Features**
   - Send emails with attachments
   - Reply to emails
   - Mark as read/unread
   - Delete emails

4. **Authentication System**
   - User login
   - Role-based access
   - API keys for external access

5. **Streaming Responses**
   - Real-time token generation
   - Better UX for long responses
   - Progress indicators

6. **Multi-modal Support**
   - Image analysis
   - PDF processing
   - Document extraction

7. **Analytics Dashboard**
   - Query statistics
   - Tool usage metrics
   - Performance monitoring
   - User behavior analysis

8. **Export Features**
   - Export conversations to PDF
   - Download logs in different formats
   - Backup/restore functionality

9. **Better Memory Management**
   - Conversation summarization
   - Long-term memory
   - Knowledge base integration

10. **API Endpoint**
    - REST API for programmatic access
    - Webhook support
    - Integration with other systems

---

## **📚 Learning Resources**

### **Key Technologies:**

**LangChain:**
- Documentation: https://python.langchain.com/
- Learn: Agent concepts, tools, chains

**LangGraph:**
- Documentation: https://langchain-ai.github.io/langgraph/
- Learn: Graph-based agent orchestration

**Ollama:**
- Website: https://ollama.ai
- Learn: Local LLM deployment

**Streamlit:**
- Documentation: https://docs.streamlit.io
- Learn: Web app creation for ML/AI

**Gmail API:**
- Documentation: https://developers.google.com/gmail/api
- Learn: Email automation

---

## **🐛 Troubleshooting**

### **Common Issues:**

**1. Ollama Connection Refused**
```bash
# Solution: Make sure Ollama is running
ollama serve

# Check if running:
ps aux | grep ollama
```

**2. Model Not Found**
```bash
# Solution: Pull the model
ollama pull llama3.2:1b

# List installed models:
ollama list
```

**3. Gmail Authentication Fails**
```bash
# Solution:
# 1. Delete gmail_token.json
# 2. Re-authenticate
# 3. Make sure gmail_credentials.json exists
```

**4. Database Not Found**
```bash
# Solution: Create database
python setup_database.py
```

**5. Excel Permission Denied**
```bash
# Solution: Close Excel file if open
# Or check write permissions
chmod 644 agent_logs.xlsx
```

**6. Import Errors**
```bash
# Solution: Install all dependencies
pip install -r requirements.txt
```

**7. Slow Performance**
```bash
# Solution: Use smaller model
# In agent files, change:
model = ChatOllama(model="llama3.2:1b")  # Fastest
# instead of:
model = ChatOllama(model="llama3.1")     # Slower but better
```

---

## **📝 Code Examples**

### **Adding a Custom Tool:**

```python
# 1. Create new file: tools/weather_tool.py
from langchain_core.tools import tool
import requests

@tool
def get_weather(city: str) -> str:
    """
    Get current weather for a city.
    
    Args:
        city: Name of the city
    
    Returns:
        Weather information
    """
    try:
        # Your weather API call here
        return f"Weather in {city}: Sunny, 72°F"
    except Exception as e:
        return f"Error: {str(e)}"

# 2. Import in agent_complete.py
from tools.weather_tool import get_weather

# 3. Add to tools list
tools = [
    search, visit_web, 
    query_customer_info, query_customer_orders, list_all_customers,
    get_weather  # Add here
]

# 4. Update system message
system_message += "\n**Weather Tool:**\n- get_weather: Get current weather for a city"
```

---

### **Creating a New Agent:**

```python
# agent_custom.py
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from tools.visit_web import visit_web
# Import your custom tools

model = ChatOllama(model="llama3.2:1b", temperature=0.6)
tools = [visit_web]  # Add your tools
memory = MemorySaver()

agent = create_agent(model, tools, checkpointer=memory)
config = {"configurable": {"thread_id": "custom123"}}

def call_custom_agent(query: str):
    response = agent.invoke({
        "messages": [
            SystemMessage(content="Your custom system message"),
            HumanMessage(content=query)
        ]
    }, config=config)
    
    return response["messages"][-1].content

# Add to app.py agent selection
```

---

## **🎓 Architecture Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI (app.py)                   │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Web Agent   │  │  Full Agent  │  │Complete Agent│      │
│  │  (agent2.py) │  │  (agent3.py) │  │(agent_complete)│    │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Agent Engine                     │
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │ChatOllama    │◄───────►│MemorySaver   │                  │
│  │(llama3.2:1b) │         │(Checkpointer)│                  │
│  └──────────────┘         └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                          Tool Layer                           │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Web Tools   │  │Database Tools│  │ Gmail Tools  │      │
│  │              │  │              │  │              │      │
│  │• DuckDuckGo  │  │• Query       │  │• Search      │      │
│  │• visit_web   │  │  Customer    │  │• Read        │      │
│  │              │  │• Query       │  │• Send        │      │
│  │              │  │  Orders      │  │              │      │
│  │              │  │• List All    │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                               │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Internet    │  │customers.db  │  │ Gmail API    │      │
│  │  (Web)       │  │(SQLite)      │  │(Google)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Logging Layer                             │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            agent_logs.xlsx (Excel Logger)             │   │
│  │  • Timestamp  • Tools Used  • Output  • Status       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## **🎯 Summary**

This project demonstrates a **production-ready AI agent framework** with:

✅ **Local LLM** - Cost-effective, private, fast
✅ **Multi-tool support** - Web, database, email
✅ **Modular architecture** - Easy to extend
✅ **Conversation memory** - Stateful interactions
✅ **Automatic logging** - Complete audit trail
✅ **Web UI** - User-friendly interface
✅ **Error handling** - Robust and reliable
✅ **Graceful degradation** - Works even with missing features