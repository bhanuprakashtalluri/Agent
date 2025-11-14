from difflib import SequenceMatcher
from .llm_cache import cached_tool


@cached_tool(ttl_seconds=60 * 30, cache_type="excel_get_cached_response", write_to_query_store=True)
def get_cached_response(query: str, threshold: float = 0.8):
    print(f"\n[get_cached_response] Input: query={query}, threshold={threshold}")
    """
    Search the Excel log for a similar user query and return the cached output if found.
    Args:
        query: The user query to match
        threshold: Similarity threshold (0-1, default 0.8)
    Returns:
        Dict with cached response (output, user_input, timestamp, status) or None if not found
    """
    if not os.path.exists(EXCEL_LOG_PATH):
        print("[get_cached_response] Excel log not found.")
        return None
    wb = load_workbook(EXCEL_LOG_PATH)
    ws = wb.active
    best_match = None
    best_score = 0.0
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
        user_input = row[1]
        score = SequenceMatcher(None, query, user_input).ratio()
        if score > best_score and score >= threshold:
            best_score = score
            best_match = {
                "timestamp": row[0],
                "user_input": user_input,
                "output": row[4],
                "status": row[5],
                "similarity": score
            }
    print(f"[get_cached_response] Output: {best_match}")
    return best_match
@cached_tool(ttl_seconds=60 * 5, cache_type="excel_history", write_to_query_store=True)
def get_conversation_history(last_n: int = 5, all_history: bool = False):
    print(f"\n[get_conversation_history] Input: last_n={last_n}, all_history={all_history}")
    """
    Retrieve recent or all conversation history from the Excel log.
    Args:
        last_n: Number of recent interactions to fetch (default 5)
        all_history: If True, return all interactions
    Returns:
        List of dicts with keys: timestamp, user_input, output, status
    """
    if not os.path.exists(EXCEL_LOG_PATH):
        print("[get_conversation_history] Excel log not found.")
        return []
    wb = load_workbook(EXCEL_LOG_PATH)
    ws = wb.active
    history = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
        history.append({
            "timestamp": row[0],
            "user_input": row[1],
            "tools_used": row[2],
            "sources": row[3],
            "output": row[4],
            "status": row[5],
        })
    print(f"[get_conversation_history] Output: {history if all_history else history[-last_n:]}")
    if all_history:
        return history
    return history[-last_n:] if len(history) >= last_n else history
import os
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
import re


EXCEL_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'agent_logs.xlsx')


def initialize_excel_log():
    print("\n[initialize_excel_log] Called")
    """Create Excel file with headers if it doesn't exist"""
    if not os.path.exists(EXCEL_LOG_PATH):
        wb = Workbook()
        ws = wb.active
        ws.title = "Agent Logs"
        
        # Headers
        headers = ['Timestamp', 'User Input', 'Tools Used', 'Sources/URLs', 'Output', 'Status']
        ws.append(headers)
        
        # Style headers
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Set column widths
        ws.column_dimensions['A'].width = 20  # Timestamp
        ws.column_dimensions['B'].width = 40  # User Input
        ws.column_dimensions['C'].width = 25  # Tools Used
        ws.column_dimensions['D'].width = 50  # Sources/URLs
        ws.column_dimensions['E'].width = 60  # Output
        ws.column_dimensions['F'].width = 12  # Status
        
        wb.save(EXCEL_LOG_PATH)
        print(f"Excel log created at: {EXCEL_LOG_PATH}")


def extract_urls(text: str) -> list:
    """Extract URLs from text"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)


def log_interaction(user_input: str, tools_used: list, agent_messages: list, output: str, status: str = "Success"):
    """
    Log user interaction to Excel file
    
    Args:
        user_input: The user's query
        tools_used: List of tools that were called
        agent_messages: All messages from the agent (to extract URLs)
        output: The final output/response
        status: Status of the interaction (Success/Error)
    """
    try:
        # Initialize if needed
        initialize_excel_log()
        
        # Load workbook
        wb = load_workbook(EXCEL_LOG_PATH)
        ws = wb.active
        
        # Extract sources/URLs from messages
        sources = []
        for msg in agent_messages:
            if hasattr(msg, 'content') and msg.content:
                urls = extract_urls(str(msg.content))
                sources.extend(urls)
        
        # Remove duplicates and format
        sources = list(set(sources))
        sources_str = '\n'.join(sources[:5]) if sources else 'No URLs'  # Limit to 5 URLs
        
        # Format tools used
        tools_str = ', '.join(tools_used) if tools_used else 'None'
        
        # Prepare row data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = [
            timestamp,
            user_input[:500],  # Limit user input length
            tools_str,
            sources_str,
            output[:1000] if output else 'No output',  # Limit output length
            status
        ]
        
        # Append row
        ws.append(row_data)
        
        # Style the new row
        row_num = ws.max_row
        for cell in ws[row_num]:
            cell.alignment = Alignment(wrap_text=True, vertical='top')
        
        # Color code status
        status_cell = ws.cell(row=row_num, column=6)
        if status == "Success":
            status_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            status_cell.font = Font(color="006100")
        else:
            status_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            status_cell.font = Font(color="9C0006")
        
        # Save
        wb.save(EXCEL_LOG_PATH)
        print(f"Logged to Excel: {EXCEL_LOG_PATH}")
        
        return True
    
    except Exception as e:
        print(f"Error logging to Excel: {e}")
        return False


def get_log_summary():
    """Get summary statistics from the log"""
    try:
        if not os.path.exists(EXCEL_LOG_PATH):
            return "No log file exists yet"
        
        wb = load_workbook(EXCEL_LOG_PATH)
        ws = wb.active
        
        total_queries = ws.max_row - 1  # Exclude header
        
        if total_queries == 0:
            return "No queries logged yet"
        
        # Count successes and errors
        success_count = 0
        error_count = 0
        
        for row in ws.iter_rows(min_row=2, max_col=6, max_row=ws.max_row):
            status = row[5].value
            if status == "Success":
                success_count += 1
            else:
                error_count += 1
        
        summary = f"""Log Summary:
- Total Queries: {total_queries}
- Successful: {success_count}
- Errors: {error_count}
- Log File: {EXCEL_LOG_PATH}"""
        
        return summary
    
    except Exception as e:
        return f"Error reading log: {e}"
