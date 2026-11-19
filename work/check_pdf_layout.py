# -*- coding: utf-8 -*-
"""PDF 版面自动检查：文本是否越出左右页边距、栏目标题是否齐全、页数统计。"""
import sys
sys.path.insert(0, r'D:\下载\创新\work\pylibs')
import pymupdf

pdf = r'D:\下载\创新\work\render\filled.pdf'
doc = pymupdf.open(pdf)
W, H = doc[0].rect.width, doc[0].rect.height
print('pages:', doc.page_count, 'page size:', round(W, 1), round(H, 1))

# 左 79.4pt、右 521.6pt（页面 595.3 - 73.7）
left_lim, right_lim = 70.0, 535.0
bad = []
all_text = []
for i, page in enumerate(doc):
    words = page.get_text('words')
    for w in words:
        x0, y0, x1, y1 = w[:4]
        if x0 < left_lim or x1 > right_lim:
            bad.append((i + 1, round(x0, 1), round(x1, 1), w[4][:30]))
    all_text.append(page.get_text())
print('out-of-margin words:', len(bad))
for b in bad[:20]:
    print('  ', b)

full = '\n'.join(all_text)
expected = [
    '一、项目简介', '二、项目相关研究现状及发展动态', '三、项目实施的目的、意义',
    '四、项目研究内容和拟解决的关键问题', '五、项目研究与实施的基础条件',
    '六、项目实施方案', '七、项目的技术路线、创新点与项目特色', '八、已有基础',
    '九、项目研究进度安排及预期成果', '十、经费预算', '十一、导师推荐意见',
]
for e in expected:
    print(f'{e}: count={full.count(e)}')
print('total chars (no ws):', len(''.join(full.split())))
