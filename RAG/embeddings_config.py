"""
Embeddings Configuration
Provides embedding models for RAG system
"""

from langchain_ollama import OllamaEmbeddings


def get_embeddings_model(model_type: str = "openrouter"):
    """
    Get embeddings model for vector store
    
    Args:
        model_type: Type of embeddings ('ollama' or 'fake' for testing)
        
    Returns:
        Embeddings model instance
    """
    
    if model_type == "ollama":
        # Use Ollama for embeddings (requires nomic-embed-text model)
        try:
            return OllamaEmbeddings(
                model="nomic-embed-text",
            )
        except Exception as e:
            print(f"⚠ Warning: Could not initialize Ollama embeddings: {e}")
            print("Please run: ollama pull nomic-embed-text")
            print("Falling back to fake embeddings for testing...")
            from langchain_community.embeddings import FakeEmbeddings
            return FakeEmbeddings(size=768)
    elif model_type == "fake":
        from langchain_community.embeddings import FakeEmbeddings
        print("Using FakeEmbeddings for testing. Install nomic-embed-text for production use.")
        return FakeEmbeddings(size=768)
    else:
        raise ValueError(f"Unknown model_type: {model_type}. Use 'ollama' or 'fake'")


def get_default_embeddings():
    """
    Get default embeddings model (OpenRouter-compatible or FakeEmbeddings)
    Returns:
        Embeddings model (FakeEmbeddings for now)
    """
    return get_embeddings_model("ollama")


if __name__ == "__main__":
    # Test embeddings
    print("Testing HuggingFace embeddings...")
    embeddings = get_embeddings_model("huggingface")
    
    test_text = "This is a test document"
    vector = embeddings.embed_query(test_text)
    print(f"✓ Generated embedding vector of dimension: {len(vector)}")
