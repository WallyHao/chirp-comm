import queue
import threading

import sounddevice as sd

from .config import FS
from .dsp import create_audio_payload


class ChirpSender:
    def __init__(self, device=None):
        self.device = device
        self.task_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        while not self.stop_event.is_set():
            try:
                payload = self.task_queue.get(timeout=0.5)
                sd.play(payload, samplerate=FS, device=self.device)
                sd.wait()
                self.task_queue.task_done()
            except queue.Empty:
                continue

    def send(self, text):
        self.task_queue.put(create_audio_payload(text))

    def stop(self):
        self.stop_event.set()
        self.thread.join()

    @staticmethod
    def list_devices():
        return sd.query_devices()
