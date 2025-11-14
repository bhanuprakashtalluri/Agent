"""
RAG Tools for LangChain Agent
Provides document search and retrieval capabilities
"""

from langchain.tools import tool
from typing import Optional

from RAG.vector_store import VectorStoreManager
from pathlib import Path
import pandas as pd


# Initialize vector store (singleton pattern)
_vector_store = None

def get_vector_store() -> VectorStoreManager:
    """Get or create vector store instance"""
    print("\n[get_vector_store] Called")
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager(
            persist_directory="data/vector_db",
            collection_name="documents"
        )
    return _vector_store


@tool
def search_documents(query: str, num_results: int = 3) -> str:
    """
    Search through uploaded documents using semantic similarity.
    Use this tool when the user asks about information that might be in their documents,
    files, PDFs, Excel sheets, or any uploaded content.
    
    Args:
        query: The search query to find relevant information
        num_results: Number of results to return (default: 3)
        
    Returns:
        String with relevant document excerpts and sources
    """
    print(f"\n[search_documents] Input: query={query}, num_results={num_results}")
    try:
        vs = get_vector_store()
        print(f"[search_documents] Vector store: {vs}")
            
            # Get stats first to check if documents exist
        stats = vs.get_stats()
        doc_count = stats.get('document_count', 0)
        print(f"[search_documents] Stats: {stats}")
            
        if doc_count == 0:
            print("[search_documents] No documents uploaded.")
            return (
                "No documents have been uploaded to the system yet. "
                "Please use the document upload functionality to add documents first."
            )
        
        # Perform similarity search with scores
        results = vs.similarity_search_with_score(query, k=num_results)
        print(f"[search_documents] Raw results: {results}")
        
        if not results:
            print(f"[search_documents] No relevant information found for: {query}")
            return f"No relevant information found for: {query}"
        
        # Format results
        output = f"Found {len(results)} relevant document(s):\n\n"
        
        for idx, (doc, score) in enumerate(results, 1):
            # Get metadata
            source = doc.metadata.get('source', 'Unknown')
            doc_type = doc.metadata.get('type', 'Unknown')
            
            # Format content (limit length)
            content = doc.page_content
            if len(content) > 500:
                content = content[:500] + "..."
            
            output += f"**Result {idx}** (Relevance: {1-score:.2f})\n"
            output += f"Source: {source} ({doc_type})\n"
            output += f"Content:\n{content}\n\n"
            output += "-" * 80 + "\n\n"
        
        print(f"[search_documents] Output: {output}")
        return output
    
    except Exception as e:
        print(f"[search_documents] Error: {str(e)}")
        return f"Error searching documents: {str(e)}"


@tool
def list_document_sources() -> str:
    """
    List all documents that have been uploaded to the system.
    Use this to see what documents are available for searching.
    
    Returns:
        String listing all document sources
    """
    try:
        vs = get_vector_store()
        
        # Get stats
        stats = vs.get_stats()
        doc_count = stats.get('document_count', 0)
        
        if doc_count == 0:
            return "No documents have been uploaded yet."
        
        # Try to get unique sources from metadata
        # This is a workaround - get a large sample and extract sources
        try:
            results = vs.similarity_search("", k=100)  # Get up to 100 chunks
            
            sources = {}
            for doc in results:
                source = doc.metadata.get('source', 'Unknown')
                doc_type = doc.metadata.get('type', 'Unknown')
                
                if source not in sources:
                    sources[source] = doc_type
            
            output = f"Total document chunks in database: {doc_count}\n\n"
            output += f"Unique documents ({len(sources)}):\n\n"
            
            for idx, (source, doc_type) in enumerate(sources.items(), 1):
                output += f"{idx}. {source} ({doc_type})\n"
            
            return output
        
        except Exception as e:
            return f"Database contains {doc_count} document chunks. Error listing sources: {str(e)}"
    
    except Exception as e:
        return f"Error listing documents: {str(e)}"


@tool  
def get_document_stats() -> str:
    """
    Get statistics about the document database.
    Use this to check how many documents are stored.
    
    Returns:
        String with database statistics
    """
    try:
        vs = get_vector_store()
        stats = vs.get_stats()
        
        output = "📊 Document Database Statistics:\n\n"
        output += f"Collection: {stats.get('collection_name', 'Unknown')}\n"
        output += f"Total chunks: {stats.get('document_count', 0)}\n"
        output += f"Storage: {stats.get('persist_directory', 'Unknown')}\n"
        
        if 'error' in stats:
            output += f"\n⚠ Error: {stats['error']}"
        
        return output
    
    except Exception as e:
        return f"Error getting stats: {str(e)}"


# Export all RAG tools
rag_tools = [search_documents, list_document_sources, get_document_stats]


@tool
def read_csv(filename: str, preview_rows: int = 20) -> str:
    """
    Read a CSV file from the project's allowed directories and return a preview.

    The function only reads files under `RAG/documents/uploads` or `data` to avoid
    exposing arbitrary filesystem access.

    Args:
        filename: Name of the CSV file (e.g. 'address_details.csv')
        preview_rows: Number of rows to include in the preview

    Returns:
        A string containing a markdown table preview of the CSV or an error message.
    """
    try:
        allowed_dirs = [Path("RAG/documents/uploads"), Path("data")]
        target_path = None
        for d in allowed_dirs:
            p = d / filename
            if p.exists() and p.is_file():
                target_path = p
                break
        if target_path is None:
            return f"Error: File '{filename}' not found in allowed directories ({', '.join(str(d) for d in allowed_dirs)})"

        df = pd.read_csv(target_path)
        preview = df.head(preview_rows)
        # Convert to markdown table
        try:
            md = preview.to_markdown(index=False)
        except Exception:
            md = preview.to_csv(index=False)
        return md
    except Exception as e:
        return f"Error reading CSV '{filename}': {str(e)}"


if __name__ == "__main__":
    # Test the tools
    print("Testing RAG tools...")
    
    # Test stats
    print("\n=== Document Stats ===")
    print(get_document_stats.invoke({}))
    
    # Test list sources
    print("\n=== Document Sources ===")
    print(list_document_sources.invoke({}))
    
    # Test search
    print("\n=== Search Test ===")
    print(search_documents.invoke({"query": "test"}))
