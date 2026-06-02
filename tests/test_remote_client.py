import os
import json
from urllib import error, request

from wendell_ci.remote_client import RemoteWendellClient


def test_remote_client_reads_default_inkpass_api_key_env(monkeypatch) -> None:
    monkeypatch.setenv("WENDELL_INKPASS_API_KEY", "inkpass-key")

    client = RemoteWendellClient.from_env("https://wendell.example")

    assert client.api_key == "inkpass-key"


def test_remote_client_sends_inkpass_api_key_header() -> None:
    client = RemoteWendellClient("https://wendell.example", api_key="inkpass-key")

    req = client._request("/worlds", method="GET")

    assert isinstance(req, request.Request)
    assert req.get_header("X-api-key") == "inkpass-key"
    assert req.get_header("Authorization") is None


def test_remote_client_falls_back_to_stored_credentials(tmp_path, monkeypatch) -> None:
    from wendell_ci.auth import StoredCredentials, store_credentials

    monkeypatch.delenv("WENDELL_INKPASS_API_KEY", raising=False)
    monkeypatch.setenv("WENDELL_CONFIG_HOME", str(tmp_path / "wendell-config"))
    store_credentials(StoredCredentials(api_key="stored-key"))

    client = RemoteWendellClient.from_env("https://wendell.example")

    assert client.api_key == "stored-key"


def test_remote_client_fetches_current_identity(monkeypatch) -> None:
    captured_headers = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return b'{"auth_type":"api_key","external_org_id":"org_123","external_user_id":"user_123"}'

    def fake_urlopen(req, timeout):
        nonlocal captured_headers
        captured_headers = dict(req.header_items())
        assert req.full_url == "https://wendell.example/me"
        assert timeout == 30
        return Response()

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    identity = RemoteWendellClient("https://wendell.example", api_key="inkpass-key").get_identity()

    assert identity["auth_type"] == "api_key"
    assert captured_headers["X-api-key"] == "inkpass-key"


def test_remote_client_lists_test_suites(monkeypatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return b'{"test_suites":[{"slug":"commerce-support"}]}'

    def fake_urlopen(req, timeout):
        assert req.full_url == "https://wendell.example/test-suites"
        assert timeout == 30
        return Response()

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    suites = RemoteWendellClient("https://wendell.example", api_key="inkpass-key").list_test_suites()

    assert suites["test_suites"][0]["slug"] == "commerce-support"


def test_remote_client_fetches_test_suite_detail(monkeypatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return b'{"world":{"slug":"commerce-support"}}'

    def fake_urlopen(req, timeout):
        assert req.full_url == "https://wendell.example/test-suites/commerce-support"
        assert timeout == 30
        return Response()

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    suite = RemoteWendellClient("https://wendell.example", api_key="inkpass-key").get_test_suite("commerce-support")

    assert suite["world"]["slug"] == "commerce-support"


def test_remote_client_creates_test_suite_draft(monkeypatch) -> None:
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return b'{"draft":{"id":"wdraft_123"}}'

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["data"] = json.loads(req.data.decode("utf-8"))
        assert timeout == 30
        return Response()

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    draft = RemoteWendellClient("https://wendell.example", api_key="inkpass-key").create_test_suite_draft(
        {"name": "Commerce Support"}
    )

    assert draft["draft"]["id"] == "wdraft_123"
    assert captured == {
        "url": "https://wendell.example/test-suite-drafts",
        "method": "POST",
        "data": {"name": "Commerce Support"},
    }


def test_remote_client_uses_test_suite_authoring_endpoints(monkeypatch) -> None:
    calls: list[tuple[str, str, dict | None]] = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return b'{"ok":true}'

    def fake_urlopen(req, timeout):
        calls.append(
            (
                req.get_method(),
                req.full_url,
                None if req.data is None else json.loads(req.data.decode("utf-8")),
            )
        )
        assert timeout == 30
        return Response()

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    client = RemoteWendellClient("https://wendell.example", api_key="inkpass-key")
    client.get_test_suite_draft("wdraft_123")
    client.generate_playbook_summary("wdraft_123")
    client.get_playbook_summary("psum_123")
    client.review_playbook_summary("psum_123", {"operations": []})
    client.approve_playbook_summary("psum_123", {"reviewer_ref": "user_123"})
    client.generate_test_suite_candidate("wdraft_123")
    client.publish_test_suite_draft("wdraft_123")

    assert calls == [
        ("GET", "https://wendell.example/test-suite-drafts/wdraft_123", None),
        ("POST", "https://wendell.example/test-suite-drafts/wdraft_123/playbook-summary", {}),
        ("GET", "https://wendell.example/playbook-summaries/psum_123", None),
        ("POST", "https://wendell.example/playbook-summaries/psum_123/reviews", {"operations": []}),
        ("POST", "https://wendell.example/playbook-summaries/psum_123/approve", {"reviewer_ref": "user_123"}),
        ("POST", "https://wendell.example/test-suite-drafts/wdraft_123/generate-suite", {}),
        ("POST", "https://wendell.example/test-suite-drafts/wdraft_123/publish", {}),
    ]


def test_remote_client_fetches_remote_runtime_work(monkeypatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return b'{"run_id":"run_123","done":false}'

    def fake_urlopen(req, timeout):
        assert req.full_url == "https://wendell.example/runs/run_123/work"
        assert timeout == 30
        return Response()

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    work = RemoteWendellClient("https://wendell.example", api_key="inkpass-key").get_run_work("run_123")

    assert work["done"] is False


def test_remote_client_fetches_run_report(monkeypatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return b'{"capability_report":{"overall_score":0.94}}'

    def fake_urlopen(req, timeout):
        assert req.full_url == "https://wendell.example/runs/run_123/report"
        assert timeout == 30
        return Response()

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    report = RemoteWendellClient("https://wendell.example", api_key="inkpass-key").get_run_report("run_123")

    assert report["capability_report"]["overall_score"] == 0.94


def test_remote_client_submits_agent_turn(monkeypatch) -> None:
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return b'{"ok":true,"trajectory_id":"traj_123"}'

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["data"] = req.data
        return Response()

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    response = RemoteWendellClient("https://wendell.example", api_key="inkpass-key").submit_agent_turn(
        "run_123",
        "sexec_123",
        {"message": "ok"},
    )

    assert response["ok"] is True
    assert captured["url"] == "https://wendell.example/runs/run_123/scenario-executions/sexec_123/agent-turns"
    assert captured["data"] == b'{"message": "ok"}'


def test_remote_client_includes_http_error_detail(monkeypatch) -> None:
    def fake_urlopen(req, timeout):
        raise error.HTTPError(
            req.full_url,
            500,
            "Internal Server Error",
            hdrs=None,
            fp=BytesBody(b'{"detail":"database migration missing"}'),
        )

    class BytesBody:
        def __init__(self, payload: bytes) -> None:
            self.payload = payload

        def read(self) -> bytes:
            return self.payload

        def close(self) -> None:
            return None

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    try:
        RemoteWendellClient("https://wendell.example", api_key="inkpass-key").create_test_suite_draft(
            {"name": "Commerce Support"}
        )
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected HTTP error detail")

    assert "HTTP Error 500: Internal Server Error: database migration missing" == message
