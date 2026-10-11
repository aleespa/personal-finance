import argparse
import socket
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from personal_finance.api.routes import router
from personal_finance.api.store import WorkbookStore
from personal_finance.paths import PROJECT_ROOT

FRONTEND_DIR = PROJECT_ROOT / "web" / "dist" / "web" / "browser"


def create_app(frontend_dir: Optional[Path] = FRONTEND_DIR) -> FastAPI:
    app = FastAPI(title="Personal Finance")
    app.state.store = WorkbookStore()
    app.include_router(router, prefix="/api")
    _mount_frontend(app, frontend_dir)
    return app


def _mount_frontend(app: FastAPI, frontend_dir: Optional[Path]) -> None:
    if frontend_dir is None or not (frontend_dir / "index.html").is_file():
        @app.get("/", include_in_schema=False)
        def frontend_missing():
            return HTMLResponse(
                "<p>The web UI has not been built. Run <code>npm ci</code> and "
                "<code>npm run build</code> in <code>web/</code>, then restart.</p>"
            )
        return

    root = frontend_dir.resolve()

    # Registered after the API router, so it only sees paths the API didn't
    # match. Real files are served as-is; anything else gets index.html so
    # Angular's router can handle deep links like /accounts.
    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path == "api" or path.startswith("api/"):
            raise HTTPException(404)
        file = (root / path).resolve()
        if path and file.is_file() and file.is_relative_to(root):
            return FileResponse(file)
        return FileResponse(root / "index.html")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the personal finance web UI.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true", help="don't open a browser tab")
    args = parser.parse_args()

    host = "127.0.0.1"
    if not args.no_browser:
        threading.Thread(
            target=_open_when_ready, args=(host, args.port), daemon=True
        ).start()
    uvicorn.run(create_app(), host=host, port=args.port)


def _open_when_ready(host: str, port: int, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            socket.create_connection((host, port), timeout=0.5).close()
            break
        except OSError:
            time.sleep(0.2)
    webbrowser.open(f"http://{host}:{port}")
