"""
Test Script for RAG Functionality
Demonstrates document loading, vector storage, and search
"""

import sys
from pathlib import Path

# Test imports
print("Testing RAG imports...")
try:
    from RAG.document_loader import DocumentLoader
    from RAG.vector_store import VectorStoreManager
    from RAG.embeddings_config import get_default_embeddings
    from langchain_core.documents import Document
    print("✓ All RAG imports successful\n")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nPlease install dependencies:")
    print("pip install chromadb sentence-transformers pypdf pdfplumber python-docx unstructured tiktoken")
    sys.exit(1)


def test_document_loader():
    """Test the document loader"""
    print("=" * 80)
    print("TEST 1: Document Loader")
    print("=" * 80)
    
    loader = DocumentLoader()
    
    # Show supported formats
    print("\nSupported file formats:")
    for ext, desc in loader.SUPPORTED_EXTENSIONS.items():
        print(f"  .{ext:8} - {desc}")
    
    # Create a test text file
    test_file = Path("RAG/documents/test_sample.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_content = """
    This is a test document for RAG system.
    
    Python Programming Language
    Python is a high-level, interpreted programming language known for its simplicity and readability.
    It was created by Guido van Rossum and first released in 1991.
    
    Key Features:
    - Easy to learn and use
    - Extensive standard library
    - Great for data science and machine learning
    - Cross-platform compatibility
    
    Popular Uses:
    - Web development (Django, Flask)
    - Data analysis (pandas, numpy)
    - Machine learning (scikit-learn, tensorflow)
    - Automation and scripting
    """
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print(f"\n✓ Created test file: {test_file}")
    
    # Load the document
    try:
        documents = loader.load_document(str(test_file))
        print(f"✓ Loaded {len(documents)} document(s)")
        print(f"  Content length: {len(documents[0].page_content)} characters")
        print(f"  Metadata: {documents[0].metadata}")
        return True
    except Exception as e:
        print(f"✗ Error loading document: {e}")
        return False


def test_embeddings():
    """Test embedding generation"""
    print("\n" + "=" * 80)
    print("TEST 2: Embeddings")
    print("=" * 80)
    
    try:
        print("\nGenerating embeddings...")
        print("Note: Requires 'ollama pull all-minilm:33m' or FakeEmbeddings will be used")
        embeddings = get_default_embeddings()
        
        # Test embedding
        test_text = "Python is a programming language"
        vector = embeddings.embed_query(test_text)
        
        print(f"✓ Generated embedding vector")
        print(f"  Dimension: {len(vector)}")
        print(f"  First 5 values: {vector[:5]}")
        return True
    except Exception as e:
        print(f"✗ Error generating embeddings: {e}")
        print("Make sure Ollama is running and all-minilm:33m model is pulled:")
        print("  ollama pull all-minilm:33m")
        return False


def test_vector_store():
    """Test vector store operations"""
    print("\n" + "=" * 80)
    print("TEST 3: Vector Store")
    print("=" * 80)
    
    try:
        # Initialize vector store
        print("\nInitializing vector store...")
        vs = VectorStoreManager(
            persist_directory="data/vector_db_test",
            collection_name="test_collection"
        )
        print("✓ Vector store initialized")
        
        # Create test documents
        test_docs = [
            Document(
                page_content="Python is a high-level programming language known for simplicity.",
                metadata={'source': 'test1.txt', 'type': 'txt', 'topic': 'python'}
            ),
            Document(
                page_content="JavaScript is a scripting language primarily used for web development.",
                metadata={'source': 'test2.txt', 'type': 'txt', 'topic': 'javascript'}
            ),
            Document(
                page_content="Machine learning is a subset of artificial intelligence.",
                metadata={'source': 'test3.txt', 'type': 'txt', 'topic': 'ai'}
            ),
            Document(
                page_content="Data science involves extracting insights from data using statistics and programming.",
                metadata={'source': 'test4.txt', 'type': 'txt', 'topic': 'data_science'}
            ),
        ]
        
        # Add documents
        print("\nAdding test documents...")
        ids = vs.add_documents(test_docs, chunk=False)
        print(f"✓ Added {len(ids)} documents")
        
        # Get stats
        stats = vs.get_stats()
        print(f"\nVector Store Stats:")
        print(f"  Collection: {stats['collection_name']}")
        print(f"  Documents: {stats['document_count']}")
        
        # Test search
        print("\n--- Search Test 1: Programming Languages ---")
        query1 = "programming languages"
        results1 = vs.similarity_search_with_score(query1, k=2)
        print(f"Query: '{query1}'")
        for idx, (doc, score) in enumerate(results1, 1):
            print(f"\nResult {idx} (Relevance: {1-score:.3f}):")
            print(f"  Content: {doc.page_content[:80]}...")
            print(f"  Source: {doc.metadata['source']}")
        
        print("\n--- Search Test 2: Artificial Intelligence ---")
        query2 = "artificial intelligence"
        results2 = vs.similarity_search_with_score(query2, k=2)
        print(f"Query: '{query2}'")
        for idx, (doc, score) in enumerate(results2, 1):
            print(f"\nResult {idx} (Relevance: {1-score:.3f}):")
            print(f"  Content: {doc.page_content[:80]}...")
            print(f"  Source: {doc.metadata['source']}")
        
        # Test metadata filtering
        print("\n--- Search Test 3: Metadata Filter ---")
        results3 = vs.similarity_search(
            query="programming",
            k=5,
            filter_dict={'topic': 'python'}
        )
        print(f"Query: 'programming' with filter topic='python'")
        print(f"Found {len(results3)} result(s)")
        for doc in results3:
            print(f"  - {doc.metadata['source']}: {doc.page_content[:60]}...")
        
        # Cleanup test vector store
        print("\n✓ All vector store tests passed")
        print("Cleaning up test database...")
        vs.delete_collection()
        print("✓ Test collection deleted")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in vector store test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_tools():
    """Test RAG tools integration"""
    print("\n" + "=" * 80)
    print("TEST 4: RAG Tools")
    print("=" * 80)
    
    try:
        from tools.rag_tools import search_documents, list_document_sources, get_document_stats
        print("✓ RAG tools imported successfully")
        
        # Test document stats
        print("\n--- Testing get_document_stats ---")
        stats_result = get_document_stats.invoke({})
        print(stats_result)
        
        # Test list sources
        print("\n--- Testing list_document_sources ---")
        sources_result = list_document_sources.invoke({})
        print(sources_result)
        
        print("\n✓ RAG tools test complete")
        return True
        
    except Exception as e:
        print(f"✗ Error testing RAG tools: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("RAG SYSTEM TEST SUITE")
    print("=" * 80 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Document Loader", test_document_loader()))
    results.append(("Embeddings", test_embeddings()))
    results.append(("Vector Store", test_vector_store()))
    results.append(("RAG Tools", test_rag_tools()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! RAG system is ready to use.")
        print("\nNext steps:")
        print("1. Upload documents: python upload_documents.py upload your_file.pdf")
        print("2. Run agent: streamlit run app.py")
        print("3. Ask questions about your documents!")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")


if __name__ == "__main__":
    main()
