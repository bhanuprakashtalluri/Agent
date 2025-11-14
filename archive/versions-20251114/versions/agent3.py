from dotenv import load_dotenv
import os
# from langchain_groq import ChatGroq  # Commented out - using Ollama instead
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from tools.visit_web import visit_web
from tools.db_tools import query_customer_info, query_customer_orders, list_all_customers


load_dotenv()

model = ChatOllama(model="llama3.2:1b", temperature=0.6)  # Using local Ollama
search = DuckDuckGoSearchResults()

tools = [search, visit_web, query_customer_info, query_customer_orders, list_all_customers]
memory = MemorySaver()

agent = create_agent(model, tools, checkpointer=memory)

config = {"configurable" : {
 "thread_id" : "abc123"
}}

#response = search.invoke("who is the prime minister of india?")
#print(response)

# Pass messages as a list with a system message to guide behavior

def call_full_agent(query: str):
    """Call agent with web search, visit_web, and database tools"""
    response = agent.invoke({
        "messages": [
            SystemMessage(content="""You are a helpful research and customer service assistant. You have access to multiple tools:

    1. **Database Tools** - For customer information:
       - query_customer_info: Search customer details by name
       - query_customer_orders: Get order history for a customer
       - list_all_customers: View all customers in the system
    
    2. **Web Search Tools** - For current information:
       - duckduckgo_results_json: Search the web for information
       - visit_web: Visit specific URLs to get detailed content

    When answering questions:
    - For customer/order queries: Use the database tools first
    - For general knowledge/current events: Use web search tools
    - Always be specific and cite your sources
    - If you need current/live web data, use visit_web after searching"""),
            HumanMessage(content=f"{query}")
        ]
    }, config=config)

    for message in response['messages']:
        print(f"--- {message.type} ---")
        print(message.content, "\n")

        if hasattr(message, "tool_calls"):
            print(message.tool_calls, "\n")

    return response["messages"][-1].content