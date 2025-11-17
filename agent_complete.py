"""
Complete Agent with all integrated tools:
- Web Search (DuckDuckGo)
- Web Scraping (visit_web)
- Database (SQLite customer data)
- Gmail (search, read, send)
- Excel Logging (automatic logging)
"""

from dotenv import load_dotenv
import google.generativeai as genai
import os
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq

from tools.visit_web import visit_web
from tools.db_tools import nl2sql_query, show_database_schema, list_tables, describe_table, get_table_row_count
from tools.excel_logger import log_interaction

# Try to import Gmail tools, but continue if they fail
gmail_tools_available = False
try:
    from tools.gmail_tools import search_gmail, read_gmail, send_gmail, get_my_email
    gmail_tools_available = True
    print("✓ Gmail tools loaded successfully")
except Exception as e:
    print(f"⚠ Gmail tools not available: {e}")
    print("Agent will work without Gmail features")

# Try to import RAG tools, but continue if they fail
rag_tools_available = False
try:
    from tools.rag_tools import search_documents, list_document_sources, get_document_stats
    # read_csv may be added dynamically below; import it if present
    try:
        from tools.rag_tools import read_csv
    except Exception:
        read_csv = None
    rag_tools_available = True
    print("✓ RAG tools loaded successfully")
except Exception as e:
    print(f"⚠ RAG tools not available: {e}")
    print("Agent will work without document search features")

load_dotenv()


# ===================== MODEL SELECTION =====================
# To switch between Groq API and Ollama local models:
# 1. Uncomment the block for the model you want to use.
# 2. Comment out the other block.
# ===========================================================

model = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    #model="llama-3.1-8b-instant",
    temperature=0.1,
    verbose=True,)

# model = ChatOllama(
#     model="qwen3:4b",  # Qwen3 4B model for reasoning
#     temperature=0.1,
#     num_ctx=4096,
#     verbose=True,)

search = DuckDuckGoSearchResults()

# All tools available to the agent
tools = [
    # Web tools
    search,
    visit_web,
    # Database tools
    nl2sql_query,
    show_database_schema,
    list_tables,
    describe_table,
    get_table_row_count,
]

# Add Gmail tools if available
if gmail_tools_available:
    tools.extend([search_gmail, read_gmail, send_gmail, get_my_email])

# Add RAG tools if available
if rag_tools_available:
    # Add RAG tools and optional read_csv if available
    rag_list = [search_documents, list_document_sources, get_document_stats]
    if 'read_csv' in globals() and read_csv is not None:
        rag_list.append(read_csv)
    tools.extend(rag_list)

memory = MemorySaver()
search = DuckDuckGoSearchResults()

# Add Gmail tools if available
if gmail_tools_available:
    tools.extend([search_gmail, read_gmail, send_gmail, get_my_email])

# Add RAG tools if available
if rag_tools_available:
    tools.extend([search_documents, list_document_sources, get_document_stats])

memory = MemorySaver()
agent = create_agent(model, tools, checkpointer=memory)

config = {"configurable": {"thread_id": "abc123"}}


def call_complete_agent(query: str):
    # --- System Prompt Construction ---
    prompt_blocks = []
    # Use the global `tools` list to determine available tool names here.
    # `filtered_tools` is computed later in this function, so referencing it
    # before assignment would raise an UnboundLocalError. Use `tools` as the
    # available toolset for prompt construction and intent-aware blocks.
    tool_names = [getattr(t, "__name__", "") for t in tools] if tools else []
    # Database block
    if "nl2sql_query" in tool_names:
        db_block = (
            "You are a database assistant. Use this schema: "
            "customers(id, name, email, phone, status, account_balance, join_date); "
            "orders(id, customer_id, order_number, product, amount, status, order_date). "
            "Join tables for related info, use LIKE for name searches. "
            "Return only the final answer/results, not the SQL query. "
            "Always format tabular data as markdown tables with headers and proper alignment. "
            "Format currency and dates clearly. "
            "Summarize and clarify output. "
            "Only generate graphs for sales, orders, trends, or time-series data (bar, line, pie, scatter, time-series) and always provide a brief summary. "
            "Never generate graphs for generic numbers or unrelated topics. "
            "Be concise, direct, and log errors if any. "
        )
        prompt_blocks.append(db_block)
    # Document block
    if any(tn in tool_names for tn in ["search_documents", "list_document_sources", "get_document_stats"]):
        prompt_blocks.append(
            "You are a document search assistant. Use document tools to answer. "
            "Return only relevant results. "
            "Use for queries about PDFs, Excel, Word, CSV, reports, or uploaded files. "
            "Summarize and clarify output. Log errors if any."
        )
    # Gmail block
    if any(tn in tool_names for tn in ["search_gmail", "read_gmail", "send_gmail", "get_my_email"]):
        prompt_blocks.append(
            "You are an email assistant. Use Gmail tools to answer. "
            "search_gmail: Gmail syntax (from:user@email.com, subject:invoice). "
            "read_gmail: Read full email. get_my_email: Get user's email (for 'send to myself'). "
            "send_gmail: Send email with recipient, subject, body. "
            "If 'send to myself' or 'my email', call get_my_email first. "
            "Never use placeholder emails. If unclear recipient, ask user. "
            "Always include subject and well-formatted body. "
            "Execute tool calls immediately. Log errors if any."
        )
    # Web block
    if any(tn in tool_names for tn in ["search", "visit_web"]):
        prompt_blocks.append(
            "You are a web assistant. Use web tools to answer. "
            "duckduckgo_results_json: Search web for current info. visit_web: Extract content from URLs. "
            "Return only relevant results. Summarize and clarify output. Log errors if any."
        )
    # Fallback block
    if not prompt_blocks:
        prompt_blocks.append(
            "You are an AI assistant. Use available tools to answer. "
            "Return only relevant results. Summarize and clarify output. Log errors if any."
        )
    # Merge blocks into one system prompt
    system_message = "\n".join(prompt_blocks)
    # Contextual intent detection: use previous queries/responses to inform current intent
    if not hasattr(call_complete_agent, "context_history"):
        call_complete_agent.context_history = []
    # Add previous query to context history
    if len(call_complete_agent.context_history) > 10:
        call_complete_agent.context_history.pop(0)
    # If this is a follow-up (e.g., starts with 'and', 'also', 'show me more', etc.), use last intent
    followup_phrases = ["and", "also", "show me more", "what about", "next", "continue"]
    is_followup = any(query.lower().startswith(phrase) for phrase in followup_phrases)
    last_intents = set()
    if is_followup and call_complete_agent.context_history:
        last_intents = call_complete_agent.context_history[-1].get("intents", set())

    # ...existing code for phrase/keyword/multi-intent detection...
    """
    Call agent with all tools and automatic Excel logging
    
    Args:
        query: User's input query
        
    Returns:
        Agent's response text
    """
    

    # --- Optimized Intent Detection ---
    import difflib
    def fuzzy_match(query, choices, threshold=0.8):
        matches = set()
        for choice in choices:
            ratio = difflib.SequenceMatcher(None, query, choice).ratio()
            if ratio >= threshold:
                matches.add(choice)
        return matches

    # Expanded keyword/phrase lists
    db_keywords = ["customer", "order", "database", "info", "details", "history", "client", "account", "user", "sql", "table", "row", "column"]
    db_phrases = ["show customer", "get customer", "customer details", "order history", "list customers", "find customer", "database query", "fetch from database"]
    doc_keywords = ["document", "pdf", "excel", "word", "csv", "file", "report", "spreadsheet", "upload", "scan", "extract", "address_details"]
    doc_phrases = ["search documents", "find document", "list documents", "document stats", "upload file", "scan file", "extract from file", "read csv", "address_details.csv"]
    email_keywords = ["email", "gmail", "send to myself", "my email", "mail", "inbox", "compose email", "read email", "send mail", "receive mail"]
    email_phrases = ["search email", "send email", "read email", "get my email", "email me", "compose email", "send gmail"]
    web_keywords = ["search", "find", "web", "news", "capital", "who", "what", "where", "when", "how", "lookup", "information", "facts", "internet", "online"]
    web_phrases = ["search the web", "find info", "lookup", "get information", "web search", "current news", "latest news", "search online"]

    # Detect raw SQL queries
    sql_keywords = ["select ", "insert ", "update ", "delete ", "join ", "where ", "from ", "group by", "order by"]
    is_sql_query = query.strip().lower().startswith(tuple([kw.strip() for kw in sql_keywords]))

    intents = set()
    q = query.lower()
    # Fuzzy phrase-level matching
    for phrase in db_phrases:
        if phrase in q or fuzzy_match(q, [phrase]):
            intents.add("db")
    for phrase in doc_phrases:
        if phrase in q or fuzzy_match(q, [phrase]):
            intents.add("doc")
    for phrase in email_phrases:
        if phrase in q or fuzzy_match(q, [phrase]):
            intents.add("email")
    for phrase in web_phrases:
        if phrase in q or fuzzy_match(q, [phrase]):
            intents.add("web")
    # Keyword-level matching
    if any(kw in q for kw in db_keywords):
        intents.add("db")
    if any(kw in q for kw in doc_keywords):
        intents.add("doc")
    if any(kw in q for kw in email_keywords):
        intents.add("email")
    if any(kw in q for kw in web_keywords) or not intents:
        intents.add("web")

    # Multi-intent: if query contains 'and', 'also', 'plus', split and match each part
    multi_splitters = [" and ", " also ", " plus ", ","]
    for splitter in multi_splitters:
        if splitter in q:
            parts = [p.strip() for p in q.split(splitter) if p.strip()]
            for part in parts:
                for phrase in db_phrases:
                    if phrase in part or fuzzy_match(part, [phrase]):
                        intents.add("db")
                for phrase in doc_phrases:
                    if phrase in part or fuzzy_match(part, [phrase]):
                        intents.add("doc")
                for phrase in email_phrases:
                    if phrase in part or fuzzy_match(part, [phrase]):
                        intents.add("email")
                for phrase in web_phrases:
                    if phrase in part or fuzzy_match(part, [phrase]):
                        intents.add("web")
                if any(kw in part for kw in db_keywords):
                    intents.add("db")
                if any(kw in part for kw in doc_keywords):
                    intents.add("doc")
                if any(kw in part for kw in email_keywords):
                    intents.add("email")
                if any(kw in part for kw in web_keywords):
                    intents.add("web")

    # Contextual intent: if follow-up, add last intents
    if last_intents:
        intents.update(last_intents)

    # Heuristic: prioritize document-related intent for explicit file/read queries (CSV, Excel, read/open file)
    file_indicators = [".csv", "csv", "read csv", "read file", "open file", "load csv", "upload file", "read excel", "xlsx", "xls", "address_details"]
    if any(ind in q for ind in file_indicators) and not is_sql_query:
        # If the query explicitly mentions a file or read/upload action, prefer document tools
        intents.discard("db")
        intents.add("doc")

    # Simple intent classifier fallback for ambiguous queries
    ambiguous = len(intents) == 0 or (len(q.split()) <= 3 and "web" not in intents)
    if ambiguous:
        intents = {"web"}

    # Save current intents to context history
    call_complete_agent.context_history.append({"query": query, "intents": intents})

    # --- Refactored Tool Selection Logic ---
    filtered_tools = []
    tool_name_map = {getattr(tool, "__name__", ""): tool for tool in tools}

    if is_sql_query:
        pass
    else:
        if "db" in intents and "nl2sql_query" in tool_name_map:
            filtered_tools.append(tool_name_map["nl2sql_query"])
        doc_tools = ["search_documents", "list_document_sources", "get_document_stats"]
        if "doc" in intents:
            for tname in doc_tools:
                if tname in tool_name_map:
                    filtered_tools.append(tool_name_map[tname])
        email_tools = ["search_gmail", "read_gmail", "send_gmail", "get_my_email"]
        if "email" in intents:
            for tname in email_tools:
                if tname in tool_name_map:
                    filtered_tools.append(tool_name_map[tname])
        web_tools = ["search", "visit_web"]
        if "web" in intents:
            for tname in web_tools:
                if tname in tool_name_map:
                    filtered_tools.append(tool_name_map[tname])
    if not filtered_tools:
        for tname in ["search", "visit_web"]:
            if tname in tool_name_map:
                filtered_tools.append(tool_name_map[tname])

    try:
        response = agent.invoke({
            "messages": [
                SystemMessage(content=system_message),
                HumanMessage(content=query)
            ]
        }, config=config, tools=filtered_tools)

        # Extract tools used and messages
        tools_used = []
        messages = response['messages']

        for message in messages:
            print(f"--- {message.type} ---")
            print(message.content, "\n")

            if hasattr(message, "tool_calls") and message.tool_calls:
                print(message.tool_calls, "\n")
                for tool_call in message.tool_calls:
                    tools_used.append(tool_call.get('name', 'unknown'))

        final_output = response["messages"][-1].content

        # Post-process: format tabular SQL results as markdown tables if detected
        def format_as_markdown_table(text):
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            # Detect simple table: lines with '|' and at least 2 lines
            if len(lines) >= 2 and all("|" in line for line in lines):
                # Add markdown table header separator if missing
                if not any("---" in line for line in lines):
                    header = lines[0]
                    num_cols = header.count("|")
                    sep = "|".join(["---"] * (num_cols + 1))
                    lines.insert(1, sep)
                return "\n".join(["```markdown", *lines, "```"])
            return text

        output_str = str(final_output).strip() if final_output is not None else ""
        # Only format if output looks like a table
        if output_str and "|" in output_str:
            output_str = format_as_markdown_table(output_str)

        # Suppress gibberish output
        import re
        def is_gibberish(text):
            # Empty or common no-result phrases
            if not text or text.lower() in ["no output", "none", "null", "no results found."]:
                return True
            # Excessive length with no structure
            if len(text) > 2000 and not ("|" in text or "error" in text.lower() or "summary" in text.lower() or "table" in text.lower()):
                return True
            # Excessive repetition of same character/word
            if len(set(text)) < 10 and len(text) > 100:
                return True
            if re.search(r'(.)\1{20,}', text):
                return True
            # Non-ASCII or control characters
            if re.search(r'[^\x20-\x7E\n\r\t]', text):
                return True
            # No sentence structure (no periods, no line breaks, no table, no keywords)
            if len(text) > 500 and not any(x in text for x in ["|", "error", "summary", "table", ".", "\n"]):
                return True
            # Looks like random tokens or hex
            if re.search(r'\b[a-f0-9]{16,}\b', text):
                return True
            return False

        # if is_gibberish(output_str):
        #     output_str = "No meaningful results returned. Please check your query or try again."
        #     status = "Error"
        # else:
        if not output_str or output_str.lower() in ["no output", "none", "null", "no results found."]:
            status = "Error"
        else:
            status = "Success"

        import threading
        def log_task():
            log_interaction(
                user_input=query,
                tools_used=tools_used,
                agent_messages=messages,
                output=output_str,
                status=status
            )
        threading.Thread(target=log_task, daemon=True).start()
        return output_str
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        log_interaction(
            user_input=query,
            tools_used=[],
            agent_messages=[],
            output=error_msg,
            status="Error"
        )
        return error_msg


if __name__ == "__main__":
    # Test the complete agent
    print("\n=== Testing Complete Agent ===\n")
    test_queries = [
        "List all customers",
        "Search for recent Python news",
    ]
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = call_complete_agent(query)
        print(f"Result: {result}\n")
        print("-" * 80)
