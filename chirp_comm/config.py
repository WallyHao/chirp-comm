FS = 48000
# 频率越高衰减越快，2-4kHz 更适合手机音频
SYNC_F0 = 2000
SYNC_F1 = 4000
BIT_F0 = 2000
BIT_F1 = 4000
# 同步信号时长
SYNC_DUR = 0.15
# 减小每 bit 时长以缩短总传输时间
# 46 bits × (0.05 + 0.01)s = 2.76s + 0.15s 同步 ≈ 3s
BIT_DUR = 0.05
PAUSE = 0.01
BIT_TOTAL_SAMPLES = int(FS * (BIT_DUR + PAUSE))
DATA_LEN_CHARS = 2
BITS_PER_BLOCK = 7
BLOCKS_PER_CHAR = 2
# 编码后总位数 = 数据位 + 奇偶校验位 + CRC位
# 数据: 2字符 × 2blocks × 7bits = 28 bits
# 奇偶: 28/7 = 4 bits
# CRC-8 Hamming编码: 8bits → 2×7 = 14 bits
DATA_BITS = DATA_LEN_CHARS * BLOCKS_PER_CHAR * BITS_PER_BLOCK
PARITY_BITS = DATA_BITS // 7
CRC_BITS = 14  # CRC-8 encoded as 2×Hamming(7,4)
TOTAL_EXPECTED_BITS = DATA_BITS + PARITY_BITS + CRC_BITS
# 自适应阈值（基于噪声水平的倍数）
SYNC_THRESHOLD_RATIO = 3.0
BIT_ENERGY_THRESHOLD_RATIO = 2.0
