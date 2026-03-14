# chirp_comm

基于线性调频（chirp）的**声波通信** Python 库：将短文本编码为可听 chirp 信号，通过扬声器发送、麦克风接收并解码。采用 `sounddevice` 做实时采集与播放，发送/接收均为非阻塞、线程化设计；内置 **Hamming(7,4) 纠错**与**动态位跟踪**，针对移动场景下的多普勒频移与时间漂移做了鲁棒性增强。

**版本**：0.2

---

## 特点

- **即插即用**：`ChirpSender` / `ChirpReceiver` 两个类，`send(text)` 与回调或 `get_messages()` 即可完成收发
- **非阻塞**：发送端用队列 + 后台线程播放；接收端用 `InputStream` 回调，不阻塞主程序
- **纠错与鲁棒**：每 4 位数据编码为 7 位汉明码，可纠正单比特错误；接收端动态位跟踪可抵消多普勒/时漂
- **可配置**：物理层参数（采样率、频率、时长）集中在 `config.py`，便于调比特率与鲁棒性
- **设备可选**：构造时传入 `device` 或通过 `list_devices()` 查看/选择麦克风与扬声器

---

## 安装

```bash
git clone <repo_url>
cd communicate-chirp
pip install -r requirements.txt
pip install -e .
```

**依赖**：`numpy`、`scipy`、`sounddevice`（Python 3.8+）。安装后可通过 `pip show chirp_comm` 查看版本（当前为 0.2）。

---

## 快速开始

**发送端**（在一个终端）：

```bash
python examples/send_demo.py
# 按提示输入 4 个字符，将通过默认扬声器发送
```

**接收端**（在另一个终端）：

```bash
python examples/recv_demo.py
# 使用默认麦克风监听，解码到的消息会打印并可通过 get_messages() 拉取
```

发送端输入 4 个字符并回车后，接收端应打印出相同内容（如 `Real-time: HELO`）。  
**消息格式**：仅支持 **4 个 ASCII 字符**；不足会自动右补空格，超出会截断。

---

## API 概览

### ChirpSender

| 方法 / 属性 | 说明 |
|-------------|------|
| `ChirpSender(device=None)` | 使用默认播放设备；`device` 可为设备索引或名称 |
| `send(text)` | 将字符串编码为 chirp 并加入播放队列（非阻塞） |
| `stop()` | 停止后台播放线程 |
| `list_devices()` | 静态方法，列出所有音频设备 |

### ChirpReceiver

| 方法 / 属性 | 说明 |
|-------------|------|
| `ChirpReceiver(device=None, callback=None)` | 使用默认麦克风；`callback(msg)` 在每解出一条消息时被调用 |
| `start()` | 开始录音与解码 |
| `stop()` | 停止录音并关闭流 |
| `get_messages()` | 取出当前已解码消息列表并清空内部缓存 |
| `list_devices()` | 静态方法，列出所有音频设备 |

### 使用示例

```python
from chirp_comm import ChirpSender, ChirpReceiver

# 发送
sender = ChirpSender()
sender.send("HELO")
sender.stop()

# 接收（回调 + 轮询拉取）
def on_msg(msg):
    print("Got:", msg)

receiver = ChirpReceiver(callback=on_msg)
receiver.start()
# ... 稍后 ...
msgs = receiver.get_messages()
receiver.stop()
```

---

## 物理层与协议简述

- **采样率**：48 kHz（在 `chirp_comm/config.py` 中可改）
- **同步**：一段 0.2 s、1 kHz→6 kHz 的线性 chirp，用于检测消息起点；前后各 0.4 s 静音，同步后 0.05 s 静音
- **数据**：每 bit 用 0.02 s 的 chirp 表示——上升 chirp（2→5 kHz）= 1，下降 chirp（5→2 kHz）= 0，后跟 0.015 s 静音（`BIT_DUR + PAUSE` 决定每比特占用的采样数）
- **消息长度**：固定 4 个 ASCII 字符；每字符 8 bit 经 **Hamming(7,4)** 编码为 2×7=14 bit，故每帧 **56 bit**（4×14），有效载荷 32 bit，编码后约 16 bps 量级

参数集中定义在 `chirp_comm/config.py`，修改后可调节比特率与抗噪折中。

---

## 技术说明（鲁棒性设计）

### Hamming(7,4) 纠错

- 每 4 位原始数据映射为 7 位编码，可**自动纠正**该 7 位中任意 **1 位**翻转错误
- 编码/解码在 `chirp_comm/dsp.py` 中实现：`_hamming_74_encode`、`_hamming_74_decode`；对外接口为 `text_to_bits_fec` / `bits_to_text_fec`
- 适合信道偶发比特错误（噪声、多径等），在移动或嘈杂环境下提高解码成功率

### 动态位跟踪（Dynamic Bit Tracking）

- 接收端**不再按固定步进**取每比特段，而是在预期位置**前后约 ±15%** 的窗口内做与参考 chirp 的互相关，根据**峰值位置**判定 0/1，并**用该峰值位置更新下一比特的起始指针**
- 可抵消因收发相对运动导致的**时间拉伸/压缩**（多普勒漂移、采样偏差），减少漏 bit 或错位导致的整帧失败

### 窗函数与相关检测

- Chirp 生成时使用 **Hanning 窗**（`np.hanning`）做淡入淡出，减少频谱泄露，提高在噪声与频偏下的相关峰质量
- 同步检测使用与 `REF_SYNC` 的互相关，阈值在 `receiver.py` 中可调（如 `max_val > 8.0`）

---

## 抗多普勒与可调参数

收发端相对运动会产生多普勒频移（Δf ∝ 载频 × 相对速度）。本库已通过**动态位跟踪**和**汉明纠错**增强鲁棒性；若需进一步优化，可参考下表（参数均在 `chirp_comm/config.py` 或 `receiver.py`）：

| 调整 | 作用 | 代价 |
|------|------|------|
| **增大 `SYNC_DUR`**（如 0.25～0.3 s） | 同步 chirp 更长，相关对频偏更不敏感 | 每帧略长 |
| **增大 `BIT_DUR`**（如 0.03～0.04 s） | 每 bit 相关更稳，抗频偏更好 | 比特率降低 |
| **降低数据 chirp 中心频率**（如 `BIT_F0,BIT_F1 = 1500,4500`） | Δf ∝ f，低频时绝对频偏更小 | 与同步段频带更近，需避免串扰 |
| **适当加大带宽**（如 1.5k～5.5 kHz） | 同一 Δf 占带宽比例更小 | 依赖设备与采样率 |
| 接收端**同步相关阈值**（`receiver.py` 中 `max_val > 8.0`） | 多普勒导致峰变矮时可适当降低以仍能检出 | 阈值过低易误检，需实测折中 |

---

## 项目结构

```text
communicate-chirp/
├── chirp_comm/
│   ├── __init__.py    # 导出 ChirpSender, ChirpReceiver
│   ├── config.py      # 物理层参数（FS, 频率, 时长, FEC 块长等）
│   ├── dsp.py         # chirp 生成（Hanning 窗）、Hamming(7,4) 编解码、payload 生成
│   ├── sender.py      # 发送端（队列 + 线程播放）
│   └── receiver.py    # 接收端（麦克风回调 + 动态位跟踪解码）
├── examples/
│   ├── send_demo.py   # 发送演示
│   └── recv_demo.py   # 接收演示
├── requirements.txt
├── setup.py
└── README.md
```

---

## 设备选择

- 使用默认设备时传 `device=None`。
- 查看设备列表：`ChirpSender.list_devices()` 或 `ChirpReceiver.list_devices()`（或 `python -c "import sounddevice as sd; print(sd.query_devices())"`）。
- 指定设备时传入整数索引或设备名称字符串，例如：
  - `ChirpSender(device=1)`、`ChirpReceiver(device=2)`
  - 或 `ChirpReceiver(device="default")`（视 sounddevice 支持而定）

---

## 注意事项与限制

- 单条消息固定为 **4 个字符**，编码后 56 bit（含 FEC），不适合长文本
- 接收端依赖同步 chirp 相关峰检测；强噪声或严重失真时可能漏检或误检，可结合业务做重发或校验
- 音频设备需支持 48 kHz 单声道；若设备不支持，可在 `config.py` 中修改 `FS` 并注意与发送端一致

---

## License

按项目仓库约定使用。
