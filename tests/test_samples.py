"""End-to-end checks that the committed samples still decode."""

import wave
from pathlib import Path

import numpy as np

from chirp_comm.config import BIT_TOTAL_SAMPLES, FS, TOTAL_EXPECTED_BITS
from chirp_comm.dsp import REF_DOWN, REF_SYNC, REF_UP
from chirp_comm.protocol import ChirpProtocol

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def _read_wav(path):
    with wave.open(str(path), "rb") as handle:
        frames = handle.readframes(handle.getnframes())
    return np.frombuffer(frames, dtype="<i2").astype(np.float64) / 32768.0


def _demodulate(audio):
    correlation = np.correlate(audio, REF_SYNC, mode="valid")
    pointer = int(np.argmax(correlation)) + len(REF_SYNC) + int(FS * 0.1)
    bits = ""
    for _ in range(TOTAL_EXPECTED_BITS):
        start = pointer - int(BIT_TOTAL_SAMPLES * 0.1)
        end = pointer + int(BIT_TOTAL_SAMPLES * 1.1)
        if end > len(audio):
            break
        segment = audio[start:end]
        up = np.correlate(segment, REF_UP, mode="valid")
        down = np.correlate(segment, REF_DOWN, mode="valid")
        if np.max(up) > np.max(down):
            bits += "1"
            pointer = start + int(np.argmax(up)) + BIT_TOTAL_SAMPLES
        else:
            bits += "0"
            pointer = start + int(np.argmax(down)) + BIT_TOTAL_SAMPLES
    return bits


def test_clean_sample_decodes():
    audio = _read_wav(SAMPLES / "01_clean.wav")
    assert ChirpProtocol.decode_from_bits(_demodulate(audio)) == "ab"


def test_low_noise_sample_decodes():
    audio = _read_wav(SAMPLES / "02_gaussian_snr20.wav")
    assert ChirpProtocol.decode_from_bits(_demodulate(audio)) == "ab"
