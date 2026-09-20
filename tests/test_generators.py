"""Tests for the sample-generation helpers."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "examples" / "generate_to_file.py"
_SPEC = importlib.util.spec_from_file_location("generate_to_file", MODULE_PATH)
generate_to_file = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(generate_to_file)

FS = 48000


def _peak_frequency(signal, fs):
    spectrum = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(len(signal), 1 / fs)
    return freqs[int(np.argmax(spectrum))]


def test_doppler_shift_moves_a_tone():
    tone = np.sin(2 * np.pi * 3000 * np.arange(FS) / FS).astype(np.float32)
    shifted = generate_to_file.apply_doppler_shift(tone, shift_hz=100, reference_hz=3000.0)
    assert _peak_frequency(shifted, FS) == pytest.approx(3100, abs=30)


def test_pink_noise_is_redder_than_white():
    carrier = np.full(FS, 0.1, dtype=np.float32)
    noise = generate_to_file.add_pink_noise(carrier, snr_db=0) - carrier
    spectrum = np.abs(np.fft.rfft(noise)) ** 2
    freqs = np.fft.rfftfreq(len(noise), 1 / FS)
    low_band = spectrum[(freqs >= 100) & (freqs <= 500)].mean()
    high_band = spectrum[(freqs >= 5000) & (freqs <= 9000)].mean()
    # 1/f power means the low band holds far more energy than the high band.
    assert low_band / high_band > 5
