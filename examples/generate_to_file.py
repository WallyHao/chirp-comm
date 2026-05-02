#!/usr/bin/env python3
"""
Generate chirp audio samples for testing

Usage:
    python generate_to_file.py              # Generate all samples
    python generate_to_file.py --clean      # Generate clean signal only
    python generate_to_file.py --noisy      # Generate noisy samples
    python generate_to_file.py --distorted  # Generate distorted samples
"""
import os
import argparse
import numpy as np
import scipy.io.wavfile as wav
from chirp_comm.config import FS, SYNC_DUR, BIT_DUR, PAUSE
from chirp_comm.dsp import REF_SYNC, REF_UP, REF_DOWN
from chirp_comm.protocol import ChirpProtocol

SAMPLES_DIR = "samples"


def generate_clean_signal(text="ab", duration_before=0.5, duration_after=0.5):
    """Generate clean chirp signal"""
    bits = ChirpProtocol.encode_to_bits(text)

    audio = [
        np.zeros(int(FS * duration_before)),
        REF_SYNC,
        np.zeros(int(FS * 0.1))
    ]

    for bit in bits:
        audio.append(REF_UP if bit == "1" else REF_DOWN)
        audio.append(np.zeros(int(FS * PAUSE)))

    audio.append(np.zeros(int(FS * duration_after)))
    return np.concatenate(audio).astype(np.float32)


def add_gaussian_noise(audio, snr_db=10):
    """Add Gaussian white noise"""
    signal_power = np.mean(audio ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = np.random.normal(0, np.sqrt(noise_power), len(audio))
    return audio + noise


def add_pink_noise(audio, snr_db=10):
    """Add pink noise (1/f noise)"""
    signal_power = np.mean(audio ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10))

    # Generate pink noise: white noise through 1/f filter
    white = np.random.normal(0, 1, len(audio))
    # Simplified pink noise approximation
    pink = np.cumsum(white)
    pink = pink - np.mean(pink)
    pink = pink / np.max(np.abs(pink)) * np.sqrt(noise_power)
    return audio + pink


def add_hum(audio, snr_db=10, freq=50):
    """Add AC hum interference"""
    signal_power = np.mean(audio ** 2)
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


def apply_doppler_shift(audio, shift_hz=100):
    """Apply Doppler frequency shift"""
    t = np.arange(len(audio)) / FS
    return audio * np.sin(2 * np.pi * shift_hz * t)


def add_reverb(audio, decay=0.3, delay=0.1):
    """Add simple reverb effect"""
    result = audio.copy()
    delay_samples = int(delay * FS)
    for i in range(1, 4):
        attenuated = audio.copy() * (decay ** i)
        if delay_samples * i < len(result):
            result[delay_samples * i:] += attenuated[:-delay_samples * i] * 0.5
    return result


def add_clicks(audio, n_clicks=10):
    """Add impulse noise (click sounds similar to recording device)"""
    result = audio.copy()
    for _ in range(n_clicks):
        pos = np.random.randint(int(FS * 0.5), len(audio) - 100)
        click = np.exp(-np.arange(100) / 10) * np.random.uniform(-0.5, 0.5)
        result[pos:pos + 100] += click
    return result


def generate_all_samples(text="ab"):
    """Generate all test samples"""
    os.makedirs(SAMPLES_DIR, exist_ok=True)

    # Clean signal
    clean = generate_clean_signal(text)
    wav.write(f"{SAMPLES_DIR}/01_clean.wav", FS, clean)
    print(f"  [OK] 01_clean.wav - Clean signal")

    # Different SNR Gaussian noise
    for snr in [20, 15, 10, 5]:
        noisy = add_gaussian_noise(clean, snr_db=snr)
        wav.write(f"{SAMPLES_DIR}/02_gaussian_snr{snr}.wav", FS, np.clip(noisy, -1, 1))
        print(f"  [OK] 02_gaussian_snr{snr}.wav - Gaussian noise SNR={snr}dB")

    # Pink noise
    pink = add_pink_noise(clean, snr_db=10)
    wav.write(f"{SAMPLES_DIR}/03_pink_noise.wav", FS, np.clip(pink, -1, 1))
    print(f"  [OK] 03_pink_noise.wav - Pink noise")

    # AC hum
    for freq in [50, 100]:
        hum = add_hum(clean, snr_db=15, freq=freq)
        wav.write(f"{SAMPLES_DIR}/04_hum_{freq}hz.wav", FS, np.clip(hum, -1, 1))
        print(f"  [OK] 04_hum_{freq}hz.wav - {freq}Hz hum interference")

    # Burst noise
    burst = add_burst_noise(clean, n_bursts=5)
    wav.write(f"{SAMPLES_DIR}/05_burst_noise.wav", FS, np.clip(burst, -1, 1))
    print(f"  [OK] 05_burst_noise.wav - Burst noise")

    # Signal dropout
    dropout = add_dropout(clean, n_dropouts=2)
    wav.write(f"{SAMPLES_DIR}/06_dropout.wav", FS, dropout)
    print(f"  [OK] 06_dropout.wav - Signal dropout")

    # Volume attenuation
    for factor in [0.5, 0.3, 0.1]:
        vol = apply_volume(clean, factor)
        wav.write(f"{SAMPLES_DIR}/07_volume_{int(factor*100)}.wav", FS, vol)
        print(f"  [OK] 07_volume_{int(factor*100)}.wav - Volume {int(factor*100)}%")

    # Doppler frequency shift
    for shift in [50, -50, 200]:
        doppler = apply_doppler_shift(clean, shift_hz=shift)
        wav.write(f"{SAMPLES_DIR}/08_doppler_{'+' if shift>0 else ''}{shift}hz.wav", FS, np.clip(doppler, -1, 1))
        print(f"  [OK] 08_doppler_{'+' if shift>0 else ''}{shift}hz.wav - Freq shift {shift}Hz")

    # Reverb
    reverb = add_reverb(clean, decay=0.3, delay=0.05)
    wav.write(f"{SAMPLES_DIR}/09_reverb.wav", FS, np.clip(reverb, -1, 1))
    print(f"  [OK] 09_reverb.wav - Reverb effect")

    # Impulse noise
    clicks = add_clicks(clean, n_clicks=10)
    wav.write(f"{SAMPLES_DIR}/10_clicks.wav", FS, np.clip(clicks, -1, 1))
    print(f"  [OK] 10_clicks.wav - Impulse noise")

    # Combined interference
    combined = add_gaussian_noise(clean, snr_db=15)
    combined = add_hum(combined, snr_db=20, freq=50)
    combined = add_burst_noise(combined, n_bursts=3)
    wav.write(f"{SAMPLES_DIR}/11_combined.wav", FS, np.clip(combined, -1, 1))
    print(f"  [OK] 11_combined.wav - Combined interference")

    print(f"\nAll samples saved to {SAMPLES_DIR}/")
    return SAMPLES_DIR


def main():
    parser = argparse.ArgumentParser(description="Generate chirp test samples")
    parser.add_argument("--text", "-t", default="ab", help="Text to encode")
    parser.add_argument("--clean", action="store_true", help="Generate clean signal only")
    parser.add_argument("--noisy", action="store_true", help="Generate noisy samples")
    parser.add_argument("--distorted", action="store_true", help="Generate distorted samples")
    args = parser.parse_args()

    if args.clean:
        os.makedirs(SAMPLES_DIR, exist_ok=True)
        clean = generate_clean_signal(args.text)
        wav.write(f"{SAMPLES_DIR}/clean.wav", FS, clean)
        print(f"Generated clean signal: {SAMPLES_DIR}/clean.wav")
    elif args.noisy:
        generate_all_samples(args.text)
    elif args.distorted:
        generate_all_samples(args.text)
    else:
        generate_all_samples(args.text)


if __name__ == "__main__":
    main()
