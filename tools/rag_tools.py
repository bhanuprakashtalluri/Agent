"""
RAG Tools for LangChain Agent
Provides document search and retrieval capabilities
"""

from pathlib import Path
from typing import Dict, List

import pandas as pd
from langchain.tools import tool

from RAG.vector_store import VectorStoreManager
from .llm_cache import cached_tool


# Initialize vector store (singleton pattern)
_vector_store = None


def get_vector_store() -> VectorStoreManager:
    """Return the singleton :class:`VectorStoreManager` instance."""
    print("\n[get_vector_store] Called")
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager(
            persist_directory="data/vector_db",
            collection_name="documents"
        )
    return _vector_store


@tool
@cached_tool(ttl_seconds=60 * 5, cache_type="rag_search", write_to_query_store=True)
def search_documents(query: str, num_results: int = 3) -> str:
    """Search uploaded documents for content relevant to *query*.

    Args:
        query: Free-form text describing the desired information.
        num_results: Number of snippets to return.

    Returns:
        Markdown string summarizing the best matches or an error message.
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
@cached_tool(ttl_seconds=60 * 30, cache_type="rag_list_sources", write_to_query_store=True)
def list_document_sources() -> str:
    """Return a list of uploaded documents and their types."""
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
            
            sources: Dict[str, str] = {}
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
@cached_tool(ttl_seconds=60 * 5, cache_type="rag_stats", write_to_query_store=True)
def get_document_stats() -> str:
    """Return aggregate statistics for the document vector store."""
    try:
        vs = get_vector_store()
        stats = vs.get_stats()
        output = "Document Database Statistics:\n\n"
        output += f"Collection: {stats.get('collection_name', 'Unknown')}\n"
        output += f"Total chunks: {stats.get('document_count', 0)}\n"
        output += f"Storage: {stats.get('persist_directory', 'Unknown')}\n"
        
        if 'error' in stats:
            output += f"\nError: {stats['error']}"
        
        return output
    
    except Exception as e:
        return f"Error getting stats: {str(e)}"


# Export all RAG tools
rag_tools = [search_documents, list_document_sources, get_document_stats]


@tool
@cached_tool(ttl_seconds=60 * 5, cache_type="read_csv", write_to_query_store=True)
def read_csv(filename: str, preview_rows: int = 20) -> str:
    """Return a tabular preview of a CSV within the allowed directories.

    Args:
        filename: Basename of the CSV relative to the allowed folders.
        preview_rows: Maximum number of rows to include in the preview.

    Returns:
        Markdown table of the preview or an explanatory error message.
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
