import sounddevice as sd

from src.config import SAMPLE_RATE, CHANNELS, BLOCK_SIZE


class Microphone:
    def __init__(self):
        self.stream = None

        # Use the operating system's current
        # default input device automatically.
        self.device = self._get_default_input_device()

    def _get_default_input_device(self):
        """Return a valid default input device."""

        default_device = sd.default.device

        if isinstance(
            default_device,
            (list, tuple),
        ):
            input_device = default_device[0]
        else:
            input_device = default_device

        try:
            input_device = int(
                input_device
            )

            device_info = sd.query_devices(
                input_device
            )

            if (
                device_info[
                    "max_input_channels"
                ] > 0
            ):
                return input_device

        except Exception:
            pass

        # Fallback: find the first device
        # that supports audio input.
        devices = sd.query_devices()

        for index, device in enumerate(
            devices
        ):
            if (
                device[
                    "max_input_channels"
                ] > 0
            ):
                return index

        raise RuntimeError(
            "No microphone input device found."
        )

    def start(self):
        """Start the microphone stream."""

        if self.stream is not None:
            return

        device_info = sd.query_devices(
            self.device
        )

        print(
            f"🎧 Using microphone: "
            f"[{self.device}] "
            f"{device_info['name']}"
        )

        print(
            "🎧 Available input channels: "
            f"{device_info['max_input_channels']}"
        )

        # Validate before opening the stream.
        sd.check_input_settings(
            device=self.device,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
        )

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            blocksize=BLOCK_SIZE,
            dtype="float32",
            device=self.device,
        )

        self.stream.start()

        print(
            "🎤 Microphone started."
        )

    def read(self):
        """Read one audio block."""

        if self.stream is None:
            raise RuntimeError(
                "Microphone is not started."
            )

        data, overflow = self.stream.read(
            BLOCK_SIZE
        )

        if overflow:
            print(
                "⚠ Audio overflow detected."
            )

        return data

    def stop(self):
        """Stop the microphone stream."""

        if self.stream is not None:

            self.stream.stop()
            self.stream.close()

            self.stream = None

            print(
                "🎤 Microphone stopped."
            )