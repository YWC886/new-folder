# 用户操作指引（一页纸）· User Operations Guide v0.1

> 面向团队与导师：如何恢复备份、推送远端、继续申报与实测。所有命令在项目根目录 `D:\下载\创新` 执行。

## 1. 环境与回归

```powershell
# 解释器（系统默认 python 是 3.15，不能用于本项目）
py -3.12 --version

# 全仓测试（281 项，6 套）
py -3.12 code\tools\run_all_tests.py

# 轮次收尾（清单 + 源码页 + 审计，必须 PASS）
py -3.12 code\tools\round_close.py
```

## 2. 备份与恢复

- 本地发布包：`data/exports/release_r120.zip`（85.3 MiB），SHA256 见同名 `.sha256`；
- 校验：`certutil -hashfile data\exports\release_r120.zip SHA256`；
- 恢复：解压到新目录后用 `py -3.12 code\tools\run_all_tests.py` 验证即可。

## 3. 推送远端（待用户执行一次）

```powershell
git remote -v                 # 当前 origin 仍指向旧地址
git remote set-url origin <你的私有仓库地址>
git push origin main --tags   # 连同 r10…r120 里程碑标签
```

## 4. 申报表后续

1. 在系统「项目成员&指导教师」步骤录入成员姓名/学号（当前缺数据）；
2. 立项依据/经费预算已按 v4 口径准备，可直接复制；
3. 附件 01–04 在 `docs/申报/附件/`（可选上传，需等"上传成功"提示）；
4. 最终提交前请导师审核；导出 Word 修订痕迹需本机 Word。

## 5. 实测启动（M0.4）

1. 按 `docs/test/试验执行SOP_v0.1.md`（含一页速查版）执行双人砝码标定；
2. 生成标定：`py -3.12 code\processing\calibration_fit.py --input <读数.csv> --output data\metadata\calib_MEASURED.json --diameter 0.2544`；
3. 门禁：`py -3.12 code\processing\measured_readiness.py --input <raw.csv> --calib <calib.json>`；
4. 处理/地图：`compute_efficiency.py --require-measured` → `aggregate_efficiency.py` → `gp_surface.py`；
5. 填论文 §4.2 表（规则见论文本身）。

## 6. 常用数据位置

| 内容 | 路径 |
|---|---|
| 申报材料 | `docs/申报/` |
| 规划与答辩 | `docs/规划/` |
| 参考与命名索引 | `docs/参考/` |
| 设计与决策 | `docs/design/`、`docs/decisions.md` |
| 过程数据 | `data/processed/`（CSV/图） |
| Excel/Word 导出 | `data/exports/` |

## 7. 纪律

- 所有数值标注 SIM / REFERENCE / MEASURED，模拟/参考不得写成实测；
- 提交前 `round_close.py` 必须 PASS（审计 HARD=0）；
- 代码只用 `py -3.12`；含中文的 .ps1 用 `pwsh` 或 `Invoke-Expression (Get-Content -Raw -Encoding UTF8 ...)`。
