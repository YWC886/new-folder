# 会话记忆交接 · MemoryPrimer v1.2（2026-11-22）

> 新会话/新成员接手先读这一份，再按 §8 开场清单操作。上一版：`会话记忆交接_MemoryPrimer_v1.1.md`。

## 1. 一句话状态

大创「多旋翼 UAV 电机—螺旋桨—电调系统效率地图」：软件原型与论文骨架已完成，v5 治理闭环（一致性审计 + round_close 门禁）；当前处于**深化阶段**（几何代理/不确定度传播/DoE 闭环/材料同步），实机 M0.4 尚未开始。

## 2. 仓库与版本基线

| 项 | 值 |
|---|---|
| HEAD | `a0524bd`（R28 文档口径，工作树干净） |
| 远端 | `https://github.com/YWC886/new-folder.git`（origin 停在 `8e99fc5`，**6 个提交待推**） |
| 待推 | `76f26ca` `6eba2d2` `da38265` `8b2f812` `d12a255` `a0524bd` |
| 测试 | **320 项 / 6 套**（acq 5 / proc 98+ / sim 29 / sel 66 / ref 81 / tools 35） |
| 复现包清单 | **262 文件**，`files: 262 missing: [] mismatch: 0` |
| 源代码页 | **88 源文件 / 17,818 行 / 357 页** |
| 里程碑 tag | r10/r21/r27/r30/r40/r50/r60/r90/r100/r110/r120 |

## 3. 环境铁律（踩过的坑）

- Python 必须用 `py -3.12`（`python` 指向 3.15，pylibs 为 cp312）；
- 第三方库在 `work/pylibs`，脚本内 `sys.path.insert(.../work/pylibs)`；matplotlib 用 Agg、中文字体 `Microsoft YaHei`；
- PowerShell 执行策略 Restricted：运行 .ps1 用 `Invoke-Expression (Get-Content -Raw -Encoding UTF8 ...)`；含中文 .ps1 必须 UTF-8；
- 控制台编码：跑测试/清单前设 `$env:PYTHONIOENCODING='utf-8'`；
- Word/PDF 文件被占用会导致导出/改名失败：先关闭对应窗口；`~$*` 锁文件在 .gitignore；
- GitHub push 间歇失败（`Connection reset`/`connect timeout`）：网络恢复后重试即可；
- 提交前必须 `py -3.12 code/tools/round_close.py`（manifest → check_release → 审计），全绿再 commit。

## 4. 代码资产（顶层）

| 子系统 | 关键入口 |
|---|---|
| 采集 | `code/acquisition/acquire.py`、`validate.py` |
| 处理 | `compute_efficiency.py`、`aggregate_efficiency.py`、`plot_efficiency_map.py`、`gp_surface.py`、`calibration_fit.py`、`measured_readiness.py`、`design_matrix.py`、`uncertainty.py`、`uq_utils.py` |
| 仿真 | `propulsion_model.py`、`simulate_campaign.py`、`transient_thermal.py`、`two_node_thermal.py` |
| 选型 | `match_propulsion.py`、`gp_match.py`、`multiobjective.py`、`bo_suggest.py`、`uq_annotate.py`、`allocation_demo.py` |
| 参考 | `uiuc_propdb.py`、`catalog_uiuc.py`、`calibrate_uiuc.py`、`bootstrap_priors.py`、`geometry_prior.py`、`bem_propeller.py`、`bem_geometry_multiprop.py`、`bem_lopo_transfer.py` |
| 工具 | `source_pages.py`、`build_manifest.py`、`check_release.py`、`round_close.py`、`run_all_tests.py`、`export_office.py`、`release_package.py`、`audit_consistency.py`、`md2docx.py` 等 |

## 5. 关键决策速查（详见 `docs/decisions.md`）

- D012 效率口径（η_em=P_shaft/P_elec，η_sys=FM·η_em，禁 T/P 简化）；
- D023 参考数据纪律（UIUC 只镜像小样本、REFERENCE 不作实验验证）；
- D031/D033/D034 REFERENCE 派生先验（do_not_apply、bootstrap≠U）；D049/D054/D055 BEM 诊断用、不作预测；
- D032 静态标定工具（仅真实读数、simulated:false、R²≥0.9995、重复性/迟滞≤0.5% FS）；
- D035–D038 MEASURED 门禁与三入口守门；D043 排程；D045 推力反解；
- **D056 不确定度统一口径**：u_meas=U/2、σ_total=sqrt(u_meas²+σ_model²)、η_cons=η−kσ_total（k=2 呈现），禁直接相加/bootstrap 冒充 U。

## 6. 目标与轮次

- 旧治理目标 `goal-d3258191…`：已完成（R124）。
- 深化目标 `goal-feedf8e7-296b-427e-afa4-70de03ae6dfb`：active，max 240，**R28 完成**；四线：①几何/Re 代理（已有负结果+诊断）②UQ 传播（已完成链路）③DoE/选型闭环 ④论文/材料同步。
- 自动化模式：goal_round 驱动，每轮产出可复核产物 + 测试 + round_close + commit；用户「暂停」才停。

## 7. 未完成事项

1. **git push**：6 个提交待推（见 §2）；
2. **Hindsight API token**：配置文件已建（`C:\Users\35509\.hindsight\coding-agent.json`），但用户给的 UUID 格式被 401 拒绝，待提供正式 token；
3. **申报表**：第 1 步+预算已暂存；第 2–5 步（成员姓名学号、指导教师、立项依据、附件）待成员信息；v3/v4 修订痕迹/PDF 需 Word 可用；
4. **硬件 M0.4**：采购→台架→双人砝码标定→MEASURED 首采（见 `docs/inputs/M0.4启动包_M0.4KickoffPack_v0.1.md` 与 SOP）；
5. **计数/导出**：Office 导出与部分文档计数需在每轮 round_close 前重建（build_manifest 已覆盖清单，导出需 `export_office.py` 重跑）。

## 8. 新会话开场清单

1. 读本文件 + 根 `README.md` + `docs/plan/项目待办与决策清单_TODOandDecisions_v0.1.md`；
2. `git log -1 --format='%h %s'`、`git status --porcelain`，确认 HEAD 与工作树；
3. `py -3.12 code/tools/round_close.py` 确认全绿（网络无关）；
4. 若远端落后，`git push origin main`；
5. 从「未完成事项」挑一项继续，或跑 goal_round 继续深化。
