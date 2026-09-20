# Chirp Communication Library

> English README: [README.md](README.md)

基于线性调频（chirp）的**声波通信** Python 库：将短文本编码为可听 chirp 信号，通过扬声器发送、麦克风接收并解码。

**版本**：0.3

---

## 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [生成测试音频](#生成测试音频)
- [实时发送](#实时发送)
- [实时监听](#实时监听)
- [录制与解码](#录制与解码)
- [分析音频样本](#分析音频样本)
- [配置参数](#配置参数)
- [项目结构](#项目结构)

---

## 安装

```bash
git clone https://github.com/WallyHao/chirp-comm.git
cd chirp_comm
pip install -r requirements.txt
pip install -e .
```

**依赖**：`numpy`、`scipy`、`sounddevice`（Python 3.8+）

---

## 快速开始

### 1. 生成测试音频

```bash
# 生成所有测试样本（包括各种噪声和干扰）
python examples/generate_to_file.py

# 仅生成纯净信号
python examples/generate_to_file.py --clean

# 指定编码内容
python examples/generate_to_file.py --text "TEST"
```

所有生成的音频文件保存在 `samples/` 目录下：

| 文件名 | 说明 |
|--------|------|
| `01_clean.wav` | 纯净信号 |
| `02_gaussian_snr*.wav` | 高斯白噪声 (SNR 5/10/15/20 dB) |
| `03_pink_noise.wav` | 粉红噪声 |
| `04_hum_*hz.wav` | 交流电哼声 (50/100 Hz) |
| `05_burst_noise.wav` | 突发噪声 |
| `06_dropout.wav` | 信号丢失 |
| `07_volume_*.wav` | 不同音量 (10/30/50%) |
| `08_doppler_*.wav` | 多普勒频移 |
| `09_reverb.wav` | 混响效果 |
| `10_clicks.wav` | 脉冲噪声 |
| `11_combined.wav` | 组合干扰 |

### 2. 实时发送

```bash
# 发送默认消息 "ab"
python examples/transmit_live.py

# 发送自定义消息
python examples/transmit_live.py "HELLO"

# 循环发送
python examples/transmit_live.py "TEST" --loop
```

### 3. 实时监听

```bash
# 启动监听，解码到的消息会实时打印
python examples/automated_command_trigger.py
```

可用命令：

| 命令 | 动作 |
|------|------|
| `LIGHT_ON` | 开灯 |
| `LIGHT_OFF` | 关灯 |
| `FAN_ON` | 开风扇 |
| `FAN_OFF` | 关风扇 |
| `LOCK` | 锁门 |
| `UNLOCK` | 解锁 |
| `ALARM` | 触发警报 |
| `SILENT` | 静音模式 |

### 4. 录制与解码

```bash
# 录制并分析
python examples/record_and_decode.py

# 录制时长（默认 8 秒）
python examples/record_and_decode.py --duration 5

# 播放指定音频文件
python examples/record_and_decode.py --play samples/01_clean.wav

# 录制并保存
python examples/record_and_decode.py --save recorded.wav
```

### 5. 分析音频样本

```bash
# 分析 samples/ 目录下的所有音频
python examples/analyze_signal.py

# 分析指定文件
python examples/analyze_signal.py samples/01_clean.wav

# 分析指定目录
python examples/analyze_signal.py /path/to/audio/
```

分析结果包含：

- **RMS**: 信号均方根值
- **Peak**: 峰值幅度
- **Sync**: 同步信号检测结果
- **Bits**: 提取的比特数
- **Errors**: 误码数
- **Decoded**: 解码结果

---

## 配置参数

核心参数位于 `chirp_comm/config.py`：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `FS` | 48000 | 采样率 (Hz) |
| `SYNC_F0` | 2000 | 同步信号起始频率 (Hz) |
| `SYNC_F1` | 4000 | 同步信号结束频率 (Hz) |
| `BIT_F0` | 2000 | 数据信号起始频率 (Hz) |
| `BIT_F1` | 4000 | 数据信号结束频率 (Hz) |
| `SYNC_DUR` | 0.15 | 同步信号时长 (s) |
| `BIT_DUR` | 0.05 | 每 bit 时长 (s) |
| `PAUSE` | 0.01 | bit 间停顿 (s) |

**预计传输时间**：46 bits × (0.05 + 0.01)s ≈ 2.9 秒

---

## 项目结构

```
communicate-chirp/
├── chirp_comm/           # 核心库
│   ├── __init__.py       # 导出主要接口
│   ├── config.py         # 配置参数
│   ├── dsp.py            # DSP 信号处理
│   ├── protocol.py       # 编码/解码协议
│   ├── packet.py         # 数据包定义
│   ├── engine.py          # 收发引擎
│   ├── audio_io.py       # 音频输入输出
│   └── diagnostics.py    # 诊断工具
├── examples/
│   ├── generate_to_file.py        # 生成测试样本
│   ├── analyze_signal.py          # 分析音频信号
│   ├── record_and_decode.py       # 录制并解码
│   ├── transmit_live.py           # 实时发送
│   └── automated_command_trigger.py  # 智能家居示例
├── samples/              # 生成的测试音频
├── requirements.txt
└── README.md
```

---

## 技术特性

- **Hamming(7,4) 纠错**：每 4 位数据编码为 7 位，可纠正单比特错误
- **动态位跟踪**：根据相关峰值位置动态调整解码窗口，抗多普勒频移
- **Hanning 窗**：chirp 信号使用淡入淡出，减少频谱泄露
- **自适应阈值**：基于噪声水平动态调整检测阈值

---

## License

按项目仓库约定使用。
