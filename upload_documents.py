"""
Document Upload Utility
Script to add documents to the RAG vector store
"""

import argparse
import sys
from pathlib import Path

from RAG.document_loader import DocumentLoader
from RAG.vector_store import VectorStoreManager


def upload_document(file_path: str, chunk: bool = True):
    """
    Upload a single document to the vector store
    
    Args:
        file_path: Path to the document
        chunk: Whether to split into chunks
    """
    print(f"\n📄 Uploading: {file_path}")
    
    # Initialize loader and vector store
    loader = DocumentLoader()
    vs = VectorStoreManager()
    
    try:
        # Load document
        documents = loader.load_document(file_path)
        print(f"✓ Loaded {len(documents)} document(s)")
        
        # Add to vector store
        ids = vs.add_documents(documents, chunk=chunk)
        print(f"✓ Added to vector store with {len(ids)} chunks")
        
        # Show stats
        stats = vs.get_stats()
        print(f"\n📊 Total documents in database: {stats['document_count']}")
        
        return True
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def upload_directory(directory_path: str, recursive: bool = True, chunk: bool = True):
    """
    Upload all documents from a directory
    
    Args:
        directory_path: Path to directory
        recursive: Search subdirectories
        chunk: Whether to split into chunks
    """
    print(f"\n📁 Uploading documents from: {directory_path}")
    
    # Initialize loader and vector store
    loader = DocumentLoader()
    vs = VectorStoreManager()
    
    try:
        # Load all documents
        documents = loader.load_directory(directory_path, recursive=recursive)
        
        if not documents:
            print("⚠ No supported documents found")
            return False
        
        print(f"\n✓ Loaded {len(documents)} document(s)")
        
        # Add to vector store
        ids = vs.add_documents(documents, chunk=chunk)
        print(f"✓ Added to vector store with {len(ids)} chunks")
        
        # Show stats
        stats = vs.get_stats()
        print(f"\n📊 Total documents in database: {stats['document_count']}")
        
        return True
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def list_documents():
    """List all documents in the vector store"""
    print("\n📚 Documents in Vector Store:")
    
    vs = VectorStoreManager()
    stats = vs.get_stats()
    
    print(f"\nCollection: {stats['collection_name']}")
    print(f"Total chunks: {stats['document_count']}")
    print(f"Storage: {stats['persist_directory']}")
    
    if stats['document_count'] > 0:
        # Try to get sample documents
        try:
            sample = vs.similarity_search("", k=10)
            sources = set()
            for doc in sample:
                sources.add(doc.metadata.get('source', 'Unknown'))
            
            print(f"\nSample sources ({len(sources)}):")
            for source in sorted(sources):
                print(f"  - {source}")
        except Exception as e:
            print(f"\nCouldn't list sources: {e}")


def clear_database():
    """Clear all documents from vector store"""
    print("\n⚠ Warning: This will delete all documents from the vector store!")
    confirm = input("Type 'yes' to confirm: ")
    
    if confirm.lower() == 'yes':
        vs = VectorStoreManager()
        vs.delete_collection()
        print("✓ Database cleared")
    else:
        print("Cancelled")


def main():
    parser = argparse.ArgumentParser(
        description="Upload documents to RAG vector store",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload a single PDF
  python upload_documents.py upload document.pdf
  
  # Upload all documents from a folder
  python upload_documents.py upload-dir RAG/documents/
  
  # List documents in database
  python upload_documents.py list
  
  # Clear database
  python upload_documents.py clear
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Upload single file
    upload_parser = subparsers.add_parser('upload', help='Upload a single document')
    upload_parser.add_argument('file', help='Path to document file')
    upload_parser.add_argument('--no-chunk', action='store_true', help='Don\'t split into chunks')
    
    # Upload directory
    upload_dir_parser = subparsers.add_parser('upload-dir', help='Upload all documents from directory')
    upload_dir_parser.add_argument('directory', help='Path to directory')
    upload_dir_parser.add_argument('--no-recursive', action='store_true', help='Don\'t search subdirectories')
    upload_dir_parser.add_argument('--no-chunk', action='store_true', help='Don\'t split into chunks')
    
    # List documents
    subparsers.add_parser('list', help='List documents in database')
    
    # Clear database
    subparsers.add_parser('clear', help='Clear all documents from database')
    
    # Show supported formats
    subparsers.add_parser('formats', help='Show supported file formats')
    
    args = parser.parse_args()
    
    if args.command == 'upload':
        success = upload_document(args.file, chunk=not args.no_chunk)
        sys.exit(0 if success else 1)
    
    elif args.command == 'upload-dir':
        success = upload_directory(
            args.directory,
            recursive=not args.no_recursive,
            chunk=not args.no_chunk
        )
        sys.exit(0 if success else 1)
    
    elif args.command == 'list':
        list_documents()
    
    elif args.command == 'clear':
        clear_database()
    
    elif args.command == 'formats':
        loader = DocumentLoader()
        print("\n📋 Supported file formats:")
        for ext, desc in loader.SUPPORTED_EXTENSIONS.items():
            print(f"  .{ext:8} - {desc}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
