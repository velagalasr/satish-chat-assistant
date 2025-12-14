#!/usr/bin/env python3
"""Test RAG search for Caterpillar"""

from src.rag import RAGManager

# Initialize RAG
rag = RAGManager()

# Test different search queries
queries = [
    "Caterpillar",
    "Satish Caterpillar",
    "work experience Caterpillar",
    "Satish work experience employment",
    "professional experience"
]

for query in queries:
    print("\n" + "=" * 60)
    print(f"SEARCHING FOR: '{query}'")
    print("=" * 60)
    results = rag.search(query, k=3)
    print(f"Found {len(results)} results\n")
    
    for i, doc in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Content:\n{doc.page_content[:500]}\n")
        print(f"Source: {doc.metadata.get('source', 'unknown')}")
        print(f"Page: {doc.metadata.get('page', 'unknown')}")
