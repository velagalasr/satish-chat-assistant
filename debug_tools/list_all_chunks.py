#!/usr/bin/env python3
"""List all chunks in ChromaDB"""

from src.rag import RAGManager

# Initialize RAG
rag = RAGManager()

# Get all documents (no query, or use a very generic one)
print("Fetching all indexed chunks...\n")
print("=" * 80)

# Access the vector store directly
if hasattr(rag, 'vector_store') and rag.vector_store:
    # Get collection directly from ChromaDB
    collection = rag.vector_store.vectorstore._collection
    
    # Get all documents
    results = collection.get(include=['documents', 'metadatas'])
    
    print(f"Total chunks: {len(results['documents'])}\n")
    
    for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas']), 1):
        print(f"\n{'='*80}")
        print(f"CHUNK {i}")
        print(f"{'='*80}")
        print(f"Content:\n{doc}\n")
        print(f"Metadata: {metadata}")
        print(f"Length: {len(doc)} characters")
