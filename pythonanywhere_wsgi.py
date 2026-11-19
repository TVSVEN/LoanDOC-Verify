"""WSGI entry point for PythonAnywhere's managed web server."""

from __future__ import annotations

import io
import os
from email.message import Message
from http import HTTPStatus
from pathlib import Path

# Keep the SQLite database and uploads outside the cloned source folder. The
# home directory is persistent on PythonAnywhere's free account.
os.environ.setdefault("DATA_DIR", str(Path.home() / "loandocverify-data"))

from app import Handler, init_db  # noqa: E402

init_db()


class _WSGIRequest(Handler):
    """Adapt one WSGI request to the existing HTTP request handlers."""

    def __init__(self, environ):
        self.command = environ.get("REQUEST_METHOD", "GET").upper()
        self.path = environ.get("PATH_INFO", "/") or "/"
        query = environ.get("QUERY_STRING", "")
        if query:
            self.path += "?" + query
        self.rfile = environ["wsgi.input"]
        self.wfile = io.BytesIO()
        self.headers = Message()
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                self.headers[key[5:].replace("_", "-")] = str(value)
        self.headers["Content-Type"] = environ.get("CONTENT_TYPE", "")
        self.headers["Content-Length"] = environ.get("CONTENT_LENGTH", "0") or "0"
        if environ.get("wsgi.url_scheme") == "https" and not self.headers.get("X-Forwarded-Proto"):
            self.headers["X-Forwarded-Proto"] = "https"
        self.status_code = 500
        self.response_headers = []

    def send_response(self, code, message=None):
        self.status_code = code

    def send_header(self, key, value):
        self.response_headers.append((key, value))

    def end_headers(self):
        pass


def application(environ, start_response):
    """WSGI application callable used by PythonAnywhere."""
    request = _WSGIRequest(environ)
    method = request.command
    if method in {"GET", "POST", "PUT", "DELETE"}:
        getattr(request, "do_" + method)()
    else:
        request.send({"error": "Method not allowed."}, 405)

    status = request.status_code
    try:
        phrase = HTTPStatus(status).phrase
    except ValueError:
        phrase = "Unknown Status"
    start_response(f"{status} {phrase}", request.response_headers)
    return [request.wfile.getvalue()]
