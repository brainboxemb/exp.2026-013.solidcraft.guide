from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import sys


def control_token(port: int) -> str:
    explicit = os.environ.get("SOLIDCRAFT_CONTROL_TOKEN")
    if explicit:
        return explicit.strip()

    explicit_dir = os.environ.get("SOLIDCRAFT_CONTROL_DIR")
    if explicit_dir:
        folder = Path(explicit_dir)
    elif sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            raise RuntimeError("LOCALAPPDATA is not set")
        folder = Path(local_app_data) / "SolidCraft" / "control"
    elif sys.platform == "darwin":
        folder = Path.home() / "Library/Application Support/SolidCraft/control"
    else:
        data = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
        folder = Path(data) / "solidcraft" / "control"

    token_file = folder / f"{port}.token"
    if not token_file.is_file():
        raise RuntimeError(
            f"SolidCraft control token not found: {token_file}. "
            f"Start SolidCraft with --control {port}."
        )
    return token_file.read_text(encoding="utf-8").strip()


class ControlClient:
    def __init__(self, port: int = 7878, host: str = "127.0.0.1"):
        self.port = port
        self.host = host

    def call(self, method: str, params: dict | None = None):
        message = {
            "id": 1,
            "method": method,
            "params": params or {},
            "token": control_token(self.port),
        }
        with socket.create_connection((self.host, self.port), timeout=10) as sock:
            sock.sendall((json.dumps(message) + "\n").encode("utf-8"))
            chunks = bytearray()
            while not chunks.endswith(b"\n"):
                part = sock.recv(1 << 16)
                if not part:
                    break
                chunks.extend(part)
        if not chunks:
            raise RuntimeError(f"SolidCraft returned no reply for {method}")
        reply = json.loads(chunks)
        if not reply.get("ok", False):
            raise RuntimeError(f"{method}: {reply.get('error', reply)}")
        return reply.get("result")
