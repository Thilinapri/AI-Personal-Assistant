import threading

from werkzeug.serving import make_server


class WebServer:
    """Run the EchoMind Flask dashboard in a background thread."""

    def __init__(
        self,
        app,
        host="127.0.0.1",
        port=5000,
    ):
        self.app = app
        self.host = host
        self.port = port

        self.server = make_server(
            self.host,
            self.port,
            self.app,
        )

        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
            name="WebServer",
        )

    def start(self):
        self.thread.start()

        print(
            f"🌐 EchoMind dashboard running at "
            f"http://{self.host}:{self.port}"
        )

    def stop(self):
        self.server.shutdown()

    def join(self):
        if self.thread.is_alive():
            self.thread.join()