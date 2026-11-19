# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, r'D:\下载\创新\work\pylibs')
import pymupdf

pdf = r'D:\下载\创新\work\render\filled.pdf'
out = r'D:\下载\创新\work\render'
doc = pymupdf.open(pdf)
print('pages', doc.page_count, 'size', doc[0].rect)
for i, page in enumerate(doc):
    txt = page.get_text().replace('\n', ' ')
    print(f'--- p{i+1}: {txt[:90]}')
    pix = page.get_pixmap(dpi=110)
    pix.save(os.path.join(out, f'p{i+1:02d}.png'))
print('done')
