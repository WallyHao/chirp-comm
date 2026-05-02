import threading
import queue
import numpy as np
import sounddevice as sd
from scipy.signal import correlate
from .config import FS, PAUSE, BIT_TOTAL_SAMPLES, TOTAL_EXPECTED_BITS, DATA_LEN_CHARS, SYNC_THRESHOLD_RATIO, BIT_ENERGY_THRESHOLD_RATIO
from .dsp import REF_SYNC, REF_UP, REF_DOWN, apply_bandpass
from .protocol import ChirpProtocol
from .packet import AcousticPacket
from .audio_io import AsyncInputStream

class Transmitter:
    def __init__(self, device=None):
        self.device = device

    def send(self, text):
        chunks = [text[i:i+DATA_LEN_CHARS] for i in range(0, max(1, len(text)), DATA_LEN_CHARS)]
        if not chunks:
            chunks = ["  "]
        for chunk in chunks:
            bits = ChirpProtocol.encode_to_bits(chunk)
            audio = [np.zeros(int(FS * 0.3)), REF_SYNC, np.zeros(int(FS * 0.1))]
            gap = np.zeros(int(FS * PAUSE))
            for bit in bits:
                audio.append(REF_UP if bit == "1" else REF_DOWN)
                audio.append(gap)
            audio.append(np.zeros(int(FS * 0.3)))
            payload = np.concatenate(audio).astype(np.float32)
            sd.play(payload, samplerate=FS, device=self.device)
            sd.wait()

class Listener:
    def __init__(self, device=None):
        self.device = device
        self.buffer = np.array([], dtype=np.float32)
        self.lock = threading.Lock()
        self.handlers = []
        self.noise_floor = 0.0
        self.noise_samples = []
        self.stream = AsyncInputStream(FS, self._on_audio, device=self.device)

    def on_packet(self, handler):
        self.handlers.append(handler)

    def _update_noise_floor(self, data):
        """更新噪声基准"""
        self.noise_samples.extend(np.abs(data).tolist())
        if len(self.noise_samples) > FS * 2:
            self.noise_floor = np.median(self.noise_samples[-int(FS * 2):])
            self.noise_samples = self.noise_samples[-int(FS):]

    def _get_sync_threshold(self):
        """获取同步检测阈值"""
        return max(self.noise_floor * SYNC_THRESHOLD_RATIO * 100, 15.0)

    def _get_bit_threshold(self):
        """获取bit检测阈值"""
        return self.noise_floor * BIT_ENERGY_THRESHOLD_RATIO * 50

    def _on_audio(self, data):
        with self.lock:
            self.buffer = np.append(self.buffer, data)
            if len(self.buffer) > FS * 10:
                self.buffer = self.buffer[-int(FS * 10):]
            self._update_noise_floor(data)
            self._process()

    def _find_sync(self, search_window):
        """在搜索窗口中查找同步信号"""
        corr = correlate(search_window, REF_SYNC, mode='valid')
        threshold = self._get_sync_threshold()
        max_val = np.max(corr)
        if max_val > threshold:
            return np.argmax(corr), max_val
        return None, 0.0

    def _get_bit(self, segment):
        """检测单个bit"""
        if len(segment) < len(REF_UP):
            return None

        c_up = correlate(segment, REF_UP, mode="valid")
        c_down = correlate(segment, REF_DOWN, mode="valid")
        m_up, m_down = np.max(c_up), np.max(c_down)

        threshold = self._get_bit_threshold()
        if max(m_up, m_down) < threshold:
            return None

        if m_up > m_down:
            return "1", np.argmax(c_up)
        else:
            return "0", np.argmax(c_down)

    def _process(self):
        # 完整数据包需要: 同步 + 数据位 + 奇偶校验 + CRC + 余量
        min_buffer_needed = len(REF_SYNC) + TOTAL_EXPECTED_BITS * BIT_TOTAL_SAMPLES + int(FS * 0.5)

        while len(self.buffer) > int(FS * 0.5):
            # 搜索窗口至少需要能包含完整数据包
            search_len = min(int(FS * 4.0), len(self.buffer))

            sync_pos, sync_val = self._find_sync(self.buffer[:search_len])

            if sync_pos is None:
                self.buffer = self.buffer[int(FS * 0.5):]
                continue

            # 检查是否有足够的数据来解码完整数据包
            data_end_estimate = sync_pos + min_buffer_needed
            if data_end_estimate > len(self.buffer):
                # 数据不足，等待更多数据
                break

            curr_ptr = sync_pos + len(REF_SYNC) + int(FS * 0.1)
            bits = ""

            for _ in range(TOTAL_EXPECTED_BITS):
                win_start = curr_ptr - int(BIT_TOTAL_SAMPLES * 0.1)
                win_end = curr_ptr + int(BIT_TOTAL_SAMPLES * 1.1)

                if win_end > len(self.buffer):
                    break

                seg = self.buffer[win_start:win_end]
                result = self._get_bit(seg)

                if result is None:
                    break

                bit, offset = result
                bits += bit
                curr_ptr = win_start + offset + BIT_TOTAL_SAMPLES

            if len(bits) == TOTAL_EXPECTED_BITS:
                text = ChirpProtocol.decode_from_bits(bits)
                packet = AcousticPacket(payload=text, rssi=float(sync_val))
                for h in self.handlers:
                    h(packet)
                self.buffer = self.buffer[curr_ptr:]
            else:
                self.buffer = self.buffer[sync_pos + len(REF_SYNC):]

    def start(self):
        self.stream.start()

    def stop(self):
        self.stream.stop()
