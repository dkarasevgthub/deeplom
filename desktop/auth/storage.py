from __future__ import annotations

import json
from pathlib import Path

from desktop.models import StoredSession


class TokenStorage:
    def __init__(self, session_file: Path):
        self.session_file = session_file

    def load(self) -> StoredSession | None:
        if not self.session_file.exists():
            return None

        try:
            payload = json.loads(self.session_file.read_text(encoding="utf-8"))
            return StoredSession(
                access_token=payload["access_token"],
                refresh_token=payload["refresh_token"],
            )
        except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError):
            self.clear()
            return None

    def save(self, access_token: str, refresh_token: str) -> None:
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        self.session_file.write_text(json.dumps(payload), encoding="utf-8")

    def clear(self) -> None:
        try:
            self.session_file.unlink(missing_ok=True)
        except OSError:
            pass
