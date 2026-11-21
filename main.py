
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

from src.cloud.reminder_sync_client import (
    CloudReminderSyncClient,
)

from src.worker.audio_worker import AudioWorker
from src.worker.audio_chunker import AudioChunker
from src.worker.session_processor import SessionProcessor
from src.worker.reminder_worker import ReminderWorker

# EchoMind TFT display
from src.display.display_controller import DisplayWorker

from web.app import create_app
from web.server import WebServer


# ==========================================
# Console Configuration
# ==========================================

def configure_console_output():
    """Configure clean console output."""

    for stream in (
        sys.stdout,
        sys.stderr,
    ):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(
                errors="backslashreplace"
            )

    # Hide normal Flask/Werkzeug HTTP request logs.
    logging.getLogger(
        "werkzeug"
    ).setLevel(
        logging.ERROR
    )


# ==========================================
# Shutdown Components
# ==========================================

def shutdown_components(
    microphone,
    audio_chunker,
    session_processor,
    reminder_worker,
    display_worker,
    web_server,
    audio_queue,
    worker,
    worker_thread,
    database,
):
    """Stop workers safely before closing shared resources."""

    print("\nStopping Assistant...")
    failures = []

    def stop_component(name, stop_function):
        try:
            stop_function()
            print(f"Stopped request sent: {name}")
        except Exception as error:
            failures.append(name)
            print(f"Shutdown error ({name}): {error}")

    def join_component(name, join_function, is_alive, timeout):
        try:
            join_function(timeout)
            if is_alive():
                failures.append(name)
                print(
                    f"WARNING: {name} did not stop "
                    f"within {timeout} seconds."
                )
            else:
                print(f"Stopped: {name}")
        except Exception as error:
            failures.append(name)
            print(f"Shutdown error ({name}): {error}")

    # 1. Stop audio collection and unblock microphone reads.
    stop_component("Audio chunker", audio_chunker.stop)
    stop_component("Microphone", microphone.stop)

    join_component(
        "Audio chunker",
        audio_chunker.join,
        lambda: (
            audio_chunker._thread is not None
            and audio_chunker._thread.is_alive()
        ),
        10,
    )

    # 2. Stop audio processing and discard queued, unprocessed audio.
    stop_component("Audio worker", worker.stop)

    try:
        while True:
            audio_queue.get_nowait()
            audio_queue.task_done()
    except queue.Empty:
        pass
    except Exception as error:
        failures.append("Audio queue")
        print(f"Shutdown error (Audio queue): {error}")

    try:
        audio_queue.put_nowait(None)
    except Exception as error:
        failures.append("Audio worker signal")
        print(f"Shutdown error (Audio worker signal): {error}")

    join_component(
        "Audio worker",
        worker_thread.join,
        worker_thread.is_alive,
        30,
    )

    # 3. Stop session processing.
    stop_component("Session processor", session_processor.stop)

    join_component(
        "Session processor",
        session_processor.join,
        lambda: (
            session_processor._thread is not None
            and session_processor._thread.is_alive()
        ),
        30,
    )

    # 4. Stop workers that may use the database or display hardware.
    stop_component("Reminder worker", reminder_worker.stop)

    join_component(
        "Reminder worker",
        reminder_worker.join,
        reminder_worker.is_alive,
        10,
    )

    stop_component("Display worker", display_worker.stop)

    join_component(
        "Display worker",
        display_worker.join,
        display_worker.is_alive,
        10,
    )

    # 5. Stop the dashboard server without changing its implementation.
    stop_component("Web server", web_server.stop)

    join_component(
        "Web server",
        lambda timeout: web_server.thread.join(timeout=timeout),
        web_server.thread.is_alive,
        10,
    )

    # 6. Never close the database while a worker may still use it.
    if failures:
        print(
            "WARNING: Some components did not shut down cleanly: "
            + ", ".join(failures)
        )
        print(
            "Database left open until process exit to protect "
            "against concurrent access."
        )
    else:
        try:
            database.close()
            print("Database closed.")
        except Exception as error:
            print(f"Database close failed: {error}")

    print("Assistant shutdown sequence finished.")


# ==========================================
# Main Application
# ==========================================

def main():

    configure_console_output()

    print("=" * 50)
    print("AI Personal Assistant")
    print("=" * 50)

    # --------------------------------------
    # Database
    # --------------------------------------

    database = Database()

    # --------------------------------------
    # Local Memory AI Components
    # --------------------------------------

    embedding_service = EmbeddingService()

    # --------------------------------------
    # Context Selection
    # --------------------------------------

    context_selector = ContextSelector(
        embedding_service=embedding_service,
    )

    # --------------------------------------
    # Optional Privacy Components
    # --------------------------------------

    privacy_gateway = None
    semantic_privacy_classifier = None

    if ENABLE_PRIVACY_GATEWAY:

        if ENABLE_SEMANTIC_PRIVACY:
            semantic_privacy_classifier = (
                SemanticPrivacyClassifier(
                    embedding_service=embedding_service,
                )
            )

        privacy_gateway = PrivacyGateway(
            context_selector=context_selector,
            semantic_classifier=semantic_privacy_classifier,
        )

        print("🔒 Privacy Gateway enabled.")

        if ENABLE_SEMANTIC_PRIVACY:
            print("🧠 Semantic privacy screening enabled.")
        else:
            print("🧠 Semantic privacy screening disabled.")

    else:

        print("🔓 Privacy Gateway disabled.")

        if ENABLE_SEMANTIC_PRIVACY:
            print(
                "⚠️ Semantic privacy setting ignored "
                "because Privacy Gateway is disabled."
            )

    # --------------------------------------
    # Retrieval
    # --------------------------------------

    retrieval_service = RetrievalService(
        database=database,
        embedding_service=embedding_service,
    )

    relationship_classifier = (
        RuleBasedRelationshipClassifier()
    )

    # --------------------------------------
    # Optional Cloud Reminder Sync
    # --------------------------------------

    cloud_sync_client = None

    try:

        cloud_sync_client = CloudReminderSyncClient()

        print("☁️ Cloud reminder sync enabled.")

    except Exception as error:

        # EchoMind must continue working locally
        # even when cloud synchronization is unavailable.
        print(
            "☁️ Cloud reminder sync disabled: "
            f"{error}"
        )

    # --------------------------------------
    # Reminder Manager
    # --------------------------------------

    reminder_manager = ReminderManager(
        database=database,
        cloud_sync_client=cloud_sync_client,
    )

    # --------------------------------------
    # Memory Manager
    # --------------------------------------

    memory_manager = MemoryManager(
        database=database,
        embedding_service=embedding_service,
        retrieval_service=retrieval_service,
        relationship_classifier=relationship_classifier,
        reminder_manager=reminder_manager,
    )

    # --------------------------------------
    # Prepare Existing Memories
    # --------------------------------------

    try:

        backfilled_count = (
            memory_manager.backfill_missing_embeddings()
        )

        if backfilled_count > 0:
            print(
                f"🧠 Prepared {backfilled_count} existing "
                "memories for semantic search."
            )

    except Exception as error:

        print(
            "Memory embedding backfill failed: "
            f"{error}"
        )

    # --------------------------------------
    # Reminder Worker
    # --------------------------------------

    reminder_worker = ReminderWorker(
        reminder_manager=reminder_manager,
        check_interval=30,
    )

    reminder_worker.start()

    # --------------------------------------
    # TFT Display Worker
    # --------------------------------------

    display_worker = DisplayWorker(
        database=database,
        refresh_interval=5,
    )

    display_worker.start()

    # --------------------------------------
    # Microphone
    # --------------------------------------

    microphone = Microphone()
    microphone.start()

    # --------------------------------------
    # AI Components
    # --------------------------------------

    # AssemblyAI is used for speech-to-text.
    stt_service = AssemblyAIService()

    keyword_filter = KeywordFilter()

    transcript_buffer = TranscriptBuffer()

    if ENABLE_GEMINI:

        memory_engine = MemoryEngine(
            privacy_gateway=privacy_gateway,
            context_selector=context_selector,
        )

        print("🤖 Gemini memory processing enabled.")

    else:

        memory_engine = DisabledMemoryEngine()

        print("🤖 Gemini memory processing disabled.")

    # --------------------------------------
    # Audio Queue
    # --------------------------------------

    audio_queue = queue.Queue(
        maxsize=2
    )

    # --------------------------------------
    # Audio Worker
    # --------------------------------------

    worker = AudioWorker(
        audio_queue=audio_queue,
        stt_service=stt_service,
        transcript_buffer=transcript_buffer,
        keyword_filter=keyword_filter,
        memory_engine=memory_engine,
        memory_manager=memory_manager,
        transcript_callback=display_worker.update_transcript,
    )

    worker_thread = threading.Thread(
        target=worker.run,
        daemon=True,
        name="AudioWorker",
    )

    worker_thread.start()

    # --------------------------------------
    # Audio Chunker
    # --------------------------------------

    audio_chunker = AudioChunker(
        microphone=microphone,
        audio_queue=audio_queue,
        database=database,
    )

    audio_chunker.start()

    # --------------------------------------
    # Session Processor
    # --------------------------------------

    # Keep the normal SessionProcessor interval unchanged.
    session_processor = SessionProcessor(
        transcript_buffer=transcript_buffer,
        memory_engine=memory_engine,
        memory_manager=memory_manager,
    )

    session_processor.start()

    # --------------------------------------
    # Web Dashboard
    # --------------------------------------

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

    # --------------------------------------
    # Ready
    # --------------------------------------

    print()
    print("✅ Assistant Ready")
    print("🎧 Continuously listening...")
    print("🖥️ EchoMind TFT display running.")
    print()

    # --------------------------------------
    # Main Loop
    # --------------------------------------

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
            display_worker=display_worker,
            web_server=web_server,
            audio_queue=audio_queue,
            worker=worker,
            worker_thread=worker_thread,
            database=database,
        )


if __name__ == "__main__":
    main()
