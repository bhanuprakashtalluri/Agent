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

from tools.visit_web import visit_web
from tools.query_database import nl2sql_query, show_database_schema, list_tables, describe_table, run_custom_sql, get_table_row_count
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
    rag_tools_available = True
    print("✓ RAG tools loaded successfully")
except Exception as e:
    print(f"⚠ RAG tools not available: {e}")
    print("Agent will work without document search features")



load_dotenv()



model = ChatOllama(
    model="qwen3:4b",  # Qwen3 4B model for reasoning
    temperature=0.1,
    num_ctx=4096,
    verbose=True,
)

search = DuckDuckGoSearchResults()

# All tools available to the agent
tools = [
    # Web tools
    search, 
    visit_web,
    
    # Database tool (NL2SQL)
    nl2sql_query,
]

# Add Gmail tools if available
if gmail_tools_available:
    tools.extend([search_gmail, read_gmail, send_gmail, get_my_email])

# Add RAG tools if available
if rag_tools_available:
    tools.extend([search_documents, list_document_sources, get_document_stats])

memory = MemorySaver()
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
    run_custom_sql,
    get_table_row_count,
]

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
    
    # Build system message based on available tools
    system_message = """
    You are an advanced AI agent. When answering, follow these steps:
    1. Break down the user query into clear, simple steps.
    2. For each step, explain what you are doing and why.
    3. Use available tools directly and show which tool is used for each step.
    4. Provide detailed, stepwise reasoning for your answer.
    5. Summarize the final result clearly and concisely.
    6. If you encounter an error, log the error and explain the cause.
    7. Always log your prompt and reasoning steps for debugging.
    Be direct, detailed, and transparent in your process.
    By default, return only the final answer, data, and any relevant visualizations. Do not include reasoning, steps, or explanations unless the user explicitly requests them (e.g., "show steps", "explain reasoning").

    **Web & Research Tools:**
    - duckduckgo_results_json: Search the web for current information
    - visit_web: Visit and extract content from URLs

    **Customer Database Tool:**
    - nl2sql_query: Use natural language to query the customer and order database. For queries about sales, orders, or transactions, always join the relevant tables (e.g., show customer names instead of IDs). If IDs are shown, provide a legend mapping IDs to names. Format results in clear, readable tables with column headers and currency/date formatting where appropriate. Always summarize and clarify the output for the user.

    **Visualizations:**
    - For outputs related to orders, sales, trends, comparisons, or time-series data, generate and display relevant graphs or visualizations (such as bar charts, line charts, pie charts, scatter plots, or time-series plots) to help users understand patterns and distributions. Do not generate visuals for generic numerical data unless it relates to these topics. Always accompany visuals with a brief summary or explanation.
    """

    if gmail_tools_available:
        system_message += """
**Gmail Tools:**
- search_gmail: Search emails using Gmail syntax (e.g., "from:user@email.com", "subject:invoice")
- read_gmail: Read full content of a specific email
- get_my_email: Get the user's own email address (only use if user says 'send to myself' or 'my email')
- send_gmail: Send emails with recipient, subject, and message body

**CRITICAL RULES for sending emails:**
- When user says "send to myself" or "my email", AUTOMATICALLY call get_my_email first (don't ask permission)
- NEVER use placeholder emails like 'your_email@example.com', 'user@example.com', etc.
- If recipient email is unclear (not "myself" or not provided), ask the user for it
- ALWAYS include a clear, descriptive subject line
- ALWAYS write a complete, well-formatted email body
- Execute tool calls immediately without asking for confirmation
"""

    if rag_tools_available:
        system_message += """
**Document Search Tools (RAG):**
- search_documents: Search through uploaded documents (PDFs, Excel, CSV, Word, etc.)
- list_document_sources: List all documents in the database
- get_document_stats: Get statistics about document database

**When to use document search:**
- User asks about content in their files/documents
- Questions about uploaded PDFs, spreadsheets, or reports
- Any query that might be answered by previously uploaded documents
"""

    system_message += """
**How to use these tools:**
1. For customer queries → use database tools
2. For web research → use search and visit_web"""

    if gmail_tools_available:
        system_message += "\n3. For email tasks → use Gmail tools"

    if rag_tools_available:
        system_message += "\n4. For document questions → use RAG search tools"

    system_message += "\n5. Always cite sources and be specific"

    # Stricter intent matching for all tools
    filtered_tools = []
    q = query.lower()
    # Multi-intent support: detect multiple intents in one query

    # Expanded phrase-level and multi-intent detection
    db_keywords = ["customer", "order", "database", "info", "details", "history", "client", "account", "user"]
    db_phrases = ["show customer", "get customer", "customer details", "order history", "list customers", "find customer"]
    doc_keywords = ["document", "pdf", "excel", "word", "csv", "file", "report", "spreadsheet"]
    doc_phrases = ["search documents", "find document", "list documents", "document stats", "upload file", "scan file"]
    email_keywords = ["email", "gmail", "send to myself", "my email", "mail", "inbox", "compose email", "read email"]
    email_phrases = ["search email", "send email", "read email", "get my email", "email me"]
    web_keywords = ["search", "find", "web", "news", "capital", "who", "what", "where", "when", "how", "lookup", "information", "facts"]
    web_phrases = ["search the web", "find info", "lookup", "get information", "web search", "current news", "latest news"]

    intents = set()
    # Phrase-level matching
    for phrase in db_phrases:
        if phrase in q:
            intents.add("db")
    for phrase in doc_phrases:
        if phrase in q:
            intents.add("doc")
    for phrase in email_phrases:
        if phrase in q:
            intents.add("email")
    for phrase in web_phrases:
        if phrase in q:
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
                    if phrase in part:
                        intents.add("db")
                for phrase in doc_phrases:
                    if phrase in part:
                        intents.add("doc")
                for phrase in email_phrases:
                    if phrase in part:
                        intents.add("email")
                for phrase in web_phrases:
                    if phrase in part:
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

    # Simple intent classifier fallback for ambiguous queries
    ambiguous = len(intents) == 0 or (len(q.split()) <= 3 and "web" not in intents)
    if ambiguous:
        intents = {"web"}

    # Save current intents to context history
    call_complete_agent.context_history.append({"query": query, "intents": intents})

    # Map intents to tools (handle all relevant tools for multi-intent)
    for tool in tools:
        tool_name = getattr(tool, "__name__", "")
        if "db" in intents and tool_name in ["nl2sql_query"]:
            filtered_tools.append(tool)
        if "doc" in intents and tool_name in ["search_documents", "list_document_sources", "get_document_stats"]:
            filtered_tools.append(tool)
        if "email" in intents and tool_name in ["search_gmail", "read_gmail", "send_gmail", "get_my_email"]:
            filtered_tools.append(tool)
        if "web" in intents and tool_name in ["search", "visit_web"]:
            filtered_tools.append(tool)

    # If no tools matched, fallback to web search tools
    if not filtered_tools:
        filtered_tools = [tool for tool in tools if getattr(tool, "__name__", "") in ["search", "visit_web"]]

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

        # Improved success/error logic
        output_str = str(final_output).strip() if final_output is not None else ""
        if not output_str or output_str.lower() in ["no output", "none", "null", "no results found."]:
            status = "Error"
        else:
            status = "Success"

        log_interaction(
            user_input=query,
            tools_used=tools_used,
            agent_messages=messages,
            output=final_output,
            status=status
        )

        return final_output
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
