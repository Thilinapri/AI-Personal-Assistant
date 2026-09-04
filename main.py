import queue
import sys
import threading

from src.audio.microphone import Microphone
from src.speech.whisper_model import WhisperService
from src.ai.keyword_filter import KeywordFilter
from src.ai.memory_engine import MemoryEngine
from src.ai.disabled_memory_engine import DisabledMemoryEngine
from src.ai.transcript_buffer import TranscriptBuffer
from src.database.database import Database
from src.config import ENABLE_GEMINI

from src.memory.memory_manager import MemoryManager
from src.memory.embedding_service import EmbeddingService
from src.memory.retrieval_service import RetrievalService
from src.memory.rule_based_relationship_classifier import RuleBasedRelationshipClassifier

from src.reminder.reminder_manager import ReminderManager

from src.worker.audio_worker import AudioWorker
from src.worker.continuous_transcriber import ContinuousTranscriber
from src.worker.session_processor import SessionProcessor
from src.worker.reminder_worker import ReminderWorker

from web.app import create_app
from web.server import WebServer


def configure_console_output():
    """Prevent unsupported console characters from stopping the application."""

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")


def shutdown_components(
    microphone,
    continuous_transcriber,
    session_processor,
    reminder_worker,
    web_server,
    audio_queue,
    worker,
    worker_thread,
    database,
):
    """Stop all workers before closing shared resources."""

    print("\nStopping Assistant...")

    # Stop microphone capture first.
    continuous_transcriber.stop()
    continuous_transcriber.join()

    # Stop periodic session processing.
    session_processor.stop()

    # Prevent AudioWorker from processing any more queued audio.
    worker.stop()

    # Remove any audio chunks that are still waiting.
    while True:
        try:
            audio_queue.get_nowait()
            audio_queue.task_done()
        except queue.Empty:
            break

    # Wake AudioWorker and tell it to exit.
    audio_queue.put(None)

    # Wait for workers to finish.
    session_processor.join()
    worker_thread.join()

    # Stop reminder checking before closing the database.
    reminder_worker.stop()
    reminder_worker.join()

    # Stop the dashboard before closing the shared database.
    web_server.stop()
    web_server.join()

    # Close shared resources last.
    database.close()
    microphone.stop()

    print("Assistant stopped.")


def main():

    configure_console_output()

    print("=" * 50)
    print("AI Personal Assistant")
    print("=" * 50)

    # ---------------------------------
    # Database
    # ---------------------------------

    database = Database()

    # ---------------------------------
    # Local Memory AI Components
    # ---------------------------------

    embedding_service = EmbeddingService()

    retrieval_service = RetrievalService(
        database=database,
        embedding_service=embedding_service,
    )

    relationship_classifier = RuleBasedRelationshipClassifier()

    # ---------------------------------
    # Reminder Manager
    # ---------------------------------

    reminder_manager = ReminderManager(
        database=database,
    )

    # ---------------------------------
    # Memory Manager
    # ---------------------------------

    memory_manager = MemoryManager(
        database=database,
        embedding_service=embedding_service,
        retrieval_service=retrieval_service,
        relationship_classifier=relationship_classifier,
        reminder_manager=reminder_manager,
    )

    # ---------------------------------
    # Prepare Existing Memories
    # ---------------------------------

    try:
        backfilled_count = memory_manager.backfill_missing_embeddings()

        if backfilled_count > 0:
            print(
                f"🧠 Prepared {backfilled_count} existing "
                "memories for semantic search."
            )

    except Exception as error:
        print(
            f"Memory embedding backfill failed: {error}"
        )

    # ---------------------------------
    # Reminder Worker
    # ---------------------------------

    reminder_worker = ReminderWorker(
        reminder_manager=reminder_manager,
        check_interval=30,
    )

    reminder_worker.start()

    # ---------------------------------
    # Microphone
    # ---------------------------------

    microphone = Microphone()
    microphone.start()

    # ---------------------------------
    # AI Components
    # ---------------------------------

    whisper = WhisperService()

    keyword_filter = KeywordFilter()

    transcript_buffer = TranscriptBuffer()

    if ENABLE_GEMINI:
        memory_engine = MemoryEngine()
        print("🤖 Gemini memory processing enabled.")
    else:
        memory_engine = DisabledMemoryEngine()
        print("🤖 Gemini memory processing disabled.")

    # ---------------------------------
    # Audio Queue
    # ---------------------------------

    audio_queue = queue.Queue()

    # ---------------------------------
    # Audio Worker
    # ---------------------------------

    worker = AudioWorker(
        audio_queue=audio_queue,
        whisper=whisper,
        transcript_buffer=transcript_buffer,
        keyword_filter=keyword_filter,
        memory_engine=memory_engine,
        memory_manager=memory_manager,
    )

    worker_thread = threading.Thread(
        target=worker.run,
        daemon=True,
        name="AudioWorker",
    )

    worker_thread.start()

    # ---------------------------------
    # Continuous Transcriber
    # ---------------------------------

    continuous_transcriber = ContinuousTranscriber(
        microphone=microphone,
        audio_queue=audio_queue,
        database=database,
    )

    continuous_transcriber.start()

    # ---------------------------------
    # Session Processor
    # ---------------------------------

    session_processor = SessionProcessor(
        transcript_buffer=transcript_buffer,
        memory_engine=memory_engine,
        memory_manager=memory_manager,
    )

    session_processor.start()

    # ---------------------------------
    # Web Dashboard
    # ---------------------------------

    web_app = create_app(
        database=database,
        embedding_service=embedding_service,
        retrieval_service=retrieval_service,
        reminder_manager=reminder_manager,
        memory_manager=memory_manager,
    )

    web_server = WebServer(
        app=web_app,
        host="127.0.0.1",
        port=5000,
    )

    web_server.start()

    print()
    print("✅ Assistant Ready")
    print("🎧 Continuously listening...")
    print()

    # ---------------------------------
    # Main Loop
    # ---------------------------------

    try:

        while True:
            threading.Event().wait(1)

    except KeyboardInterrupt:
        pass

    finally:

        shutdown_components(
            microphone=microphone,
            continuous_transcriber=continuous_transcriber,
            session_processor=session_processor,
            reminder_worker=reminder_worker,
            web_server=web_server,
            audio_queue=audio_queue,
            worker=worker,
            worker_thread=worker_thread,
            database=database,
        )


if __name__ == "__main__":
    main()