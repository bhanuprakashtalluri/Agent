from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import HumanMessage
#from langgraph.prebuilt import create_react_agent
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver


load_dotenv()

model = ChatGroq(model="llama-3.2:1b", temperature=0.6)
search = DuckDuckGoSearchResults()
tools = [search]
memory = MemorySaver()

#agent = create_react_agent(model, tools, checkpointer = memory)
agent = create_agent(model, tools, checkpointer = memory)

config = {"configurable" : {
 "thread_id" : "abc123"
}}

#response = search.invoke("who is the prime minister of india?")
#print(response)

# Pass messages as a list
response = agent.invoke({
    "messages": [HumanMessage(content="who is the prime minister of india?")]
},config=config)

for message in response['messages']:
    print(f"--- {message.type} ---")
    print(message.content, "\n")

    if hasattr(message, "tool_calls"):
        print(message.tool_calls, "\n")