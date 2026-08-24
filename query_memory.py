from src.database.database import Database
from src.memory.embedding_service import EmbeddingService
from src.memory.retrieval_service import RetrievalService
from src.memory.memory_manager import MemoryManager


def display_results(results):
    """Display retrieved memories in a readable format."""

    if not results:
        print("\nNo matching memories found.\n")
        return

    print("\nRelevant memories:\n")

    for index, result in enumerate(results, start=1):

        print(f"{index}. {result['title']}")
        print(f"   {result['content']}")

        if result["date"]:
            print(f"   Date: {result['date']}")

        if result["time"]:
            print(f"   Time: {result['time']}")

        print(f"   Similarity: {result['score']:.3f}")
        print()


def main():

    print("=" * 50)
    print("EchoMind Memory Search")
    print("=" * 50)

    database = Database()

    embedding_service = EmbeddingService()

    retrieval_service = RetrievalService(
        database=database,
        embedding_service=embedding_service,
    )

    memory_manager = MemoryManager(
        database=database,
        embedding_service=embedding_service,
        retrieval_service=retrieval_service,
    )

    # Generate embeddings for older memories that were
    # stored before embedding support was added.
    updated_count = memory_manager.backfill_missing_embeddings()

    if updated_count:
        print(
            f"Prepared {updated_count} existing "
            f"memories for search."
        )

    try:

        while True:

            query = input(
                "\nAsk EchoMind (or type 'exit'): "
            ).strip()

            if query.lower() in {"exit", "quit"}:
                break

            if not query:
                continue

            results = retrieval_service.search(
                query,
                limit=5,
            )

            display_results(results)

    except KeyboardInterrupt:
        print()

    finally:
        database.close()

    print("Memory search stopped.")


if __name__ == "__main__":
    main()