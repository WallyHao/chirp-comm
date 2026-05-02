#!/usr/bin/env python3
"""
Transmit chirp signal in real-time

Usage:
    python transmit_live.py              # Transmit default message "ab"
    python transmit_live.py "HELLO"     # Transmit custom message
    python transmit_live.py --loop      # Loop transmission
"""
import argparse
import numpy as np
import sounddevice as sd
from chirp_comm.config import FS, PAUSE
from chirp_comm.dsp import REF_SYNC, REF_UP, REF_DOWN
from chirp_comm.protocol import ChirpProtocol


def generate_audio(text):
    """Generate chirp audio"""
    bits = ChirpProtocol.encode_to_bits(text)

    audio = [
        np.zeros(int(FS * 0.5)),
        REF_SYNC,
        np.zeros(int(FS * 0.1))
    ]

    for bit in bits:
        audio.append(REF_UP if bit == "1" else REF_DOWN)
        audio.append(np.zeros(int(FS * PAUSE)))

    audio.append(np.zeros(int(FS * 0.5)))
    return np.concatenate(audio).astype(np.float32)


def transmit(text, loop=False):
    """Transmit chirp signal"""
    audio = generate_audio(text)
    duration = len(audio) / FS

    print(f"Generated signal: '{text}'")
    print(f"Duration: {duration:.2f} seconds")

    if loop:
        print("Looping... Press Ctrl+C to stop")
        try:
            while True:
                print(f"\nTransmitting ({duration:.1f}s)...")
                sd.play(audio, FS)
                sd.wait()
        except KeyboardInterrupt:
            print("\nStopped")
    else:
        print("Transmitting...")
        sd.play(audio, FS)
        sd.wait()
        print("Done!")


def main():
    parser = argparse.ArgumentParser(description="Transmit chirp signal in real-time")
    parser.add_argument("message", nargs="?", default="ab", help="Message to transmit")
    parser.add_argument("--loop", "-l", action="store_true", help="Loop transmission")
    args = parser.parse_args()

    transmit(args.message, loop=args.loop)


if __name__ == "__main__":
    main()
