# Ollama Setup Guide

## What is Ollama?

Ollama allows you to run large language models locally on your machine - **completely free with no API limits!**

## Installation Steps

### 1. Install Ollama

**For macOS:**
```bash
# Download and install from https://ollama.ai
# Or use brew:
brew install ollama
```

**For Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**For Windows:**
Download from https://ollama.ai/download/windows

### 2. Start Ollama Service

```bash
ollama serve
```

Leave this terminal running in the background.

### 3. Pull a Model

Open a new terminal and pull the model:

```bash
# Pull llama3.2 (recommended - good balance of speed and quality)
ollama pull llama3.2

# Or pull other models:
# ollama pull llama3.1       # Larger, more capable
# ollama pull mistral        # Fast and efficient
# ollama pull codellama      # Good for code
```

### 4. Install Python Dependencies

```bash
pip install langchain-ollama
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 5. Test Ollama

```bash
# Test in terminal
ollama run llama3.2
# Type a question and press Enter
# Type /bye to exit
```

## Available Models

| Model | Size | Best For | Speed |
|-------|------|----------|-------|
| llama3.2 | ~2GB | General use, fast | ⚡⚡⚡ |
| llama3.1 | ~4GB | Better quality | ⚡⚡ |
| mistral | ~4GB | Fast, efficient | ⚡⚡⚡ |
| codellama | ~3GB | Code generation | ⚡⚡ |
| llama2 | ~3GB | Older but stable | ⚡⚡ |

## Change Model in Agent

To use a different model, edit the agent files:

```python
# In agent_complete.py, agent2.py, agent3.py
model = ChatOllama(model="llama3.2", temperature=0.6)

# Change to:
model = ChatOllama(model="mistral", temperature=0.6)  # or any model you pulled
```

## Troubleshooting

### Ollama not found
```bash
# Check if Ollama is installed
ollama --version

# If not installed, install it from https://ollama.ai
```

### Connection refused
```bash
# Make sure Ollama service is running
ollama serve

# Or check if it's already running:
ps aux | grep ollama
```

### Model not found
```bash
# List installed models
ollama list

# Pull the model if not installed
ollama pull llama3.2
```

### Slow performance
- Try a smaller model like `llama3.2` instead of `llama3.1`
- Ensure Ollama service is running
- Close other heavy applications

## Advantages of Ollama

✅ **Free** - No API costs
✅ **No limits** - Unlimited queries
✅ **Privacy** - All data stays local
✅ **Offline** - Works without internet
✅ **Fast** - No network latency

## Run Your Agent

After setting up Ollama:

```bash
# Start Ollama service (in one terminal)
ollama serve

# Run your agent (in another terminal)
streamlit run app.py
```

---

**Need help?** Check https://ollama.ai/docs
