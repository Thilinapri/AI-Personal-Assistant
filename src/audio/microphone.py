
import sounddevice as sd

from src.config import SAMPLE_RATE, CHANNELS, BLOCK_SIZE


class Microphone:
    """Capture microphone audio using the system's default input device."""

    def __init__(self):
        self.device = self._get_default_input_device()
        self.stream = None

    def _get_default_input_device(self):
        """Select the operating system's default input device."""

        default_device = sd.default.device

        # sounddevice may return an InputOutputPair object.
        input_device = default_device[0]

        if input_device is None or int(input_device) < 0:
            raise RuntimeError(
                "No default microphone input device found."
            )

        input_device = int(input_device)
        device_info = sd.query_devices(input_device)

        if device_info["max_input_channels"] <= 0:
            raise RuntimeError(
                "The default device does not support audio input."
            )

        print(
            f"Using microphone: [{input_device}] "
            f"{device_info['name']}"
        )

        print(
            f"Available input channels: "
            f"{device_info['max_input_channels']}"
        )

        return input_device

    def start(self):
        """Start microphone audio capture."""

        if self.stream is not None:
            return

        self.stream = sd.InputStream(
            device=self.device,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            blocksize=BLOCK_SIZE,
            dtype="float32"
        )

        self.stream.start()
        print("Microphone started.")

    def read(self):
        """Read one block of microphone audio."""

        if self.stream is None:
            raise RuntimeError(
                "Microphone is not started. Call start() first."
            )

        data, overflow = self.stream.read(BLOCK_SIZE)

        if overflow:
            print("⚠ Audio overflow detected.")

        return data

    def stop(self):
        """Stop and close microphone audio capture."""

        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        print("Microphone stopped.")
