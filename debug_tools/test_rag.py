#!/usr/bin/env python3
"""Test RAG search functionality"""

from src.rag import RAGManager

# Initialize RAG
rag = RAGManager()

# Get stats
stats = rag.get_stats()
print("=" * 60)
print("RAG STATS:")
print("=" * 60)
for key, value in stats.items():
    print(f"{key}: {value}")

# Test search for "Satish"
print("\n" + "=" * 60)
print("SEARCHING FOR 'Satish':")
print("=" * 60)
results = rag.search('Satish', k=5)
print(f"\nFound {len(results)} results\n")

for i, doc in enumerate(results, 1):
    print(f"\n--- Result {i} ---")
    print(f"Content: {doc.page_content[:400]}...")
    print(f"Metadata: {doc.metadata}")

# Test search for "resume"
print("\n" + "=" * 60)
print("SEARCHING FOR 'resume skills experience':")
print("=" * 60)
results = rag.search('resume skills experience', k=3)
print(f"\nFound {len(results)} results\n")

for i, doc in enumerate(results, 1):
    print(f"\n--- Result {i} ---")
    print(f"Content: {doc.page_content[:300]}...")
