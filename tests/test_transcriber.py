from src.audio.calibrator import NoiseCalibrator
from src.speech.listener import SpeechListener
from src.speech.whisper_model import WhisperService

# Calibrate microphone
calibrator = NoiseCalibrator()
threshold = calibrator.calibrate()

# Initialize listener and Whisper
listener = SpeechListener(threshold)
whisper = WhisperService()

while True:

    audio = listener.listen()

    if audio is None:
        print("Program terminated.")
        break

    print("📝 Transcribing...")

    text = whisper.transcribe(audio)

    print(f"\nYou said: {text}\n")