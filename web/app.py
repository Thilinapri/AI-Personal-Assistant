from flask import Flask, jsonify, render_template, request

from src.database.database import Database
from src.memory.embedding_service import EmbeddingService
from src.memory.memory_manager import MemoryManager
from src.memory.retrieval_service import RetrievalService
from src.reminder.reminder_manager import ReminderManager


def create_app(
    database=None,
    embedding_service=None,
    retrieval_service=None,
    reminder_manager=None,
    memory_manager=None,
):
    app = Flask(__name__)

    # If the dashboard is started by itself,
    # create its required services normally.
    if database is None:
        database = Database()

    if embedding_service is None:
        embedding_service = EmbeddingService()

    if retrieval_service is None:
        retrieval_service = RetrievalService(
            database=database,
            embedding_service=embedding_service,
        )

    if reminder_manager is None:
        reminder_manager = ReminderManager(
            database=database,
        )

    if memory_manager is None:
        memory_manager = MemoryManager(
            database=database,
            embedding_service=embedding_service,
            retrieval_service=retrieval_service,
            reminder_manager=reminder_manager,
        )

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/status")
    def status():
        try:
            database.connection.execute("SELECT 1")
            database_status = "connected"

        except Exception:
            database_status = "error"

        listening_enabled = (
            database.get_listening_enabled()
        )

        return jsonify(
            {
                "application": "EchoMind",
                "web": "running",
                "database": database_status,
                "listening": (
                    "active"
                    if listening_enabled
                    else "paused"
                ),
            }
        )

    @app.route(
        "/api/listening",
        methods=["POST"],
    )
    def update_listening():

        data = request.get_json(silent=True) or {}

        enabled = data.get("enabled")

        if not isinstance(enabled, bool):
            return jsonify(
                {
                    "error":
                        "enabled must be true or false"
                }
            ), 400

        database.set_listening_enabled(enabled)

        return jsonify(
            {
                "success": True,
                "listening": (
                    "active"
                    if enabled
                    else "paused"
                ),
            }
        )

    @app.route("/api/memories")
    def memories():
        rows = database.get_active_memories()

        result = []

        for row in rows:
            result.append(
                {
                    "id": row[0],
                    "category": row[1],
                    "title": row[2],
                    "content": row[3],
                    "date": row[4],
                    "time": row[5],
                    "notification": bool(row[6]),
                    "status": row[9],
                    "seen_count": row[12],
                }
            )

        return jsonify(result)

    @app.route("/api/memories", methods=["DELETE"])
    def clear_memories():
        database.delete_all_memories()

        return jsonify(
            {
                "success": True,
                "message": "All memories deleted.",
            }
        )

    @app.route("/api/memories/<int:memory_id>", methods=["DELETE"])
    def delete_memory(memory_id):
        database.delete_memory(memory_id)

        return jsonify(
            {
                "success": True,
                "memory_id": memory_id,
            }
        )

    @app.route(
        "/api/memories/<int:memory_id>",
        methods=["PUT"],
    )
    def update_memory(memory_id):

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify(
                {
                    "error": "JSON body is required."
                }
            ), 400

        required_fields = {
            "category",
            "title",
            "content",
            "date",
            "time",
            "notification",
        }

        missing = required_fields - data.keys()

        if missing:
            return jsonify(
                {
                    "error":
                        "Missing fields: "
                        + ", ".join(sorted(missing))
                }
            ), 400

        if (
            not isinstance(data["category"], str)
            or not data["category"].strip()
        ):
            return jsonify(
                {"error": "Category is required."}
            ), 400

        if (
            not isinstance(data["title"], str)
            or not data["title"].strip()
        ):
            return jsonify(
                {"error": "Title is required."}
            ), 400

        if (
            not isinstance(data["content"], str)
            or not data["content"].strip()
        ):
            return jsonify(
                {"error": "Content is required."}
            ), 400

        if not isinstance(data["notification"], bool):
            return jsonify(
                {
                    "error":
                        "notification must be true or false."
                }
            ), 400

        updated = memory_manager.update_memory(
            memory_id,
            data,
        )

        if not updated:
            return jsonify(
                {
                    "error":
                        "Active memory not found."
                }
            ), 404

        return jsonify(
            {
                "success": True,
                "memory_id": memory_id,
            }
        )

    @app.route("/api/reminders")
    def reminders():
        rows = database.get_all_reminders()

        result = []

        for row in rows:
            result.append(
                {
                    "id": row[0],
                    "memory_id": row[1],
                    "reminder_time": row[2],
                    "status": row[3],
                    "created_at": row[4],
                    "triggered_at": row[5],
                    "title": row[6],
                    "content": row[7],
                }
            )

        return jsonify(result)

    @app.route("/api/memories/search")
    def search_memories():
        query = request.args.get("q", "").strip()

        if not query:
            return jsonify([])

        results = retrieval_service.search(
            query,
            limit=5,
        )

        return jsonify(results)

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
    )