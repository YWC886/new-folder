# -*- coding: utf-8 -*-
"""把 PDF 渲染为 PNG 并做越界/页数检查。

用法：python render_plan.py <pdf> <outdir> [dpi]
输出：每页 PNG + 页数、每页首 90 字、越界文本框统计。
"""
import os
import sys

import fitz


def main(argv):
    pdf = argv[1]
    outdir = argv[2]
    dpi = int(argv[3]) if len(argv) > 3 else 110
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf)
    print('pages:', doc.page_count)
    problems = 0
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        png = os.path.join(outdir, f'p{i + 1:02d}.png')
        pix.save(png)
        text = page.get_text().replace('\n', ' ')
        head = text[:90]
        # 越界检查：文本块超出左右安全边距（A4 595x842pt，边距按 55pt 计）
        W, H = page.rect.width, page.rect.height
        bad = 0
        for b in page.get_text('blocks'):
            x0, y0, x1, y1 = b[:4]
            if x0 < 40 or x1 > W - 40:
                bad += 1
        problems += bad
        flag = f'  [越界块 {bad}]' if bad else ''
        print(f'p{i + 1:02d} ({len(text)}字){flag}: {head}')
    print('total overflow blocks:', problems)


if __name__ == '__main__':
    main(sys.argv)
