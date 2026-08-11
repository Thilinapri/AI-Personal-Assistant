import queue
import sys
import threading
from datetime import datetime

from src.audio.microphone import Microphone
from src.audio.calibrator import NoiseCalibrator
from src.speech.listener import SpeechListener
from src.speech.whisper_model import WhisperService
from src.ai.keyword_filter import KeywordFilter
from src.ai.memory_engine import MemoryEngine
from src.ai.transcript_buffer import TranscriptBuffer
from src.database.database import Database
from src.worker.audio_worker import AudioWorker
from src.worker.session_processor import SessionProcessor


def configure_console_output():
    """Prevent unsupported console characters from stopping the application."""

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")


def shutdown_components(
    microphone,
    session_processor,
    audio_queue,
    worker_thread,
    database,
):
    """Stop workers before closing shared database and microphone resources."""

    # The listener loop has exited, so no additional microphone audio is queued.
    session_processor.stop()
    audio_queue.put(None)

    session_processor.join()
    worker_thread.join()

    database.close()
    microphone.stop()


def main():

    configure_console_output()

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

    transcript_buffer = TranscriptBuffer()

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
        transcript_buffer=transcript_buffer,
        keyword_filter=keyword_filter,
        memory_engine=memory_engine,
        database=database
    )

    worker_thread = threading.Thread(
        target=worker.run,
        daemon=True
    )

    worker_thread.start()

    session_processor = SessionProcessor(
        transcript_buffer=transcript_buffer,
        memory_engine=memory_engine,
        database=database,
    )
    session_processor.start()

    print("\n✅ Assistant Ready...\n")

    try:

        while True:

            audio = listener.listen()

            if audio is not None:

                audio_queue.put(audio)

    except KeyboardInterrupt:

        print("\nStopping Assistant...")

    finally:
        shutdown_components(
            microphone=microphone,
            session_processor=session_processor,
            audio_queue=audio_queue,
            worker_thread=worker_thread,
            database=database,
        )


if __name__ == "__main__":
    main()
