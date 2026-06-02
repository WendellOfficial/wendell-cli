from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


CONFIG_HOME_ENV = "WENDELL_CONFIG_HOME"
DEFAULT_PROFILE = "default"


@dataclass(frozen=True)
class StoredCredentials:
    api_key: str
    profile: str = DEFAULT_PROFILE
    api_url: str | None = None
    runner_id: str | None = None


def config_dir() -> Path:
    configured = os.environ.get(CONFIG_HOME_ENV)
    if configured:
        return Path(configured).expanduser()
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_home:
        return Path(xdg_home).expanduser() / "wendell"
    return Path.home() / ".config" / "wendell"


def credentials_path() -> Path:
    return config_dir() / "credentials.json"


def store_credentials(credentials: StoredCredentials) -> Path:
    directory = config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(0o700)
    path = credentials_path()
    payload: dict[str, Any] = {
        "version": 1,
        "profiles": {
            credentials.profile: {
                "api_key": credentials.api_key,
                "api_url": credentials.api_url,
                "runner_id": credentials.runner_id,
            }
        },
        "current_profile": credentials.profile,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    path.chmod(0o600)
    return path


def load_credentials(profile: str | None = None) -> StoredCredentials | None:
    path = credentials_path()
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    selected = profile or str(data.get("current_profile") or DEFAULT_PROFILE)
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        return None
    profile_data = profiles.get(selected)
    if not isinstance(profile_data, dict):
        return None
    api_key = profile_data.get("api_key")
    if not isinstance(api_key, str) or not api_key:
        return None
    api_url = profile_data.get("api_url")
    runner_id = profile_data.get("runner_id")
    return StoredCredentials(
        api_key=api_key,
        profile=selected,
        api_url=api_url if isinstance(api_url, str) and api_url else None,
        runner_id=runner_id if isinstance(runner_id, str) and runner_id else None,
    )


def delete_credentials() -> bool:
    path = credentials_path()
    if not path.exists():
        return False
    path.unlink()
    return True


def resolve_api_key(api_key_env: str) -> str | None:
    env_value = os.environ.get(api_key_env)
    if env_value:
        return env_value
    credentials = load_credentials()
    return None if credentials is None else credentials.api_key
