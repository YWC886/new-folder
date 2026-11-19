# -*- coding: utf-8 -*-
"""Extract text from the application PDF."""
import sys, io
sys.path.insert(0, r'D:\下载\创新\work\pylibs')
from pypdf import PdfReader

src = sys.argv[1]
dst = sys.argv[2]
out = io.open(dst, 'w', encoding='utf-8')
reader = PdfReader(src)
print("pages:", len(reader.pages), file=out)
meta = reader.metadata
if meta:
    print("metadata:", dict(meta), file=out)
for i, page in enumerate(reader.pages):
    print(f"\n===== PAGE {i+1} =====", file=out)
    try:
        txt = page.extract_text() or ''
    except Exception as e:
        txt = f"<<extract error: {e}>>"
    print(txt, file=out)
out.close()
print("done")
