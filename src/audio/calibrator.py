import time
import numpy as np

from src.config import CALIBRATION_DURATION, NOISE_MARGIN


class NoiseCalibrator:
    def __init__(self, microphone):
        self.microphone = microphone

    def calibrate(self):
        """
        Measure background noise and calculate
        an adaptive speech threshold.
        """

        print("Calibrating microphone...")
        print("Please remain quiet...\n")

        volumes = []

        start_time = time.time()

        while time.time() - start_time < CALIBRATION_DURATION:

            audio = self.microphone.read()

            volume = np.sqrt(np.mean(audio ** 2))

            volumes.append(volume)

        noise_level = np.median(volumes)

        threshold = noise_level + NOISE_MARGIN

        print(f"Noise Level      : {noise_level:.5f}")
        print(f"Speech Threshold : {threshold:.5f}")

        return threshold