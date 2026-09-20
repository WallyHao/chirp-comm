#!/usr/bin/env python3
"""
Smart home command trigger

Listen for chirp signals and execute corresponding actions.
This is a demo showing how to integrate chirp communication into real applications.

Usage:
    python automated_command_trigger.py
"""

import numpy as np
import sounddevice as sd
from scipy.signal import correlate

from chirp_comm.config import BIT_TOTAL_SAMPLES, FS, TOTAL_EXPECTED_BITS
from chirp_comm.dsp import REF_DOWN, REF_SYNC, REF_UP
from chirp_comm.protocol import ChirpProtocol


class SmartHomeController:
    """Smart home controller"""

    # Command mapping table
    COMMANDS = {
        "LIGHT_ON": "Turn on lights",
        "LIGHT_OFF": "Turn off lights",
        "FAN_ON": "Turn on fan",
        "FAN_OFF": "Turn off fan",
        "LOCK": "Lock door",
        "UNLOCK": "Unlock door",
        "ALARM": "Trigger alarm",
        "SILENT": "Silent mode",
    }

    def __init__(self):
        self.is_listening = False
        self.rx_buffer = np.array([])

    def handle_command(self, decoded):
        """Handle received command"""
        action = self.COMMANDS.get(decoded)
        if action:
            print(f"\n[CMD RECEIVED] >>> {decoded}")
            print(f"[ACTION] >>> {action}")
            self.execute_action(action)
        else:
            print(f"\n[UNKNOWN CMD] >>> {decoded}")

    def execute_action(self, action):
        """Execute specific action"""
        print(f"      [OK] Executed: {action}")

    def process_audio(self, audio):
        """Process audio data"""
        if len(audio) < len(REF_SYNC):
            return

        # Detect sync
        corr = correlate(audio, REF_SYNC, mode="valid")
        if len(corr) == 0 or np.max(corr) < 50:
            return

        peak_idx = np.argmax(corr)

        # Decode bits
        curr_ptr = peak_idx + len(REF_SYNC) + int(FS * 0.1)
        bits = ""

        for _ in range(TOTAL_EXPECTED_BITS):
            win_start = curr_ptr - int(BIT_TOTAL_SAMPLES * 0.1)
            win_end = curr_ptr + int(BIT_TOTAL_SAMPLES * 1.1)
            if win_end > len(audio):
                break
            seg = audio[win_start:win_end]
            c_up = correlate(seg, REF_UP, mode="valid")
            c_down = correlate(seg, REF_DOWN, mode="valid")
            bits += "1" if np.max(c_up) > np.max(c_down) else "0"
            curr_ptr = (
                win_start
                + (np.argmax(c_up) if np.max(c_up) > np.max(c_down) else np.argmax(c_down))
                + BIT_TOTAL_SAMPLES
            )

        if len(bits) >= TOTAL_EXPECTED_BITS:
            decoded = ChirpProtocol.decode_from_bits(bits)
            if decoded in self.COMMANDS:
                self.handle_command(decoded)

    def audio_callback(self, indata, frames, time, status):
        """Audio callback function"""
        if status:
            print(f"Audio status: {status}")
        self.rx_buffer = np.concatenate([self.rx_buffer, indata.flatten()])

        # Keep buffer size reasonable
        max_buffer = int(FS * 10)  # 10 seconds
        if len(self.rx_buffer) > max_buffer:
            self.rx_buffer = self.rx_buffer[-max_buffer:]

    def run(self):
        """Start listening"""
        print("=" * 60)
        print("Smart Home Command Trigger")
        print("=" * 60)
        print("\nAvailable commands:")
        for cmd, action in self.COMMANDS.items():
            print(f"  {cmd}: {action}")
        print("\nListening... Press Ctrl+C to stop")

        self.is_listening = True
        try:
            with sd.InputStream(
                samplerate=FS, channels=1, callback=self.audio_callback, blocksize=int(FS * 0.1)
            ):
                while self.is_listening:
                    sd.sleep(100)
        except KeyboardInterrupt:
            print("\nStopped listening")


if __name__ == "__main__":
    controller = SmartHomeController()
    controller.run()
