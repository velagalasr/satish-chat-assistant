#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract text from the PDF to see what's in it"""

import sys
from pypdf import PdfReader

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pdf_path = "data/documents/SatishVelagala Resume.pdf"

print(f"Reading PDF: {pdf_path}\n")
print("=" * 80)

reader = PdfReader(pdf_path)
print(f"Total pages: {len(reader.pages)}\n")

for i, page in enumerate(reader.pages):
    text = page.extract_text()
    print(f"\n{'='*80}")
    print(f"PAGE {i+1}")
    print(f"{'='*80}")
    print(text)
    print(f"\nPage {i+1} length: {len(text)} characters")
    
    # Check for Caterpillar
    if "caterpillar" in text.lower():
        print("✅ FOUND 'Caterpillar' on this page!")
