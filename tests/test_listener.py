from src.audio.calibrator import NoiseCalibrator
from src.speech.listener import SpeechListener

calibrator = NoiseCalibrator()
threshold = calibrator.calibrate()

listener = SpeechListener(threshold)

while True:

    audio = listener.listen()

    if audio is None:
        print("Program terminated.")
        break

    print(audio.shape)