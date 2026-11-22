# 下一阶段行动清单 _NextActions_v0.1

> 生成于 r91（2026-11-22），承接 r90 里程碑。
> 原则：先清用户侧阻塞，再做自动化可推进项；每项注明验收证据。

## A. 用户侧阻塞（需人操作）

| # | 事项 | 所需 | 验收 |
|---|---|---|---|
| A1 | 申报表第 2–5 步（成员/指导教师/立项依据/附件） | 成员姓名、学号、负责人 | 系统显示「学生暂存项目」更新，附件上传成功 |
| A2 | v3 申报表修订痕迹与 PDF | 本机关闭占用的 Word | `申报表-修改版_v3草稿_修订痕迹.docx` + PDF |
| A3 | 根目录重复 `附件3…_已填写.docx` 清理 | 关闭 Word | 根目录仅剩 README/.gitignore |
| A4 | origin 推送（可选） | 远端凭据 | `git push` 后 origin/main 更新 |

## B. 自动化可推进（按优先级）

| # | 事项 | 产出 | 验收 |
|---|---|---|---|
| B1 | 第八九部分批注 C26–C29 修订 | 修订 docx + 改动说明追加 | 批注逐条映射；round_close PASS |
| B2 | 开题答辩 PPT 并入要点页 | `开题答辩PPT_v0.2.pptx` | 页数/图注正确；present |
| B3 | 双语命名扩批（剩余 docs 交付物） | 重命名 + 引用同步 | 无断链（grep 旧名 0 命中） |
| B4 | 源码页计数同步 | 67+ 文件计数一致 | `check_release` 全绿 |

## C. 实机条件到位后（依赖 A1/采购）

1. M0.4 最小采集链路 + 双人 M1 砝码标定 → 第一份实测标定；
2. MEASURED 通路全链路重跑（readiness → compute → aggregate → 地图 v1.0）；
3. 用实测数据替换论文占位表与答辩材料中的 SIM 数字。

## D. 每轮收尾固定动作

```powershell
py -3.12 code\tools\source_pages.py --overwrite   # 代码增删后
py -3.12 code\tools\round_close.py               # 清单重建 + preflight
# PASS 后 git add -A / commit
```
