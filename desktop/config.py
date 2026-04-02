from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _default_session_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "DeeplomDesktop"
    return Path.home() / ".deeplom-desktop"


@dataclass(frozen=True)
class AppConfig:
    app_name: str = "proзапас"
    api_base_url: str = os.getenv("DEEPLOM_API_BASE_URL", "http://127.0.0.1:8000")
    request_timeout_seconds: float = float(os.getenv("DEEPLOM_REQUEST_TIMEOUT", "10"))
    session_file: Path = _default_session_dir() / "session.json"


def get_config() -> AppConfig:
    return AppConfig()
