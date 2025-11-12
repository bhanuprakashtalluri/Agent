"""
Vector Store Manager using ChromaDB
Handles document storage, retrieval, and similarity search
"""

import os
from typing import List, Optional
from pathlib import Path

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .embeddings_config import get_default_embeddings


class VectorStoreManager:
    """Manages vector store operations for RAG"""
    
    def __init__(
        self, 
        persist_directory: str = "data/vector_db",
        collection_name: str = "documents",
        embeddings_model=None
    ):
        """
        Initialize vector store manager
        
        Args:
            persist_directory: Where to store the vector database
            collection_name: Name of the collection
            embeddings_model: Embeddings model (default: HuggingFace)
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Create directory if doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Use default embeddings if none provided
        self.embeddings = embeddings_model or get_default_embeddings()
        
        # Initialize or load vector store
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )
        
        # Text splitter for chunking large documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def add_documents(self, documents: List[Document], chunk: bool = True) -> List[str]:
        """
        Add documents to vector store
        
        Args:
            documents: List of Document objects
            chunk: Whether to split documents into chunks
            
        Returns:
            List of document IDs
        """
        if chunk:
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            print(f"Split {len(documents)} documents into {len(chunks)} chunks")
        else:
            chunks = documents
        
        # Add to vector store
        ids = self.vectorstore.add_documents(chunks)
        
        print(f"✓ Added {len(chunks)} document chunks to vector store")
        
        return ids
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 4,
        filter_dict: Optional[dict] = None
    ) -> List[Document]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Metadata filter (e.g., {'type': 'pdf'})
            
        Returns:
            List of most similar documents
        """
        results = self.vectorstore.similarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )
        
        return results
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[dict] = None
    ) -> List[tuple[Document, float]]:
        """
        Search with relevance scores
        
        Args:
            query: Search query
            k: Number of results
            filter_dict: Metadata filter
            
        Returns:
            List of (document, score) tuples
        """
        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict
        )
        
        return results
    
    def as_retriever(self, search_kwargs: Optional[dict] = None):
        """
        Get a retriever interface for LangChain
        
        Args:
            search_kwargs: Arguments for similarity search
            
        Returns:
            Retriever object
        """
        if search_kwargs is None:
            search_kwargs = {"k": 4}
        
        return self.vectorstore.as_retriever(
            search_kwargs=search_kwargs
        )
    
    def delete_collection(self):
        """Delete the entire collection"""
        self.vectorstore.delete_collection()
        print(f"✓ Deleted collection: {self.collection_name}")
    
    def get_stats(self) -> dict:
        """
        Get statistics about the vector store
        
        Returns:
            Dictionary with stats
        """
        try:
            # Get collection
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'persist_directory': self.persist_directory
            }
        except Exception as e:
            return {
                'error': str(e),
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory
            }
    
    def search_by_metadata(self, metadata_filter: dict, k: int = 10) -> List[Document]:
        """
        Search documents by metadata only
        
        Args:
            metadata_filter: Filter dict (e.g., {'type': 'pdf'})
            k: Number of results
            
        Returns:
            List of matching documents
        """
        # Get all documents and filter by metadata
        # Note: This is a simple implementation
        # For production, you'd want a more efficient approach
        results = self.vectorstore.similarity_search(
            query="",  # Empty query
            k=k,
            filter=metadata_filter
        )
        
        return results


def create_or_load_vectorstore(
    persist_directory: str = "data/vector_db",
    collection_name: str = "documents"
) -> VectorStoreManager:
    """
    Convenience function to create or load a vector store
    
    Args:
        persist_directory: Storage directory
        collection_name: Collection name
        
    Returns:
        VectorStoreManager instance
    """
    return VectorStoreManager(
        persist_directory=persist_directory,
        collection_name=collection_name
    )


if __name__ == "__main__":
    # Test vector store
    print("Testing Vector Store...")
    
    vs = VectorStoreManager()
    
    # Test document
    test_docs = [
        Document(
            page_content="Python is a great programming language for data science.",
            metadata={'source': 'test.txt', 'type': 'txt'}
        ),
        Document(
            page_content="Machine learning is a subset of artificial intelligence.",
            metadata={'source': 'test2.txt', 'type': 'txt'}
        )
    ]
    
    # Add documents
    vs.add_documents(test_docs)
    
    # Search
    results = vs.similarity_search("programming language", k=2)
    print(f"\nSearch results: {len(results)}")
    for doc in results:
        print(f"- {doc.page_content[:100]}...")
    
    # Get stats
    stats = vs.get_stats()
    print(f"\nVector Store Stats: {stats}")
