"""
Quick test script to verify new model configuration
Tests both qwen3:4b LLM and nomic-embed-text embeddings
"""

def test_llm():
    """Test qwen3:4b model"""
    print("\n" + "=" * 80)
    print("TEST 1: Testing qwen3:4b LLM")
    print("=" * 80)
    
    try:
        from langchain_ollama import ChatOllama
        
        model = ChatOllama(
            model="qwen3:4b",
            temperature=0.3,
            num_ctx=8192,
        )
        
        print("\n✓ qwen3:4b model initialized")
        
        # Simple test
        response = model.invoke("What is 2+2? Answer in one word.")
        print(f"✓ Model response: {response.content}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing qwen3:4b: {e}")
        print("\nMake sure model is pulled:")
        print("  ollama pull qwen3:4b")
        return False


def test_embeddings():
    """Test nomic-embed-text embeddings"""
    print("\n" + "=" * 80)
    print("TEST 2: Testing nomic-embed-text Embeddings")
    print("=" * 80)
    
    try:
        from RAG.embeddings_config import get_default_embeddings
        
        print("\n✓ Initializing embeddings...")
        embeddings = get_default_embeddings()
        
        # Test embedding
        test_text = "Python is a programming language"
        vector = embeddings.embed_query(test_text)
        
        print(f"✓ Generated embedding vector")
        print(f"  Dimension: {len(vector)} (should be 768 for nomic-embed-text)")
        print(f"  First 5 values: {vector[:5]}")
        
        if len(vector) == 768:
            print("✓ Correct dimension for nomic-embed-text!")
        elif len(vector) == 384:
            print("⚠ Using 384 dimensions - might be fallback or old model")
        
        return True
    except Exception as e:
        print(f"✗ Error testing embeddings: {e}")
        print("\nMake sure model is pulled:")
        print("  ollama pull nomic-embed-text")
        return False


def test_agent_tools():
    """Test that agent loads with new configuration"""
    print("\n" + "=" * 80)
    print("TEST 3: Testing Agent Configuration")
    print("=" * 80)
    
    try:
        from agent_complete import model, tools
        
        print(f"\n✓ Agent loaded successfully")
        print(f"  Model: {model.model}")
        print(f"  Context window: {model.num_ctx}")
        print(f"  Temperature: {model.temperature}")
        print(f"  Number of tools: {len(tools)}")
        
        # List tools
        print("\n  Available tools:")
        for tool in tools:
            print(f"    - {tool.name}")
        
        return True
    except Exception as e:
        print(f"✗ Error loading agent: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "🚀 " * 20)
    print("Testing New Model Configuration")
    print("qwen3:4b + nomic-embed-text")
    print("🚀 " * 20)
    
    results = []
    
    # Test LLM
    results.append(("qwen3:4b LLM", test_llm()))
    
    # Test embeddings
    results.append(("nomic-embed-text Embeddings", test_embeddings()))
    
    # Test agent
    results.append(("Agent Configuration", test_agent_tools()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n" + "🎉 " * 20)
        print("ALL TESTS PASSED!")
        print("Your new configuration is ready to use:")
        print("  • qwen3:4b (128K context, thinking mode)")
        print("  • nomic-embed-text (768d, 8192 token context)")
        print("\nRun: streamlit run app.py")
        print("🎉 " * 20)
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        print("\nMake sure you have pulled the models:")
        print("  ollama pull qwen3:4b")
        print("  ollama pull nomic-embed-text")
    
    return all_passed


if __name__ == "__main__":
    main()
