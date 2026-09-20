#!/usr/bin/env python3
"""
Generate chirp audio samples for testing.

Usage:
    python generate_to_file.py              # Generate all samples
    python generate_to_file.py --clean      # Generate clean signal only
    python generate_to_file.py --seed 42    # Reproducible interference
"""

import argparse
import os
import wave

import numpy as np

from chirp_comm.config import FS, PAUSE
from chirp_comm.dsp import REF_DOWN, REF_SYNC, REF_UP
from chirp_comm.protocol import ChirpProtocol

SAMPLES_DIR = "samples"


def write_wav(path, audio, fs=FS):
    """Write a mono 16-bit PCM WAV file using only the standard library."""
    samples = np.clip(audio, -1.0, 1.0)
    pcm = (samples * 32767.0).astype("<i2")
    with wave.open(path, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(fs)
        handle.writeframes(pcm.tobytes())


def generate_clean_signal(text="ab", duration_before=0.5, duration_after=0.5):
    """Generate clean chirp signal"""
    bits = ChirpProtocol.encode_to_bits(text)

    audio = [np.zeros(int(FS * duration_before)), REF_SYNC, np.zeros(int(FS * 0.1))]

    for bit in bits:
        audio.append(REF_UP if bit == "1" else REF_DOWN)
        audio.append(np.zeros(int(FS * PAUSE)))

    audio.append(np.zeros(int(FS * duration_after)))
    return np.concatenate(audio).astype(np.float32)


def add_gaussian_noise(audio, snr_db=10):
    """Add Gaussian white noise"""
    signal_power = np.mean(audio**2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = np.random.normal(0, np.sqrt(noise_power), len(audio))
    return audio + noise


def add_pink_noise(audio, snr_db=10):
    """Add pink (1/f) noise shaped in the frequency domain.

    The amplitude spectrum is scaled by 1/sqrt(f), which makes the power
    spectrum fall off as 1/f. A cumulative sum of white noise would instead
    produce Brownian (1/f^2) noise.
    """
    signal_power = np.mean(audio**2)
    noise_power = signal_power / (10 ** (snr_db / 10))

    n = len(audio)
    spectrum = np.fft.rfft(np.random.normal(0, 1, n))
    freqs = np.fft.rfftfreq(n)
    shape = np.ones_like(freqs)
    shape[1:] = 1.0 / np.sqrt(freqs[1:])
    pink = np.fft.irfft(spectrum * shape, n=n)
    pink = pink / np.sqrt(np.mean(pink**2)) * np.sqrt(noise_power)
    return audio + pink


def add_hum(audio, snr_db=10, freq=50):
    """Add AC hum interference"""
    signal_power = np.mean(audio**2)
    noise_power = signal_power / (10 ** (snr_db / 10))

    t = np.arange(len(audio)) / FS
    hum = np.sin(2 * np.pi * freq * t) * np.sqrt(noise_power)
    return audio + hum


def add_burst_noise(audio, n_bursts=5, burst_duration=0.002):
    """Add burst noise (short duration high amplitude interference)"""
    result = audio.copy()
    for _ in range(n_bursts):
        start = np.random.randint(int(FS * 0.5), len(audio) - int(FS * 1))
        length = int(burst_duration * FS)
        end = min(start + length, len(result))
        amplitude = np.random.uniform(0.3, 0.8)
        result[start:end] += np.random.uniform(-amplitude, amplitude, end - start)
    return result


def add_dropout(audio, n_dropouts=2, dropout_duration=0.01):
    """Add signal dropout (silent segments)"""
    result = audio.copy()
    for _ in range(n_dropouts):
        start = np.random.randint(int(FS * 0.5), len(audio) - int(FS * 1))
        length = int(dropout_duration * FS)
        end = min(start + length, len(result))
        result[start:end] *= 0.1
    return result


def apply_volume(audio, factor):
    """Adjust volume"""
    return audio * factor


def apply_doppler_shift(audio, shift_hz=100, reference_hz=3000.0):
    """Apply a Doppler shift by time-scaling the whole signal.

    Doppler scales every frequency by the same factor, so a shift of
    ``shift_hz`` measured at ``reference_hz`` is modelled by resampling the
    signal by ``1 + shift_hz / reference_hz``. Positive shifts compress the
    signal and raise its frequencies; negative shifts stretch it. Ring
    modulating with a sine would only create sidebands, not a shift.
    """
    factor = 1.0 + shift_hz / reference_hz
    n = len(audio)
    out_len = int(np.floor((n - 1) / factor)) + 1
    source = np.arange(out_len) * factor
    return np.interp(source, np.arange(n), audio).astype(np.float32)


def add_reverb(audio, decay=0.3, delay=0.1):
    """Add simple reverb effect"""
    result = audio.copy()
    delay_samples = int(delay * FS)
    for i in range(1, 4):
        attenuated = audio.copy() * (decay**i)
        if delay_samples * i < len(result):
            result[delay_samples * i :] += attenuated[: -delay_samples * i] * 0.5
    return result


def add_clicks(audio, n_clicks=10):
    """Add impulse noise (click sounds similar to recording device)"""
    result = audio.copy()
    for _ in range(n_clicks):
        pos = np.random.randint(int(FS * 0.5), len(audio) - 100)
        click = np.exp(-np.arange(100) / 10) * np.random.uniform(-0.5, 0.5)
        result[pos : pos + 100] += click
    return result


def generate_all_samples(text="ab", seed=0):
    """Generate all test samples"""
    np.random.seed(seed)
    os.makedirs(SAMPLES_DIR, exist_ok=True)

    # Clean signal
    clean = generate_clean_signal(text)
    write_wav(f"{SAMPLES_DIR}/01_clean.wav", clean)
    print("  [OK] 01_clean.wav - Clean signal")

    # Different SNR Gaussian noise
    for snr in [20, 15, 10, 5]:
        noisy = add_gaussian_noise(clean, snr_db=snr)
        write_wav(f"{SAMPLES_DIR}/02_gaussian_snr{snr}.wav", noisy)
        print(f"  [OK] 02_gaussian_snr{snr}.wav - Gaussian noise SNR={snr}dB")

    # Pink noise
    pink = add_pink_noise(clean, snr_db=10)
    write_wav(f"{SAMPLES_DIR}/03_pink_noise.wav", pink)
    print("  [OK] 03_pink_noise.wav - Pink noise")

    # AC hum
    for freq in [50, 100]:
        hum = add_hum(clean, snr_db=15, freq=freq)
        write_wav(f"{SAMPLES_DIR}/04_hum_{freq}hz.wav", hum)
        print(f"  [OK] 04_hum_{freq}hz.wav - {freq}Hz hum interference")

    # Burst noise
    burst = add_burst_noise(clean, n_bursts=5)
    write_wav(f"{SAMPLES_DIR}/05_burst_noise.wav", burst)
    print("  [OK] 05_burst_noise.wav - Burst noise")

    # Signal dropout
    dropout = add_dropout(clean, n_dropouts=2)
    write_wav(f"{SAMPLES_DIR}/06_dropout.wav", dropout)
    print("  [OK] 06_dropout.wav - Signal dropout")

    # Volume attenuation
    for factor in [0.5, 0.3, 0.1]:
        vol = apply_volume(clean, factor)
        write_wav(f"{SAMPLES_DIR}/07_volume_{int(factor * 100)}.wav", vol)
        print(f"  [OK] 07_volume_{int(factor * 100)}.wav - Volume {int(factor * 100)}%")

    # Doppler frequency shift
    for shift in [50, -50, 200]:
        doppler = apply_doppler_shift(clean, shift_hz=shift)
        sign = "+" if shift >= 0 else ""
        write_wav(f"{SAMPLES_DIR}/08_doppler_{sign}{shift}hz.wav", doppler)
        print(f"  [OK] 08_doppler_{sign}{shift}hz.wav - Freq shift {shift}Hz")

    # Reverb
    reverb = add_reverb(clean, decay=0.3, delay=0.05)
    write_wav(f"{SAMPLES_DIR}/09_reverb.wav", reverb)
    print("  [OK] 09_reverb.wav - Reverb effect")

    # Impulse noise
    clicks = add_clicks(clean, n_clicks=10)
    write_wav(f"{SAMPLES_DIR}/10_clicks.wav", clicks)
    print("  [OK] 10_clicks.wav - Impulse noise")

    # Combined interference
    combined = add_gaussian_noise(clean, snr_db=15)
    combined = add_hum(combined, snr_db=20, freq=50)
    combined = add_burst_noise(combined, n_bursts=3)
    write_wav(f"{SAMPLES_DIR}/11_combined.wav", combined)
    print("  [OK] 11_combined.wav - Combined interference")

    print(f"\nAll samples saved to {SAMPLES_DIR}/")
    return SAMPLES_DIR


def main():
    parser = argparse.ArgumentParser(description="Generate chirp test samples")
    parser.add_argument("--text", "-t", default="ab", help="Text to encode")
    parser.add_argument("--clean", action="store_true", help="Generate clean signal only")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for reproducibility")
    args = parser.parse_args()

    if args.clean:
        os.makedirs(SAMPLES_DIR, exist_ok=True)
        clean = generate_clean_signal(args.text)
        write_wav(f"{SAMPLES_DIR}/clean.wav", clean)
        print(f"Generated clean signal: {SAMPLES_DIR}/clean.wav")
    else:
        generate_all_samples(args.text, seed=args.seed)


if __name__ == "__main__":
    main()
