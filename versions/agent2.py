from dotenv import load_dotenv
import os
# from langchain_groq import ChatGroq  # Commented out - using Ollama instead
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from tools.visit_web import visit_web


load_dotenv()

model = ChatOllama(model="llama3.2:1b", temperature=0.6)  # Using local Ollama
search = DuckDuckGoSearchResults()

tools = [search, visit_web]
memory = MemorySaver()

agent = create_agent(model, tools, checkpointer=memory)

config = {"configurable" : {
 "thread_id" : "abc123"
}}

#response = search.invoke("who is the prime minister of india?")
#print(response)

# Pass messages as a list with a system message to guide behavior

def call_web_agent(query: str):
    """Call agent with web search and visit_web tools only"""
    response = agent.invoke({
        "messages": [
            SystemMessage(content="""You are a helpful research assistant. When answering questions:
    1. First use duckduckgo_results_json to search and find relevant URLs
    2. Then use visit_web to visit the most relevant URL from the search results to get detailed, real-time information
    3. Provide a comprehensive answer based on the content you retrieved from the website

    Always visit websites for questions that need current/live data."""),
            HumanMessage(content=f"{query}")
        ]
    }, config=config)

    for message in response['messages']:
        print(f"--- {message.type} ---")
        print(message.content, "\n")

        if hasattr(message, "tool_calls"):
            print(message.tool_calls, "\n")

    return response["messages"][-1].content