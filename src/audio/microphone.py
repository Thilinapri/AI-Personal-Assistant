import sounddevice as sd

from src.config import SAMPLE_RATE, CHANNELS, BLOCK_SIZE


class Microphone:
    def __init__(self):
        self.stream = None

        # Device 3 was tested successfully and captured your voice.
        self.device = 3

    def start(self):
        """Start the microphone stream."""

        if self.stream is None:
            device_info = sd.query_devices(self.device)

            print(
                f"🎧 Using microphone: [{self.device}] "
                f"{device_info['name']}"
            )

            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                blocksize=BLOCK_SIZE,
                dtype="float32",
                device=self.device,
            )

            self.stream.start()

            print("🎤 Microphone started.")

    def read(self):
        """Read one audio block."""

        if self.stream is None:
            raise RuntimeError("Microphone is not started.")

        data, overflow = self.stream.read(BLOCK_SIZE)

        if overflow:
            print("⚠ Audio overflow detected.")

        return data

    def stop(self):
        """Stop the microphone stream."""

        if self.stream is not None:
            self.stream.stop()
            self.stream.close()

            self.stream = None

            print("🎤 Microphone stopped.")