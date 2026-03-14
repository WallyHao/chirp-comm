import threading

import numpy as np
import sounddevice as sd
from scipy.signal import correlate

from .config import BIT_DUR, BIT_TOTAL_SAMPLES, FS, TOTAL_EXPECTED_BITS
from .dsp import REF_DOWN, REF_SYNC, REF_UP, bits_to_text_fec


class ChirpReceiver:
    def __init__(self, device=None, callback=None):
        self.device = device
        self.results = []
        self.buffer = np.array([], dtype=np.float32)
        self.lock = threading.Lock()
        self.callback = callback
        self.search_len = int(FS * 0.8)

    def _audio_callback(self, indata, frames, time, status):
        with self.lock:
            self.buffer = np.append(self.buffer, indata[:, 0])
            if len(self.buffer) > FS * 5:
                self.buffer = self.buffer[-int(FS * 5) :]
            self._process_buffer()

    def _process_buffer(self):
        while len(self.buffer) > self.search_len:
            corr = correlate(self.buffer[: self.search_len], REF_SYNC, mode="valid")
            max_val = np.max(corr)
            if max_val > 8.0:
                peak_idx = np.argmax(corr)
                curr_ptr = peak_idx + len(REF_SYNC) + int(FS * 0.05)
                bits = ""

                for _ in range(TOTAL_EXPECTED_BITS):
                    win_start = curr_ptr - int(BIT_TOTAL_SAMPLES * 0.15)
                    win_end = curr_ptr + int(BIT_TOTAL_SAMPLES * 1.15)
                    if win_end > len(self.buffer):
                        break

                    seg = self.buffer[win_start:win_end]
                    c_up = correlate(seg, REF_UP, mode="valid")
                    c_down = correlate(seg, REF_DOWN, mode="valid")

                    m_up, m_down = np.max(c_up), np.max(c_down)
                    if m_up > m_down:
                        bits += "1"
                        curr_ptr = win_start + np.argmax(c_up) + BIT_TOTAL_SAMPLES
                    else:
                        bits += "0"
                        curr_ptr = win_start + np.argmax(c_down) + BIT_TOTAL_SAMPLES

                if len(bits) == TOTAL_EXPECTED_BITS:
                    msg = bits_to_text_fec(bits)
                    self.results.append(msg)
                    if self.callback:
                        self.callback(msg)
                    self.buffer = self.buffer[curr_ptr:]
                else:
                    break
            else:
                self.buffer = self.buffer[int(FS * 0.2) :]
                break

    def start(self):
        self.stream = sd.InputStream(
            samplerate=FS,
            device=self.device,
            channels=1,
            callback=self._audio_callback,
        )
        self.stream.start()

    def stop(self):
        self.stream.stop()
        self.stream.close()

    def get_messages(self):
        with self.lock:
            res = list(self.results)
            self.results.clear()
            return res

    @staticmethod
    def list_devices():
        return sd.query_devices()
