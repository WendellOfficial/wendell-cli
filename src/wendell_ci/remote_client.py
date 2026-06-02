from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from .auth import resolve_api_key

DEFAULT_API_URL = "https://api.wendellai.com"


class RemoteWendellClient:
    """Minimal HTTP client for the future Wendell system of record.

    The runner should execute agents locally. This client is only responsible for
    fetching versioned evaluation data and uploading traces/results.
    """

    def __init__(self, api_url: str | None = None, api_key: str | None = None) -> None:
        api_url = api_url or DEFAULT_API_URL
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

    @classmethod
    def from_env(cls, api_url: str | None = None, api_key_env: str = "WENDELL_INKPASS_API_KEY") -> "RemoteWendellClient":
        return cls(api_url=api_url, api_key=resolve_api_key(api_key_env))

    def fetch_scenario_pack(
        self,
        world: str,
        scenario_pack: str,
        *,
        world_version: str | None = None,
        scenario_pack_version: str | None = None,
    ) -> dict[str, Any]:
        query = {
            "world_version": world_version,
            "scenario_pack_version": scenario_pack_version,
        }
        return self._get(f"/worlds/{world}/scenario-packs/{scenario_pack}", query=query)

    def list_test_suites(self) -> dict[str, Any]:
        return self._get("/test-suites")

    def get_test_suite(self, suite_slug: str) -> dict[str, Any]:
        return self._get(f"/test-suites/{suite_slug}")

    def create_test_suite_draft(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/test-suite-drafts", payload)

    def get_test_suite_draft(self, draft_id: str) -> dict[str, Any]:
        return self._get(f"/test-suite-drafts/{draft_id}")

    def generate_playbook_summary(self, draft_id: str) -> dict[str, Any]:
        return self._post(f"/test-suite-drafts/{draft_id}/playbook-summary", {})

    def get_playbook_summary(self, summary_id: str) -> dict[str, Any]:
        return self._get(f"/playbook-summaries/{summary_id}")

    def review_playbook_summary(self, summary_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post(f"/playbook-summaries/{summary_id}/reviews", payload)

    def approve_playbook_summary(self, summary_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post(f"/playbook-summaries/{summary_id}/approve", payload)

    def generate_test_suite_candidate(self, draft_id: str) -> dict[str, Any]:
        return self._post(f"/test-suite-drafts/{draft_id}/generate-suite", {})

    def publish_test_suite_draft(self, draft_id: str) -> dict[str, Any]:
        return self._post(f"/test-suite-drafts/{draft_id}/publish", {})

    def create_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/runs", payload)

    def get_run(self, run_id: str) -> dict[str, Any]:
        return self._get(f"/runs/{run_id}")

    def get_run_report(self, run_id: str) -> dict[str, Any]:
        return self._get(f"/runs/{run_id}/report")

    def get_run_work(self, run_id: str) -> dict[str, Any]:
        return self._get(f"/runs/{run_id}/work")

    def submit_agent_turn(self, run_id: str, scenario_execution_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post(f"/runs/{run_id}/scenario-executions/{scenario_execution_id}/agent-turns", payload)

    def upload_trace(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post(f"/runs/{run_id}/traces", payload)

    def upload_result(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post(f"/runs/{run_id}/results", payload)

    def complete_run(self, run_id: str) -> dict[str, Any]:
        return self._post(f"/runs/{run_id}/complete", {})

    def get_identity(self) -> dict[str, Any]:
        return self._get("/me")

    def start_runner_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/auth/runner-sessions", payload)

    def register_cli(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/auth/register-cli", payload)

    def login_cli(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/auth/login-cli", payload)

    def create_cli_session_link(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/auth/cli-session-link", payload)

    def _get(self, path: str, query: dict[str, str | None] | None = None) -> dict[str, Any]:
        query = {key: value for key, value in (query or {}).items() if value}
        suffix = ""
        if query:
            from urllib.parse import urlencode

            suffix = f"?{urlencode(query)}"
        req = self._request(path + suffix, method="GET")
        return self._send(req)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = self._request(path, method="POST", data=body)
        req.add_header("Content-Type", "application/json")
        return self._send(req)

    def _request(self, path: str, method: str, data: bytes | None = None) -> request.Request:
        req = request.Request(f"{self.api_url}{path}", data=data, method=method)
        req.add_header("Accept", "application/json")
        if self.api_key:
            req.add_header("X-API-Key", self.api_key)
        return req

    def _send(self, req: request.Request) -> dict[str, Any]:
        try:
            with request.urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = _http_error_detail(exc)
            if detail:
                raise RuntimeError(f"HTTP Error {exc.code}: {exc.reason}: {detail}") from exc
            raise
        return json.loads(raw) if raw else {}


def _http_error_detail(exc: error.HTTPError) -> str:
    raw = exc.read().decode("utf-8", errors="replace").strip()
    if not raw:
        return ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:500]
    detail = payload.get("detail") if isinstance(payload, dict) else None
    if isinstance(detail, str):
        return detail
    return json.dumps(payload, sort_keys=True)[:500]
