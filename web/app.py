from flask import Flask, jsonify, render_template, request

from src.database.database import Database
from src.memory.embedding_service import EmbeddingService
from src.memory.retrieval_service import RetrievalService


def create_app():
    app = Flask(__name__)

    database = Database()

    embedding_service = EmbeddingService()

    retrieval_service = RetrievalService(
        database,
        embedding_service,
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
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False,
    )