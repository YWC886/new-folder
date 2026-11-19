# 最小采集链路与数据字典 v0.1

> 状态：软件模拟链路已可用；**实机串口、ADS1256 接线和砝码标定尚待硬件验证**。本目录不保存任何虚构的实机结论。
>
> 对应第一阶段 M0.4：拉压力传感器 → 24 bit ADC → 串口 → CSV。当前程序先统一串口协议、原始数据格式和质量检查，后续固件只需按协议输出即可。

## 1. 文件与目录

| 路径 | 用途 |
| --- | --- |
| `code/acquisition/acquire.py` | 模拟或实机串口采集，写原始 CSV 与元数据 |
| `code/acquisition/validate.py` | 只读检查结构、序号、时间、样本率、缺失值和稳态波动 |
| `code/acquisition/test_acquisition.py` | 无硬件回归测试 |
| `data/raw/` | 原始 CSV 与同名 `.meta.json`，只增不改、禁止覆盖 |
| `data/processed/` | 后续清洗和效率计算结果，必须由脚本生成 |
| `data/metadata/` | 校验报告、标定记录、测试记录与数据字典 |

## 2. 快速运行

在项目根目录执行以下 PowerShell 命令。

### 2.1 无硬件模拟

```powershell
python code\acquisition\acquire.py --mode simulate --run-id 20261117_SIM_22V2_50pct_R1 --duration 5 --sample-rate 1000 --operator "模拟联调" --combo DEMO --voltage-set 22.2 --throttle-set 50 --repeat R1 --prop-diameter-m 0.4572
python code\acquisition\validate.py --input data\raw\20261117_SIM_22V2_50pct_R1.csv --window 3 --min-sample-rate 990 --output data\metadata\20261117_SIM_22V2_50pct_R1.validation.json
```

模拟数据固定随机种子，可复现；文件名含 `SIM`，元数据中 `simulated=true`，不得用于效率结论或申报书实测结果。

### 2.2 自动化测试

```powershell
python -m unittest discover -s code\acquisition -p "test_*.py" -v
```

### 2.3 实机串口采集

```powershell
python code\acquisition\acquire.py --mode serial --port COM5 --baud 115200 --duration 10 --run-id 20261127_M1P1_22V2_50pct_R1 --operator "成员B+成员C" --combo M1P1 --motor "待冻结型号" --esc "待冻结型号" --prop "待冻结规格" --voltage-set 22.2 --throttle-set 50 --repeat R1 --prop-diameter-m 0.4572
python code\acquisition\validate.py --input data\raw\20261127_M1P1_22V2_50pct_R1.csv --window 3 --min-sample-rate 990 --output data\metadata\20261127_M1P1_22V2_50pct_R1.validation.json
```

- 将 `COM5` 换成设备管理器中的实际串口；固件与电脑均设为 115200 baud、8N1。
- `--duration` 到时停止。串口坏帧、非 UTF-8 数据或零有效样本会明确报错；已写入的原始 CSV 保留，元数据标记 `interrupted`，不得当作完整试验。
- 电机、桨、电调型号未冻结前保留“待冻结”字样，不得编造。

## 3. 串口协议 v0.1

固件上电后可先输出一次表头，之后每行一帧；允许空行和以 `#` 开头的调试注释，不得夹杂其他日志。

```text
seq,device_time_ms,thrust_raw,torque_raw,rpm,voltage_v,current_a,motor_temp_c,ambient_temp_c,humidity_pct,pressure_kpa
0,0,28000.0,17000.0,6000.0,22.200,8.000,35.0,24.0,45.0,96.0
```

- 每帧固定 11 列，UTF-8 编码，换行结束。
- `seq`、`device_time_ms`、`thrust_raw` 必填；未接入的通道留空，不填 0 冒充测量。
- `seq` 从 0 连续递增；`device_time_ms` 为设备上电后的非负毫秒时间戳。
- 力与扭矩先保留 ADC 原始计数，标定后在处理脚本中换算，禁止直接覆盖原始值。

## 4. 原始 CSV 数据字典 v0.1

| 字段 | 类型 | 单位 | 必填 | 含义 |
| --- | --- | --- | --- | --- |
| `host_ts` | ISO8601 字符串 | — | 是 | 电脑接收时间，含时区 |
| `elapsed_s` | 浮点 | s | 是 | 本次采集开始后的电脑端相对时间 |
| `seq` | 非负整数 | — | 是 | 设备帧序号，用于发现丢帧 |
| `device_time_ms` | 非负整数 | ms | 是 | 设备时间戳，用于估计样本率 |
| `thrust_raw` | 浮点 | ADC count | 是 | 推力桥式传感器 ADC 原始值 |
| `torque_raw` | 浮点 | ADC count | 否 | 反扭矩传感器 ADC 原始值 |
| `rpm` | 浮点 | r/min | 否 | 转速；未接入时留空 |
| `voltage_v` | 浮点 | V | 否 | 母线电压瞬时值 |
| `current_a` | 浮点 | A | 否 | 母线电流瞬时值 |
| `motor_temp_c` | 浮点 | °C | 否 | 电机温度 |
| `ambient_temp_c` | 浮点 | °C | 否 | 环境温度 |
| `humidity_pct` | 浮点 | %RH | 否 | 相对湿度 |
| `pressure_kpa` | 浮点 | kPa | 否 | 大气压 |

### 同名 `.meta.json` 元数据

| 字段组 | 记录内容 |
| --- | --- |
| 数据身份 | `run_id`、`schema_version`、`status`、`mode`、`simulated`、数据声明 |
| 时间 | 开始/结束时间、电脑端时长、写入行数 |
| 接口 | 串口、波特率、8N1；模拟模式的随机种子与样本率 |
| 试验条件 | 操作人、组合、电机、电调、桨、目标电压、目标油门、重复编号、实测桨径、备注 |
| 异常 | 中断类型与错误信息；正常完成为 `null` |

文件命名推荐：`日期_组合_电压_油门_重复.csv`，例如 `20261127_M1P1_22V2_50pct_R1.csv`。`run_id` 仅允许字母、数字、点、下划线和连字符，程序自动替换其他字符。

## 5. 校验规则与结果解释

| 检查 | 错误（`fail`） | 警告（`pass_with_warnings`） |
| --- | --- | --- |
| 表头与数据行 | 表头不符、无数据、必填项为空、非有限数值 | — |
| 序号与时间 | 序号重复/缺号、设备时间倒退、时间格式错误 | — |
| 样本率 | 指定下限后，估计样本率低于下限 | — |
| 通道完整性 | — | 可选通道全缺失、元数据缺失或不可读 |
| 末尾稳态窗口 | — | `thrust_raw` 或 `rpm` 相对标准差 >1% |

`pass` 只表示软件规则通过，**不等于传感器已标定、数据物理正确或试验安全合格**。JSON 报告应放入 `data/metadata/`，原始 CSV 始终保持不变。

## 6. 硬件接入与砝码验证待办

1. 固件按协议输出，先验证单通道 `thrust_raw`，再接入扭矩、转速和电参量。
2. 用 ADS1256/ADS1232 进行正式采集；HX711 仅用于原理验证，不输出正式效率数据。
3. 双人完成零点与砝码加载/卸载记录，另存标定系数；标定前不得把 ADC count 换算结果称为实测推力。
4. 静态验证需记录砝码等级、质量、当地重力加速度依据、加载点、重复次数、零点和迟滞。
5. 上电试转前另按项目 SOP 检查防护罩、急停、桨叶、紧固与双人到场；本模拟程序不能替代安全检查。
