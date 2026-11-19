# -*- coding: utf-8 -*-
"""拼装完整规划 Markdown：part1 + part2(八/九) + 技能清单(第十章) + part2(十一/附录)。"""
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))


def read(name):
    with open(os.path.join(BASE, name), encoding='utf-8') as f:
        return f.read()


def skills_chapter():
    text = read('skills.md')
    lines = text.splitlines()
    # 删除首行大标题
    if lines and lines[0].startswith('# '):
        lines = lines[1:]
    mapping = {
        '## 一、技能地图（总览）': '### 10.1 技能地图（总览）',
        '## 二、通识科研素养（R 类）': '### 10.2 通识科研素养（R 类）',
        '## 三、机械与台架（M 类）': '### 10.3 机械与台架（M 类）',
        '## 四、电气与采集（E 类）': '### 10.4 电气与采集（E 类）',
        '## 五、测试与实验设计（T 类）': '### 10.5 测试与实验设计（T 类）',
        '## 六、建模与优化（O 类）': '### 10.6 建模与优化（O 类）',
        '## 七、软件与工具（S 类）': '### 10.7 软件与工具（S 类）',
        '## 八、三阶段学习路径': '### 10.8 三阶段学习路径',
        '## 九、每周学习安排模板': '### 10.9 每周学习安排模板',
        '## 十、技能自评表（每周更新一次）': '### 10.10 技能自评表（每周更新一次）',
        '## 十一、避坑提醒': '### 10.11 避坑提醒',
    }
    out = ['## 十、技能清单与学习路径（2026 级新生版）', '']
    for line in lines:
        s = line.strip()
        if s in mapping:
            out.append(mapping[s])
        elif s.startswith('### '):
            out.append('#### ' + s[4:])
        else:
            out.append(line)
    return '\n'.join(out)


def main():
    part1 = read('plan_part1.md')
    part2 = read('plan_part2.md')
    marker = '## 十一、'
    idx = part2.index(marker)
    part2_a, part2_b = part2[:idx], part2[idx:]

    skills = skills_chapter()
    full = part1.rstrip() + '\n\n---\n\n' + part2_a.rstrip() + '\n\n---\n\n' + skills.rstrip() + '\n\n---\n\n' + part2_b.rstrip() + '\n'

    # 复选框转可读符号
    full = full.replace('- [ ] ', '- □ ')
    # 修正文档根路径写法（避免被当成 URL 或转义）
    full = full.replace('D:\\下载\\创新', 'D:/下载/创新')

    # 生成章节目录（章节导航，无页码，兼容 docx 与 PDF）
    chapters = [m.group(1) for m in re.finditer(r'^## (.+)$', full, flags=re.M)]
    n_ap = len([c for c in chapters if c.startswith('附录')])
    n_ch = len(chapters) - n_ap
    nav = ['## 目录（章节导航）', '',
           '本规划共 %d 章 + %d 个附录。建议按章节顺序阅读：第 1—2 章为项目定位与技术路线，第 3 章（WBS）是任务细化的核心，'
           '第 4—7 章为环境、进度、分工与数据规范，第 8 章为技术预研结论，第 9 章为风险，第 10 章为技能清单与学习路径，'
           '第 11 章为近两周启动清单，附录为传感器、记录表、参考资料与环境文件。' % (n_ch, n_ap), '']
    nav += ['- ' + c for c in chapters]
    nav = '\n'.join(nav) + '\n\n'
    full = full.replace('## 一、项目定位与目标', nav + '## 一、项目定位与目标', 1)

    out = os.path.join(BASE, 'plan_full.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(full)
    print('saved:', out, 'chars:', len(full))
    # 统计章节
    for m in re.finditer(r'^## (.+)$', full, flags=re.M):
        print('  ', m.group(1))


if __name__ == '__main__':
    main()
