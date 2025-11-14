# Agent Versions

This folder contains previous iterations of the agent during development.

## Files

### agent.py
**Original version** - Basic agent with ChatGroq API
- Uses cloud-based ChatGroq (llama-3.3-70b-versatile)
- Only DuckDuckGo search tool
- Minimal functionality
- For initial testing

### agent2.py
**Web Agent** - Research assistant
- Uses local Ollama (llama3.2:1b)
- Tools: DuckDuckGo search + visit_web
- Focused on web research and content extraction
- Good for information gathering

### agent3.py
**Full Agent** - Customer service + research
- Uses local Ollama (llama3.2:1b)
- Tools: Web search + database queries
- Customer information management
- Combined customer service and research capabilities

## Current Production Agent

The main production agent is:
- **`../agent_complete.py`** - All features + Gmail + Excel logging

## Usage

These files are kept for reference and can be imported if you want to use simpler agent configurations:

```python
from versions.agent2 import call_web_agent
from versions.agent3 import call_full_agent
```

## Migration Notes

All agents have been moved to use consistent paths:
- Database: `../data/customers.db`
- Logs: `../data/agent_logs.xlsx`
- Gmail config: `../config/gmail_credentials.json`
