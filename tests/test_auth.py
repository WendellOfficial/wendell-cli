import json
import stat

from wendell_ci.auth import StoredCredentials, credentials_path, load_credentials, store_credentials


def test_store_credentials_uses_wendell_config_home_with_strict_permissions(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WENDELL_CONFIG_HOME", str(tmp_path / "wendell-config"))

    path = store_credentials(StoredCredentials(api_key="inkpass-key", api_url="http://127.0.0.1:8765"))

    assert path == tmp_path / "wendell-config" / "credentials.json"
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["profiles"]["default"]["api_key"] == "inkpass-key"
    assert load_credentials() == StoredCredentials(api_key="inkpass-key", api_url="http://127.0.0.1:8765")


def test_credentials_path_defaults_to_xdg_config_home(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("WENDELL_CONFIG_HOME", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    assert credentials_path() == tmp_path / "wendell" / "credentials.json"
