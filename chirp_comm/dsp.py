import numpy as np

from .config import BIT_DUR, BIT_F0, BIT_F1, FS, SYNC_DUR, SYNC_F0, SYNC_F1


def generate_chirp(f0, f1, duration):
    n = int(FS * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    ch = np.sin(2 * np.pi * (f0 * t + (f1 - f0) * t**2 / (2 * duration)))
    # np.hanning matches scipy.signal.windows.hann, keeping the import scipy-free.
    fade = np.hanning(n)
    return (ch * fade).astype(np.float32)


REF_SYNC = generate_chirp(SYNC_F0, SYNC_F1, SYNC_DUR)
REF_UP = generate_chirp(BIT_F0, BIT_F1, BIT_DUR)
REF_DOWN = generate_chirp(BIT_F1, BIT_F0, BIT_DUR)


def get_bandpass_filter(lowcut, highcut, fs=None, order=4):
    """创建带通滤波器"""
    from scipy.signal import butter

    if fs is None:
        fs = FS
    nyq = fs / 2
    low = max(lowcut / nyq, 0.01)
    high = min(highcut / nyq, 0.99)
    b, a = butter(order, [low, high], btype="band")
    return b, a


def apply_bandpass(audio, lowcut=None, highcut=None):
    """对音频应用带通滤波"""
    from scipy.signal import filtfilt

    if lowcut is None:
        lowcut = SYNC_F0 - 500
    if highcut is None:
        highcut = SYNC_F1 + 500
    b, a = get_bandpass_filter(lowcut, highcut)
    return filtfilt(b, a, audio)


def hamming_74_encode(nibble_str):
    d = [int(b) for b in nibble_str]
    p1 = (d[0] + d[1] + d[3]) % 2
    p2 = (d[0] + d[2] + d[3]) % 2
    p3 = (d[1] + d[2] + d[3]) % 2
    return f"{p1}{p2}{d[0]}{p3}{d[1]}{d[2]}{d[3]}"


def hamming_74_decode(block_str):
    y = [int(b) for b in block_str]
    s1 = (y[0] + y[2] + y[4] + y[6]) % 2
    s2 = (y[1] + y[2] + y[5] + y[6]) % 2
    s3 = (y[3] + y[4] + y[5] + y[6]) % 2
    syn = s1 + (s2 << 1) + (s3 << 2)
    if syn != 0:
        y[syn - 1] = 1 - y[syn - 1]
    return f"{y[2]}{y[4]}{y[5]}{y[6]}"
