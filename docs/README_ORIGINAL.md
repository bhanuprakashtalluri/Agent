# AI Agent with Complete Tool Integration

## 🎯 Features

This AI agent includes:

1. **Web Search & Scraping** - DuckDuckGo search + web content extraction
2. **Customer Database** - SQLite database with customer and order data
3. **Gmail Integration** - Search, read, and send emails
4. **Filesystem Cache** - Save and retrieve markdown responses
5. **Excel Logging** - Automatic logging of all interactions

## 📦 Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Gmail API (Optional but recommended)

To use Gmail features, you need to set up OAuth2 credentials:

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

#### Step 2: Create OAuth2 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure consent screen if prompted:
   - User Type: External
   - App name: "AI Agent"
   - Add your email as test user
4. Application type: "Desktop app"
5. Download the credentials JSON file
6. Save it as `gmail_credentials.json` in the project root

#### Step 3: First-time Authentication
When you first use Gmail features, the agent will:
1. Open a browser window for authentication
2. Ask you to login with your Google account
3. Save the token to `gmail_token.json` for future use

**Note:** If you skip Gmail setup, the agent will work fine without email features.

## 🚀 Usage

### Run the Streamlit App

```bash
streamlit run app.py
```

### Choose Your Agent Type

The app offers three agent configurations:

1. **Complete Agent (All Tools)** - Recommended
   - All features enabled
   - Automatic Excel logging
   - Filesystem caching
   - Gmail integration

2. **Full Agent (Web + Database)**
   - Web search and scraping
   - Customer database access
   - No logging or Gmail

3. **Web Agent Only**
   - Just web search and scraping
   - Minimal features

## 📂 Project Structure

```
agent/
├── app.py                      # Streamlit UI
├── agent2.py                   # Web-only agent
├── agent3.py                   # Web + Database agent
├── agent_complete.py           # Complete agent with all tools
├── requirements.txt            # Python dependencies
├── customers.db                # SQLite database
├── agent_logs.xlsx            # Excel log (auto-created)
├── gmail_credentials.json      # Gmail OAuth (you create this)
├── gmail_token.json           # Gmail token (auto-created)
├── cache/                     # Cached markdown files (auto-created)
│   └── *.md
└── tools/
    ├── visit_web.py           # Web scraping tool
    ├── query_database.py      # Database query tools
    ├── filesystem_cache.py    # Cache management
    ├── gmail_tools.py         # Gmail integration
    └── excel_logger.py        # Excel logging utility
```

## 💡 Example Queries

### Customer Database
- "List all customers"
- "Show me John Doe's information"
- "What orders does Jane Smith have?"
- "What's Alice Brown's account balance?"

### Web Search
- "What's the latest news about Python?"
- "Search for machine learning tutorials"
- "Find information about LangChain"

### Gmail (if configured)
- "Search for emails from john@example.com"
- "Find unread emails from today"
- "Search for emails with subject containing 'invoice'"

### File Management
- "Save this response to cache"
- "List all cached files"
- "Read the cached file from yesterday"

### Mixed Queries
- "Search for Python tutorials and save the results to cache"
- "Check if John Doe has any orders and email me the details"

## 📊 Excel Logging

All interactions are automatically logged to `agent_logs.xlsx` with:
- Timestamp
- User input
- Tools used
- Sources/URLs visited
- Output
- Status (Success/Error)

View the log summary in the sidebar of the Streamlit app.

## 🗄️ Database Schema

### Customers Table
- id (PRIMARY KEY)
- name
- email
- phone
- status
- account_balance
- join_date

### Orders Table
- id (PRIMARY KEY)
- customer_id (FOREIGN KEY)
- order_number
- product
- amount
- status
- order_date

## 🔧 Troubleshooting

### Gmail Not Working
- Make sure `gmail_credentials.json` exists
- Check that Gmail API is enabled in Google Cloud Console
- Delete `gmail_token.json` and re-authenticate if issues persist

### Excel Logging Errors
- Ensure `openpyxl` is installed: `pip install openpyxl`
- Check write permissions in the project directory

### Cache Directory Issues
- The `cache/` directory is auto-created
- Check write permissions

## 🎨 Customization

### Add More Customers
Edit `setup_database.py` and run:
```bash
python3 setup_database.py
```

### Modify Agent Behavior
Edit the system message in `agent_complete.py` to change how the agent uses tools.

### Add New Tools
1. Create a new tool in `tools/` directory
2. Import it in `agent_complete.py`
3. Add to the `tools` list

## 📝 Notes

- The agent uses Groq's LLaMA model (configured in `.env`)
- Memory is session-based using MemorySaver
- Excel logs persist across sessions
- Cache files are stored indefinitely (manage manually if needed)
