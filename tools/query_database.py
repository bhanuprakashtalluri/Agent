"""High-level helpers for natural-language to SQL interactions."""

import os
import sqlite3
from typing import List

from langchain_ollama import ChatOllama

from tools.cache_manager import CacheManager
from tools.llm_cache import cached_invoke, cached_sql_query

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'customers.db')

# System prompt for NL2SQL
SYSTEM_PROMPT = """
You are an expert database assistant. Given a user's question in English and the following database schema, generate a safe SQL query to answer the question.

Schema:
Table: customers (id, name, email, phone, status, account_balance, join_date)
Table: orders (order_number, product, amount, status, order_date, customer_id)

IMPORTANT:
When searching for names (e.g., 'John' or 'John Smith'), always use a case-insensitive LIKE clause with wildcards on both sides: WHERE name LIKE '%John%' or WHERE name LIKE '%John Smith%'.
If the exact name is not found, also search for similar names using LIKE with each word in the query (e.g., WHERE name LIKE '%John%' OR name LIKE '%Smith%').
If no exact match is found, return similar names found in the database and indicate that these are similar matches.

When returning results for similar matches, clearly state that no exact match was found for the searched name. Group and label orders under each actual customer name, not under the searched name. Do not mislabel or merge data. Example:
No exact match found for "John Smith". Showing similar matches:
Customer: John Doe
Order: ...
Customer: Jane Smith
Order: ...

GENERAL INSTRUCTIONS:
For queries involving related information from multiple tables, always use SQL JOINs by inferring the correct foreign key relationships from the schema provided above.
When searching for names or similar fields, use a case-insensitive LIKE clause with wildcards on both sides (e.g., WHERE name LIKE '%John%').
Do not hardcode table or column names—always infer relationships and columns from the schema.
If no exact match is found, return similar names found in the database and indicate that these are similar matches, grouped and labeled correctly.

To reduce token usage, always:
- Limit the number of rows returned using LIMIT clauses (e.g., LIMIT 10).
- Avoid selecting all columns (SELECT *) unless necessary; prefer selecting only relevant columns.
- Do not include unnecessary data or metadata in the results.

IMPORTANT: Return only the query results, not the SQL query itself. Do not include the SQL query in your response, unless explicitly requested.
"""
cache = CacheManager()


def split_to_subqueries_with_llm(user_question: str) -> List[str]:
    """Break a multi-part NL question into focused SQL sub-queries.

    Args:
        user_question: Original user request expressed in English.

    Returns:
        List of numbered sub-queries extracted from the LLM response.
    """
    print(f"\n[split_to_subqueries_with_llm] Input: {user_question}")
    split_prompt = (
        "You are an expert database assistant. Given the following user question, break it down into distinct sub-queries. "
        "Each sub-query should be answerable by a single SQL SELECT statement. "
        "Return only the sub-queries as a numbered list, no explanations.\n\nUser question: " + user_question
    )
    text = cached_invoke(
        model,
        split_prompt,
        cache=cache,
        cache_type="llm_split",
        ttl_seconds=300,
        model_name=str(getattr(model, "model", "qwen3")),
    )
    print(f"[split_to_subqueries_with_llm] Raw LLM response: {text}")
    # Parse numbered list into sub-queries
    import re
    sub_queries = re.findall(r"\d+\.\s*(.+)", text)
    if not sub_queries:
        # fallback: split by newlines
        sub_queries = [line.strip() for line in text.splitlines() if line.strip()]
    print(f"[split_to_subqueries_with_llm] Output sub-queries: {sub_queries}")
    return sub_queries

def handle_multi_query_with_llm(user_question: str) -> str:
    """
    Use LLM to split multi-part question, then run nl2sql_query for each sub-query and aggregate results.
    Args:
        user_question: The user's multi-part question in English
    Returns:
        Aggregated string containing results for each generated sub-query.
    """
    print(f"\n[handle_multi_query_with_llm] Input: {user_question}")
    sub_queries = split_to_subqueries_with_llm(user_question)
    results = []
    for idx, q in enumerate(sub_queries, 1):
        result = nl2sql_query(q)
        print(f"[handle_multi_query_with_llm] Sub-query Q{idx}: {q}\nResult:\n{result}")
        results.append(f"Q{idx}: {q}\n{result}\n")
    output = '\n'.join(results)
    print(f"[handle_multi_query_with_llm] Final output:\n{output}")
    return output

# Initialize the reasoning LLM
model = ChatOllama(
        model="qwen3:4b",
        temperature=0.1,
        num_ctx=4096,
        verbose=False,
)

def nl2sql_query(user_question: str) -> str:
    """Translate an English question into SQL, execute it, and format results.

    Args:
        user_question: Question to answer using the customer database.

    Returns:
        Formatted rows or an error message describing why execution failed.
    """
    prompt = SYSTEM_PROMPT + f"\nUser question: {user_question}\nSQL:"
    sql_str = cached_invoke(model, prompt, cache, cache_type="nl2sql",
                            ttl_seconds=60, model_name=str(getattr(model, 'model', 'qwen3')))
    # Print raw LLM response (string)
    print("\n--- LLM Raw Response ---")
    print(sql_str)
    print("\n--- LLM Generated SQL Query ---")
    print(sql_str)
    # Basic safety: only allow SELECT queries
    if not sql_str.strip().lower().startswith("select"):
        print("\n--- LLM Output (Non-SELECT) ---")
        print(sql_str)
        return f"Error: Only SELECT queries are allowed. Model generated: {sql_str}"
    try:
        def executor():
            conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute(sql_str)
            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            conn.close()
            return cols, rows

        columns, results = cached_sql_query(
            sql_str,
            executor,
            cache=cache,
            cache_type="sql_results",
            ttl_seconds=30,
        )
        print("\n--- Raw DB Results ---")
        print("Columns:", columns)
        print("Rows:", results)
        # Format results
        if not results:
            return "No results found."
        # Post-process: check if searched name is an exact match
        import re
        searched_name = None
        name_match = re.search(r"show (?:all )?orders of ([\w ]+)", user_question.lower())
        if name_match:
            searched_name = name_match.group(1).strip().title()
        # Find all customer names in results
        name_idx = None
        for idx, col in enumerate(columns):
            if col.lower() == "name":
                name_idx = idx
                break
        found_names = set()
        if name_idx is not None:
            for row in results:
                found_names.add(str(row[name_idx]))
        # If searched_name is not in found_names, label as similar matches
        output = []
        if searched_name and name_idx is not None and searched_name not in found_names:
            output.append(f'No exact match found for "{searched_name}". Showing similar matches:')
            # Group by customer name
            from collections import defaultdict
            grouped = defaultdict(list)
            for row in results:
                grouped[row[name_idx]].append(row)
            for cname, rows in grouped.items():
                output.append(f'\nCustomer: {cname}')
                output.append(" | ".join(columns))
                for row in rows:
                    output.append(" | ".join(str(item) for item in row))
        else:
            output.append(" | ".join(columns))
            for row in results:
                output.append(" | ".join(str(item) for item in row))
        return "\n".join(output)
    except Exception as e:
        print("\n--- DB Error ---")
        print(str(e))
        return f"Error executing SQL: {str(e)}"
    
# List all table names in the database
def list_tables() -> str:
    """
    List all table names in the customer database.
    Returns:
        A string with all table names, one per line.
    """
    print("\n[list_tables] Called")
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        print(f"[list_tables] Output: {tables}")
        return '\n'.join(tables) if tables else "No tables found."
    except Exception as e:
        print(f"[list_tables] Error: {str(e)}")
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
    print(f"\n[describe_table] Input: {table_name}")
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        conn.close()
        print(f"[describe_table] Output: {columns}")
        if not columns:
            return f"Table '{table_name}' not found."
        desc = [f"{col[1]} ({col[2]})" for col in columns]
        return f"Table: {table_name}\n" + '\n'.join(desc)
    except Exception as e:
        print(f"[describe_table] Error: {str(e)}")
        return f"Error describing table: {str(e)}"

# Return the number of rows in a table
def get_table_row_count(table_name: str) -> str:
    """
    Return the number of rows in a table.
    Args:
        table_name: Name of the table.
    Returns:
        String with row count or error message.
    """
    print(f"\n[get_table_row_count] Input: {table_name}")
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"[get_table_row_count] Output: {count}")
        return f"Table '{table_name}' has {count} rows."
    except Exception as e:
        print(f"[get_table_row_count] Error: {str(e)}")
        return f"Error getting row count: {str(e)}"
# Tool to show database schema
def show_database_schema() -> str:
    """
    Retrieve and display the schema of the customer database (tables and columns).
    Returns:
        A formatted string showing all tables and their columns.
    """
    print("\n[show_database_schema] Called")
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"[show_database_schema] Tables: {tables}")
        schema_info = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            print(f"[show_database_schema] Table: {table}, Columns: {columns}")
            schema_info.append(f"Table: {table}")
            for col in columns:
                schema_info.append(f"  - {col[1]} ({col[2]})")
        conn.close()
        output = '\n'.join(schema_info) if schema_info else "No tables found in the database."
        print(f"[show_database_schema] Output:\n{output}")
        return output
    except Exception as e:
        print(f"[show_database_schema] Error: {str(e)}")
        return f"Error retrieving schema: {str(e)}"

