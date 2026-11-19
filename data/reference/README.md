# data/reference —— 公开参考数据（external reference data）

本目录存放**外部公开数据**，用于对标与交叉检查，不参与效率地图的实测结论。

## 目录

| 路径 | 内容 | 来源与许可 |
| --- | --- | --- |
| `uiuc/apce_10x7_static_pg0811.txt` | APC 10x7E 静态 CT/CP 数据（16 个 RPM 点） | UIUC Propeller Database, Vol.1；科研/教学用途，引用时须注明 UIUC（见文件头注释） |
| `uiuc/apce_11x7_static_kt0534.txt` | APC E 11x7 静态 CT/CP（16 个 RPM 点，1966–6320 r/min） | UIUC Propeller Database, Vol.1；科研/教学用途，引用时须注明 UIUC（见文件头注释） |
| `uiuc/apce_11x8_static_kt0517.txt` | APC E 11x8 静态 CT/CP（16 个 RPM 点，1655–6213 r/min） | UIUC Propeller Database, Vol.1；科研/教学用途，引用时须注明 UIUC（见文件头注释） |
| `uiuc/apcsf_10x7_static_kt0827.txt` | APC Slow Flyer 10x7 静态 CT/CP（16 个 RPM 点，2283–5987 r/min） | UIUC Propeller Database, Vol.1；科研/教学用途，引用时须注明 UIUC（见文件头注释） |
| `uiuc/apcsp_9x6_static_2532rd.txt` | APC Sport 9x6 静态 CT/CP（16 个 RPM 点，2564–6521 r/min） | UIUC Propeller Database, Vol.1；科研/教学用途，引用时须注明 UIUC（见文件头注释） |
| `uiuc/grcp_10x6_static_rd0851.txt` | Graupner CAM 10x6 静态 CT/CP（16 个 RPM 点，1987–6592 r/min） | UIUC Propeller Database, Vol.1；科研/教学用途，引用时须注明 UIUC（见文件头注释） |
| `uiuc/grsn_10x7_static_rd0787.txt` | Graupner Super Nylon 10x7 静态 CT/CP（16 个 RPM 点，1954–6388 r/min） | UIUC Propeller Database, Vol.1；科研/教学用途，引用时须注明 UIUC（见文件头注释） |
| `uiuc/ance_8.5x6_static_2848cm.txt` | Aeronaut Carbon Electric 8.5x6 静态 CT/CP（16 个 RPM 点，2489–6897 r/min） | UIUC Propeller Database, Vol.1；科研/教学用途，引用时须注明 UIUC（见文件头注释） |

## 数据来源

- UIUC Propeller Database（Brandt, Deters, Ananda, Dantsker, Selig）：
  <https://m-selig.ae.illinois.edu/props/propDB.html>
- 完整数据库下载：<https://m-selig.ae.illinois.edu/props/download/UIUC-propDB.zip>
  （md5 `a41e484f1fd0fb6ff80b76e27410808b`）
- Volume 1 数据页：<https://m-selig.ae.illinois.edu/props/volume-1/propDB-volume-1.html>

## 使用约定

1. 引用这些数据时必须注明 UIUC 数据库与相应论文（见文件头）；
2. 仅在科研/教学范围内使用；如需再分发，请先联系 UIUC（`webmaster@illinois.edu`）；
3. 本仓库只镜像**少量样本**用于解析器/对标脚本开发与测试，不镜像完整数据库；
4. 对标结果一律标注 `REFERENCE`，不得把参考数据与本项目合成/实测数据混为一谈。

## 候选数据源（待核查许可证）

| 数据源 | 内容 | 状态 |
| --- | --- | --- |
| UIUC Propeller Database Vols 1–4 | 小型 UAV 桨风洞 CT/CP/效率，静态 + 风速扫描 | **已入库样本**（Vol.1 APC 10x7E 静态） |
| APC 官方性能数据 | 厂商提供，需核查使用条款 | 待核查 |
| NACA/NASA 报告 | 历史桨数据，公有领域较多 | 候选 |
| 其他高校风洞数据集 | 需逐项核查许可证 | 候选 |
