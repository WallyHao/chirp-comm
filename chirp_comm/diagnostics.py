import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate
from scipy.io import wavfile
from .dsp import REF_SYNC, REF_UP, REF_DOWN, apply_bandpass
from .config import FS, SYNC_F0, SYNC_F1, BIT_F0, BIT_F1

class SignalDiagnostics:
    def __init__(self, file_path):
        sr, audio = wavfile.read(file_path)
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        elif audio.dtype == np.int32:
            audio = audio.astype(np.float32) / 2147483648.0
        if sr != FS:
            from scipy.signal import resample_poly
            gcd = np.gcd(FS, sr)
            audio = resample_poly(audio, FS // gcd, sr // gcd)
        self.audio = audio
        self.sync_corr = correlate(self.audio, REF_SYNC, mode='valid')
        self.peak_idx = np.argmax(self.sync_corr)
        self.peak_val = self.sync_corr[self.peak_idx]

    def analyze_and_show(self):
        fig = plt.figure(figsize=(12, 8))

        ax1 = fig.add_subplot(3, 1, 1)
        t = np.arange(len(self.audio)) / FS
        ax1.plot(t, self.audio, color='blue', alpha=0.7)
        ax1.axvline(x=self.peak_idx/FS, color='red', linestyle='--', label=f'SYNC at {self.peak_idx/FS:.3f}s')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Amplitude')
        ax1.set_title("Time Domain Waveform")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2 = fig.add_subplot(3, 1, 2)
        S = np.abs(np.fft.rfft(self.audio))
        freqs = np.fft.rfftfreq(len(self.audio), 1/FS)
        ax2.plot(freqs, S)
        ax2.axvline(x=SYNC_F0, color='g', linestyle='--', alpha=0.5)
        ax2.axvline(x=SYNC_F1, color='g', linestyle='--', alpha=0.5)
        ax2.set_xlim(0, 15000)
        ax2.set_xlabel('Frequency (Hz)')
        ax2.set_ylabel('Magnitude')
        ax2.set_title("Frequency Spectrum")
        ax2.grid(True, alpha=0.3)

        ax3 = fig.add_subplot(3, 1, 3)
        t_corr = np.arange(len(self.sync_corr)) / FS
        ax3.plot(t_corr, self.sync_corr, color='red')
        ax3.axhline(y=self.peak_val * 0.3, color='orange', linestyle='--', alpha=0.5)
        ax3.scatter([self.peak_idx/FS], [self.peak_val], color='blue', s=100, zorder=5)
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Correlation')
        ax3.set_title(f"SYNC Cross-Correlation (peak={self.peak_val:.1f})")
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def get_stats(self):
        """返回诊断统计信息"""
        return {
            'audio_length': len(self.audio) / FS,
            'sync_peak': self.peak_val,
            'sync_position': self.peak_idx / FS,
            'audio_energy': np.sum(self.audio**2),
        }
