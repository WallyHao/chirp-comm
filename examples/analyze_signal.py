#!/usr/bin/env python3
"""
Analyze chirp signal samples

Usage:
    python analyze_signal.py                    # Analyze all samples
    python analyze_signal.py samples/01_clean.wav  # Analyze specific file
"""
import sys
import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import correlate
from chirp_comm.config import FS, BIT_TOTAL_SAMPLES, TOTAL_EXPECTED_BITS
from chirp_comm.dsp import REF_SYNC, REF_UP, REF_DOWN
from chirp_comm.protocol import ChirpProtocol


def analyze_signal(audio, filename="unknown"):
    """Analyze chirp signal"""
    # Ensure audio is in range -1 to 1
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0
    elif audio.max() > 1.0 or audio.min() < -1.0:
        audio = audio.astype(np.float32)
        audio = audio / (np.max(np.abs(audio)) + 1e-10)

    results = {
        "filename": filename,
        "rms": np.sqrt(np.mean(audio ** 2)),
        "peak": np.max(np.abs(audio)),
        "sync_detected": False,
        "sync_peak": 0,
        "sync_position": 0,
        "bits_extracted": 0,
        "errors": 0,
        "error_rate": 0,
        "decoded": None,
        "status": "N/A"
    }

    # Detect sync
    corr = correlate(audio, REF_SYNC, mode='valid')
    if len(corr) > 0:
        results["sync_peak"] = np.max(corr)
        results["sync_position"] = np.argmax(corr) / FS
        results["sync_detected"] = results["sync_peak"] > 50

    if not results["sync_detected"]:
        results["status"] = "NO_SYNC"
        return results

    # Decode bits
    peak_idx = np.argmax(corr)
    curr_ptr = peak_idx + len(REF_SYNC) + int(FS * 0.1)
    bits = ""

    for i in range(TOTAL_EXPECTED_BITS):
        win_start = curr_ptr - int(BIT_TOTAL_SAMPLES * 0.1)
        win_end = curr_ptr + int(BIT_TOTAL_SAMPLES * 1.1)
        if win_end > len(audio):
            break
        seg = audio[win_start:win_end]
        c_up = correlate(seg, REF_UP, mode="valid")
        c_down = correlate(seg, REF_DOWN, mode="valid")
        bits += "1" if np.max(c_up) > np.max(c_down) else "0"
        curr_ptr = win_start + (np.argmax(c_up) if np.max(c_up) > np.max(c_down) else np.argmax(c_down)) + BIT_TOTAL_SAMPLES

    results["bits_extracted"] = len(bits)

    # Calculate bit error rate
    if len(bits) >= TOTAL_EXPECTED_BITS:
        expected_bits = ChirpProtocol.encode_to_bits("ab")
        errors = sum(a != b for a, b in zip(bits, expected_bits))
        results["errors"] = errors
        results["error_rate"] = errors / len(expected_bits) * 100

        try:
            results["decoded"] = ChirpProtocol.decode_from_bits(bits)
            if results["decoded"] == "ab":
                results["status"] = "OK"
            elif results["decoded"] == "!!!":
                results["status"] = "CRC_ERROR"
            else:
                results["status"] = "DECODE_ERROR"
        except:
            results["status"] = "DECODE_ERROR"
    else:
        results["status"] = "INSUFFICIENT_BITS"

    return results


def print_results(results):
    """Print analysis results"""
    print(f"\n{results['filename']}:")
    print(f"  RMS: {results['rms']:.4f}, Peak: {results['peak']:.4f}")
    print(f"  Sync: {'OK' if results['sync_detected'] else 'FAIL'} (peak={results['sync_peak']:.1f} at {results['sync_position']:.3f}s)")

    if results["sync_detected"]:
        status_icon = "OK" if results["status"] == "OK" else "FAIL"
        print(f"  Bits: {results['bits_extracted']}/{TOTAL_EXPECTED_BITS}, Errors: {results['errors']} ({results['error_rate']:.1f}%)")
        print(f"  Decoded: '{results['decoded']}' [{status_icon}] {results['status']}")


def analyze_directory(dir_path):
    """Analyze all wav files in directory"""
    if not os.path.exists(dir_path):
        print(f"Directory not found: {dir_path}")
        return

    files = sorted([f for f in os.listdir(dir_path) if f.endswith('.wav')])

    if not files:
        print(f"No wav files in directory: {dir_path}")
        return

    print("=" * 60)
    print(f"Analyzing {len(files)} samples in {dir_path}")
    print("=" * 60)

    all_results = []
    for f in files:
        filepath = os.path.join(dir_path, f)
        _, audio = wavfile.read(filepath)
        if audio.ndim > 1:
            audio = audio[:, 0]
        results = analyze_signal(audio, f)
        print_results(results)
        all_results.append(results)

    # Statistics
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    total = len(all_results)
    ok = sum(1 for r in all_results if r["status"] == "OK")
    sync_ok = sum(1 for r in all_results if r["sync_detected"])
    avg_errors = np.mean([r["error_rate"] for r in all_results if r["bits_extracted"] > 0])

    print(f"  Total samples: {total}")
    print(f"  Sync detected: {sync_ok}/{total}")
    print(f"  Decoded correctly: {ok}/{total} ({100*ok/total:.1f}%)")
    print(f"  Average error rate: {avg_errors:.1f}%")


def main():
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.isdir(target):
            analyze_directory(target)
        elif os.path.isfile(target):
            _, audio = wavfile.read(target)
            if audio.ndim > 1:
                audio = audio[:, 0]
            results = analyze_signal(audio, os.path.basename(target))
            print_results(results)
        else:
            print(f"File not found: {target}")
    else:
        analyze_directory("samples")


if __name__ == "__main__":
    main()
