import numpy as np
from scipy.signal import correlate
from .config import *


def generate_chirp(f0, f1, duration):
    t = np.linspace(0, duration, int(FS * duration))
    ch = np.sin(2 * np.pi * (f0 * t + (f1 - f0) * t**2 / (2 * duration)))
    fade = np.hanning(len(t))
    return ch * fade


REF_SYNC = generate_chirp(SYNC_F0, SYNC_F1, SYNC_DUR).astype(np.float32)
REF_UP = generate_chirp(BIT_F0, BIT_F1, BIT_DUR).astype(np.float32)
REF_DOWN = generate_chirp(BIT_F1, BIT_F0, BIT_DUR).astype(np.float32)


def _hamming_74_encode(nibble_str):
    d = [int(b) for b in nibble_str]
    p1 = (d[0] + d[1] + d[3]) % 2
    p2 = (d[0] + d[2] + d[3]) % 2
    p3 = (d[1] + d[2] + d[3]) % 2
    return f"{p1}{p2}{d[0]}{p3}{d[1]}{d[2]}{d[3]}"


def _hamming_74_decode(block_str):
    y = [int(b) for b in block_str]
    s1 = (y[0] + y[2] + y[4] + y[6]) % 2
    s2 = (y[1] + y[2] + y[5] + y[6]) % 2
    s3 = (y[3] + y[4] + y[5] + y[6]) % 2
    syn = s1 + (s2 << 1) + (s3 << 2)
    if syn != 0:
        y[syn - 1] = 1 - y[syn - 1]
    return f"{y[2]}{y[4]}{y[5]}{y[6]}"


def text_to_bits_fec(text):
    text = text[:DATA_LEN_CHARS].ljust(DATA_LEN_CHARS)
    bit_stream = ""
    for char in text:
        byte = format(ord(char), "08b")
        bit_stream += _hamming_74_encode(byte[:4])
        bit_stream += _hamming_74_encode(byte[4:])
    return bit_stream


def bits_to_text_fec(bit_stream):
    chars = []
    for i in range(0, len(bit_stream), BITS_PER_BLOCK * BLOCKS_PER_CHAR):
        char_bits = bit_stream[i : i + BITS_PER_BLOCK * BLOCKS_PER_CHAR]
        if len(char_bits) < BITS_PER_BLOCK * BLOCKS_PER_CHAR:
            break
        b1 = _hamming_74_decode(char_bits[:7])
        b2 = _hamming_74_decode(char_bits[7:])
        chars.append(chr(int(b1 + b2, 2)))
    return "".join(chars)


def create_audio_payload(text):
    bits = text_to_bits_fec(text)
    audio = [np.zeros(int(FS * 0.4)), REF_SYNC, np.zeros(int(FS * 0.05))]
    gap = np.zeros(int(FS * PAUSE))
    for bit in bits:
        audio.append(REF_UP if bit == "1" else REF_DOWN)
        audio.append(gap)
    audio.append(np.zeros(int(FS * 0.4)))
    return np.concatenate(audio).astype(np.float32)
