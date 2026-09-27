import logging
import queue
import sys
import threading

from src.audio.microphone import Microphone

# Speech-to-text
from src.speech.assemblyai_service import AssemblyAIService

from src.ai.keyword_filter import KeywordFilter
from src.ai.memory_engine import MemoryEngine
from src.ai.disabled_memory_engine import DisabledMemoryEngine
from src.ai.transcript_buffer import TranscriptBuffer

from src.database.database import Database

from src.config import (
    ENABLE_GEMINI,
    ENABLE_PRIVACY_GATEWAY,
    ENABLE_SEMANTIC_PRIVACY,
)

from src.memory.memory_manager import MemoryManager
from src.memory.embedding_service import EmbeddingService
from src.memory.retrieval_service import RetrievalService
from src.memory.rule_based_relationship_classifier import (
    RuleBasedRelationshipClassifier,
)

from src.privacy.context_selector import ContextSelector
from src.privacy.privacy_gateway import PrivacyGateway
from src.privacy.semantic_privacy_classifier import (
    SemanticPrivacyClassifier,
)

from src.reminder.reminder_manager import ReminderManager

from src.worker.audio_worker import AudioWorker
from src.worker.audio_chunker import AudioChunker
from src.worker.session_processor import SessionProcessor
from src.worker.reminder_worker import ReminderWorker

from web.app import create_app
from web.server import WebServer


def configure_console_output():
    """Configure clean console output."""

    for stream in (
        sys.stdout,
        sys.stderr,
    ):
        if hasattr(
            stream,
            "reconfigure",
        ):
            stream.reconfigure(
                errors="backslashreplace"
            )

    # Hide normal Flask/Werkzeug HTTP request logs.
    logging.getLogger(
        "werkzeug"
    ).setLevel(
        logging.ERROR
    )


def shutdown_components(
    microphone,
    audio_chunker,
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

    # Stop microphone/audio collection first.
    audio_chunker.stop()
    audio_chunker.join()

    # Stop periodic session processing.
    session_processor.stop()

    # Prevent AudioWorker from processing more audio.
    worker.stop()

    # Remove audio chunks still waiting.
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

    # Stop reminder checking before closing database.
    reminder_worker.stop()
    reminder_worker.join()

    # Stop dashboard before closing shared database.
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

    # ---------------------------------
    # Context Selection
    # ---------------------------------

    context_selector = ContextSelector(
        embedding_service=embedding_service,
    )

    # ---------------------------------
    # Optional Privacy Components
    # ---------------------------------

    privacy_gateway = None
    semantic_privacy_classifier = None

    if ENABLE_PRIVACY_GATEWAY:

        if ENABLE_SEMANTIC_PRIVACY:
            semantic_privacy_classifier = (
                SemanticPrivacyClassifier(
                    embedding_service=(
                        embedding_service
                    ),
                )
            )

        privacy_gateway = PrivacyGateway(
            context_selector=(
                context_selector
            ),
            semantic_classifier=(
                semantic_privacy_classifier
            ),
        )

        print(
            "🔒 Privacy Gateway enabled."
        )

        if ENABLE_SEMANTIC_PRIVACY:
            print(
                "🧠 Semantic privacy screening enabled."
            )
        else:
            print(
                "🧠 Semantic privacy screening disabled."
            )

    else:

        print(
            "🔓 Privacy Gateway disabled."
        )

        if ENABLE_SEMANTIC_PRIVACY:
            print(
                "⚠️ Semantic privacy setting ignored "
                "because Privacy Gateway is disabled."
            )

    # ---------------------------------
    # Retrieval
    # ---------------------------------

    retrieval_service = RetrievalService(
        database=database,
        embedding_service=embedding_service,
    )

    relationship_classifier = (
        RuleBasedRelationshipClassifier()
    )

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
        relationship_classifier=(
            relationship_classifier
        ),
        reminder_manager=reminder_manager,
    )

    # ---------------------------------
    # Prepare Existing Memories
    # ---------------------------------

    try:
        backfilled_count = (
            memory_manager
            .backfill_missing_embeddings()
        )

        if backfilled_count > 0:
            print(
                f"🧠 Prepared "
                f"{backfilled_count} existing "
                "memories for semantic search."
            )

    except Exception as error:
        print(
            "Memory embedding backfill failed: "
            f"{error}"
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

    # AssemblyAI is now used for speech-to-text.
    stt_service = AssemblyAIService()

    keyword_filter = KeywordFilter()

    transcript_buffer = TranscriptBuffer()

    if ENABLE_GEMINI:

        memory_engine = MemoryEngine(
            privacy_gateway=privacy_gateway,
            context_selector=context_selector,
        )

        print(
            "🤖 Gemini memory processing enabled."
        )

    else:

        memory_engine = DisabledMemoryEngine()

        print(
            "🤖 Gemini memory processing disabled."
        )

    # ---------------------------------
    # Audio Queue
    # ---------------------------------

    audio_queue = queue.Queue(
        maxsize=2
    )

    # ---------------------------------
    # Audio Worker
    # ---------------------------------

    worker = AudioWorker(
        audio_queue=audio_queue,
        stt_service=stt_service,
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
    # Audio Chunker
    # ---------------------------------

    audio_chunker = AudioChunker(
        microphone=microphone,
        audio_queue=audio_queue,
        database=database,
    )

    audio_chunker.start()

    # ---------------------------------
    # Session Processor
    # ---------------------------------

    # Keep the normal SessionProcessor
    # interval unchanged.
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
            audio_chunker=audio_chunker,
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