#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.rag import RAGManager

rag = RAGManager()
store = rag.vectorstore
col = store.vectorstore._collection
res = col.get(include=['documents', 'metadatas'])

print(f'Total chunks: {len(res["documents"])}\n')

found_caterpillar = False
for i, (doc, meta) in enumerate(zip(res['documents'], res['metadatas'])):
    if 'caterpillar' in doc.lower():
        found_caterpillar = True
        print(f'=== FOUND Caterpillar in Chunk {i+1} ===')
        print(f'Page: {meta.get("page", "unknown")}')
        print(f'Content:\n{doc[:800]}...\n')

if not found_caterpillar:
    print('❌ Caterpillar NOT FOUND in any chunks!')
    print('\nShowing all chunks:')
    for i, doc in enumerate(res['documents']):
        print(f'\n=== Chunk {i+1} ===')
        print(doc[:400])
        print('...\n')
