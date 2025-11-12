# List all table names in the database
def list_tables() -> str:
    """
    List all table names in the customer database.
    Returns:
        A string with all table names, one per line.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return '\n'.join(tables) if tables else "No tables found."
    except Exception as e:
        return f"Error listing tables: {str(e)}"

# Describe columns and types for a specific table
def describe_table(table_name: str) -> str:
    """
    Show columns and types for a specific table.
    Args:
        table_name: Name of the table to describe.
    Returns:
        A string listing columns and types, or error message.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        conn.close()
        if not columns:
            return f"Table '{table_name}' not found."
        desc = [f"{col[1]} ({col[2]})" for col in columns]
        return f"Table: {table_name}\n" + '\n'.join(desc)
    except Exception as e:
        return f"Error describing table: {str(e)}"

# Safely execute a user-provided SQL query (read-only)
def run_custom_sql(sql: str) -> str:
    """
    Safely execute a user-provided SQL query (SELECT only).
    Args:
        sql: SQL query string (must start with SELECT).
    Returns:
        Query results or error message.
    """
    try:
        if not sql.strip().lower().startswith("select"):
            return "Only SELECT queries are allowed."
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        if not results:
            return "No results found."
        output = [" | ".join(columns)]
        for row in results:
            output.append(" | ".join(str(item) for item in row))
        return '\n'.join(output)
    except Exception as e:
        return f"Error executing custom SQL: {str(e)}"

# Return the number of rows in a table
def get_table_row_count(table_name: str) -> str:
    """
    Return the number of rows in a table.
    Args:
        table_name: Name of the table.
    Returns:
        String with row count or error message.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        conn.close()
        return f"Table '{table_name}' has {count} rows."
    except Exception as e:
        return f"Error getting row count: {str(e)}"
# Tool to show database schema
def show_database_schema() -> str:
    """
    Retrieve and display the schema of the customer database (tables and columns).
    Returns:
        A formatted string showing all tables and their columns.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        schema_info = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            schema_info.append(f"Table: {table}")
            for col in columns:
                schema_info.append(f"  - {col[1]} ({col[2]})")
        conn.close()
        return '\n'.join(schema_info) if schema_info else "No tables found in the database."
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"

import sqlite3
import os
from langchain_ollama import ChatOllama

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'customers.db')

# System prompt for NL2SQL
SYSTEM_PROMPT = """
You are an expert database assistant. Given a user's question in English and the following database schema, generate a safe SQL query to answer the question.

Schema:
Table: customers (id, name, email, phone, status, account_balance, join_date)
Table: orders (order_number, product, amount, status, order_date, customer_id)

Only generate the SQL query, do not explain or add extra text.
"""

# Initialize the reasoning LLM
model = ChatOllama(
        model="qwen3:4b",
        temperature=0.1,
        num_ctx=4096,
        verbose=False,
)

def nl2sql_query(user_question: str) -> str:
    """
    Translate an English question to SQL using qwen3:4b, execute it, and return results.
    Args:
        user_question: The user's question in English
    Returns:
        Query results or error message
    """
    prompt = SYSTEM_PROMPT + f"\nUser question: {user_question}\nSQL:"
    sql_query = model.invoke(prompt)
    # Extract SQL string from AIMessage if needed
    if hasattr(sql_query, "content"):
        sql_str = sql_query.content
    else:
        sql_str = str(sql_query)
    # Basic safety: only allow SELECT queries
    if not sql_str.strip().lower().startswith("select"):
        return f"Error: Only SELECT queries are allowed. Model generated: {sql_str}"
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_str)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        # Format results
        if not results:
            return "No results found."
        output = [" | ".join(columns)]
        for row in results:
            output.append(" | ".join(str(item) for item in row))
        return "\n".join(output)
    except Exception as e:
        return f"Error executing SQL: {str(e)}"
