import time
import numpy as np

from src.config import (
    CALIBRATION_DURATION,
    CONTINUE_NOISE_MULTIPLIER,
    CONTINUE_SIGMA_MULTIPLIER,
    MIN_CONTINUE_RMS,
    MIN_START_RMS,
    START_NOISE_MULTIPLIER,
    START_SIGMA_MULTIPLIER,
)


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

        return self.create_noise_profile(volumes)

    @staticmethod
    def create_noise_profile(volumes):
        """Build start and continuation thresholds from calibration RMS values."""

        volume_array = np.asarray(volumes, dtype=float)
        noise_floor = float(np.median(volume_array))
        noise_mad = float(np.median(np.abs(volume_array - noise_floor)))
        noise_sigma = 1.4826 * noise_mad

        start_threshold = max(
            noise_floor * START_NOISE_MULTIPLIER,
            noise_floor + START_SIGMA_MULTIPLIER * noise_sigma,
            MIN_START_RMS,
        )
        continue_threshold = max(
            noise_floor * CONTINUE_NOISE_MULTIPLIER,
            noise_floor + CONTINUE_SIGMA_MULTIPLIER * noise_sigma,
            MIN_CONTINUE_RMS,
        )

        profile = {
            "noise_floor": noise_floor,
            "noise_sigma": noise_sigma,
            "start_threshold": start_threshold,
            "continue_threshold": continue_threshold,
        }

        print(f"Noise Floor              : {noise_floor:.5f}")
        print(f"Noise Sigma              : {noise_sigma:.5f}")
        print(f"Speech Start Threshold   : {start_threshold:.5f}")
        print(f"Speech Continue Threshold: {continue_threshold:.5f}")

        return profile
