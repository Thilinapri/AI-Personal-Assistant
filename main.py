import queue
import threading
from datetime import datetime

from src.audio.microphone import Microphone
from src.audio.calibrator import NoiseCalibrator
from src.speech.listener import SpeechListener
from src.speech.whisper_model import WhisperService
from src.ai.keyword_filter import KeywordFilter
from src.ai.memory_engine import MemoryEngine
from src.database.database import Database
from src.worker.audio_worker import AudioWorker


def main():

    print("=" * 50)
    print("AI Personal Memory Assistant")
    print("=" * 50)

    # ---------------------------------
    # Initialize microphone
    # ---------------------------------

    microphone = Microphone()

    print("Starting microphone...")
    microphone.start()

    # ---------------------------------
    # Noise Calibration
    # ---------------------------------

    print("Calibrating background noise...")

    calibrator = NoiseCalibrator(microphone)

    threshold = calibrator.calibrate()

    print(f"Noise Threshold : {threshold:.5f}")

    # ---------------------------------
    # Listener
    # ---------------------------------

    listener = SpeechListener(
        microphone=microphone,
        threshold=threshold
    )

    # ---------------------------------
    # AI Components
    # ---------------------------------

    whisper = WhisperService()

    keyword_filter = KeywordFilter()

    memory_engine = MemoryEngine()

    database = Database()

    # ---------------------------------
    # Audio Queue
    # ---------------------------------

    audio_queue = queue.Queue()

    # ---------------------------------
    # Worker
    # ---------------------------------

    worker = AudioWorker(
        audio_queue=audio_queue,
        whisper=whisper,
        keyword_filter=keyword_filter,
        memory_engine=memory_engine,
        database=database
    )

    worker_thread = threading.Thread(
        target=worker.run,
        daemon=True
    )

    worker_thread.start()

    print("\n✅ Assistant Ready...\n")

    try:

        while True:

            audio = listener.listen()

            if audio is not None:

                audio_queue.put(audio)

    except KeyboardInterrupt:

        print("\nStopping Assistant...")

    finally:

        audio_queue.put(None)

        worker_thread.join(timeout=2)

        database.close()

        microphone.stop()


if __name__ == "__main__":
    main()