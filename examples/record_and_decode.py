#!/usr/bin/env python3
"""
Record and decode chirp signal

Usage:
    python record_and_decode.py                    # Record and analyze
    python record_and_decode.py --duration 5       # Record for 5 seconds
    python record_and_decode.py --play samples/01_clean.wav  # Play specified file
"""

import argparse

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from scipy.signal import correlate

from chirp_comm.config import BIT_TOTAL_SAMPLES, FS, TOTAL_EXPECTED_BITS
from chirp_comm.dsp import REF_DOWN, REF_SYNC, REF_UP
from chirp_comm.protocol import ChirpProtocol


def record_audio(duration=8):
    """Record audio"""
    print(f"Recording for {duration} seconds...")
    print("Please prepare to play audio from phone/computer")
    print("Press Ctrl+C to cancel\n")

    try:
        print("Recording started...")
        recording = sd.rec(int(duration * FS), samplerate=FS, channels=1)
        sd.wait()
        rx_audio = recording.flatten()
        print(f"Recording complete! Duration: {len(rx_audio) / FS:.2f}s")
        return rx_audio
    except KeyboardInterrupt:
        print("\nRecording cancelled")
        return None


def analyze_audio(rx_audio):
    """Analyze recorded audio"""
    print("\n" + "-" * 60)
    print("Analyzing recorded audio...")
    print(f"Signal RMS: {np.sqrt(np.mean(rx_audio**2)):.6f}")

    # Detect sync
    corr = correlate(rx_audio, REF_SYNC, mode="valid")
    peak_val = np.max(corr)
    peak_idx = np.argmax(corr)

    print("\nSync detection:")
    print(f"  Correlation peak: {peak_val:.2f}")
    print(f"  Peak position: {peak_idx / FS:.3f}s")

    if peak_val <= 50:
        print("  [FAIL] No sync signal detected")
        print("\nPossible causes:")
        print("  1. Phone volume too low")
        print("  2. Microphone and phone too far apart")
        print("  3. Recording finished before playback started")
        return

    print("  [OK] Sync signal detected!")

    # Decode bits
    print("\nDecoding bits...")
    curr_ptr = peak_idx + len(REF_SYNC) + int(FS * 0.1)
    bits = ""

    for _ in range(TOTAL_EXPECTED_BITS):
        win_start = curr_ptr - int(BIT_TOTAL_SAMPLES * 0.1)
        win_end = curr_ptr + int(BIT_TOTAL_SAMPLES * 1.1)
        if win_end > len(rx_audio):
            break
        seg = rx_audio[win_start:win_end]
        c_up = correlate(seg, REF_UP, mode="valid")
        c_down = correlate(seg, REF_DOWN, mode="valid")
        bits += "1" if np.max(c_up) > np.max(c_down) else "0"
        curr_ptr = (
            win_start
            + (np.argmax(c_up) if np.max(c_up) > np.max(c_down) else np.argmax(c_down))
            + BIT_TOTAL_SAMPLES
        )

    print(f"  Extracted bits: {len(bits)}")

    # Calculate bit error rate
    expected_bits = ChirpProtocol.encode_to_bits("ab")
    errors = sum(a != b for a, b in zip(bits, expected_bits))
    print(f"  Raw errors: {errors}/{len(expected_bits)} ({100 * errors / len(expected_bits):.1f}%)")

    # Decode
    try:
        decoded = ChirpProtocol.decode_from_bits(bits)
        print(f"  Decoded result: '{decoded}'")

        if decoded == "ab":
            print("  [OK] Decoded correctly (error correction successful)!")
        elif decoded == "!!!":
            print("  [FAIL] CRC checksum error")
        elif decoded == "???":
            print("  [FAIL] Insufficient data length")
        else:
            print("  Expected: 'ab'")
    except Exception as e:
        print(f"  Decode failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Record and decode chirp signal")
    parser.add_argument(
        "--duration", "-d", type=float, default=8, help="Recording duration (seconds)"
    )
    parser.add_argument("--save", "-s", help="Save recorded audio to specified file")
    parser.add_argument("--play", "-p", help="Play specified audio file (requires mpv or similar)")
    args = parser.parse_args()

    if args.play:
        import subprocess

        print(f"Playing: {args.play}")
        subprocess.run(["mpv", "--no-video", args.play])
        return

    print("=" * 60)
    print("Record and Decode Chirp Signal")
    print("=" * 60)
    print(f"\nExpected data bits: {TOTAL_EXPECTED_BITS}")

    rx_audio = record_audio(args.duration)

    if rx_audio is not None:
        # Save
        if args.save:
            wavfile.write(args.save, FS, rx_audio.astype(np.float32))
            print(f"Saved to {args.save}")

        # Analyze
        analyze_audio(rx_audio)


if __name__ == "__main__":
    main()
