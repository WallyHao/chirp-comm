class AsyncInputStream:
    def __init__(self, fs, callback, device=None):
        self.fs = fs
        self.callback = callback
        self.device = device
        self.stream = None

    def start(self):
        import sounddevice as sd

        self.stream = sd.InputStream(
            samplerate=self.fs, device=self.device, channels=1, callback=self._internal_callback
        )
        self.stream.start()

    def _internal_callback(self, indata, frames, time, status):
        self.callback(indata[:, 0])

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
