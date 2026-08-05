from src.audio.calibrator import NoiseCalibrator

calibrator = NoiseCalibrator()

threshold = calibrator.calibrate()

print(f"\nFinal Threshold = {threshold:.5f}")