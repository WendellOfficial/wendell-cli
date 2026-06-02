import json
from pathlib import Path

import pytest

from wendell_ci.worldsim_client import LocalWorldsimClient, WorldsimUnavailableError


ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_INPUT = ROOT / "configs" / "customer_inputs" / "workspace_access_support_input.json"


def _skip_without_worldsim_fixture() -> None:
    if not WORKSPACE_INPUT.exists():
        pytest.skip("legacy worldsim fixture is not included in the public CLI repository")


def test_local_worldsim_client_runs_command_agent_from_project_directory(tmp_path: Path) -> None:
    _skip_without_worldsim_fixture()
    agent = tmp_path / "agent.py"
    agent.write_text(
        """
import json
from pathlib import Path
import sys

Path("agent_was_here.txt").write_text("ran", encoding="utf-8")
payload = json.loads(sys.stdin.read())
steps = payload.get("available_tools", [])
tool_calls = []
for tool in steps:
    name = tool.get("name")
    if name:
        tool_calls.append({"name": name, "args": {}})
print(json.dumps({"message": "I will verify details, follow policy, and escalate when required.", "tool_calls": tool_calls}))
""".strip(),
        encoding="utf-8",
    )

    client = LocalWorldsimClient()
    try:
        suite = client.run_builtin_agent(
            WORKSPACE_INPUT,
            "project_agent",
            project="workspace-agent",
            world="workspace_access_support",
            scenario_pack="smoke",
            agent_command="python agent.py",
            agent_cwd=str(tmp_path),
            max_turns=1,
        )
    except WorldsimUnavailableError:
        pytest.skip("worldsim package is not installed in this environment")

    assert suite.scenario_results
    assert (tmp_path / "agent_was_here.txt").read_text(encoding="utf-8") == "ran"
    assert all(result.trace_id for result in suite.scenario_results)


def test_command_agent_receives_blind_eval_payload_without_hidden_rubric(tmp_path: Path) -> None:
    _skip_without_worldsim_fixture()
    agent = tmp_path / "agent.py"
    payload_path = tmp_path / "payload.json"
    agent.write_text(
        f"""
import json
from pathlib import Path
import sys

payload = json.loads(sys.stdin.read())
Path({str(payload_path)!r}).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps({{"message": "I will help with the request.", "tool_calls": []}}))
""".strip(),
        encoding="utf-8",
    )

    client = LocalWorldsimClient()
    try:
        client.run_builtin_agent(
            WORKSPACE_INPUT,
            "project_agent",
            project="workspace-agent",
            world="workspace_access_support",
            scenario_pack="smoke",
            agent_command="python agent.py",
            agent_cwd=str(tmp_path),
            max_turns=1,
        )
    except WorldsimUnavailableError:
        pytest.skip("worldsim package is not installed in this environment")

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    serialized = json.dumps(payload)
    assert payload["schema_version"] == "wendell.agent_input.v1"
    assert "available_tools" in payload
    assert "case" in payload
    assert "mode" not in payload
    assert "rubric" not in payload
    assert "success_criteria" not in serialized
    assert "failure_criteria" not in serialized
    assert "hidden_facts" not in serialized
    assert "source_lineage" not in serialized
    assert "terminal_outcome" not in serialized
    assert "tool_contract" not in serialized


def test_ambiguity_deferral_can_block_steps_without_critical_failure(tmp_path: Path) -> None:
    _skip_without_worldsim_fixture()
    agent = tmp_path / "agent.py"
    agent.write_text(
        """
import json
import sys

json.loads(sys.stdin.read())
print(json.dumps({
    "message": "I need the missing required detail before I can use tools or claim this is done.",
    "tool_calls": [],
}))
""".strip(),
        encoding="utf-8",
    )

    client = LocalWorldsimClient()
    try:
        suite = client.run_builtin_agent(
            WORKSPACE_INPUT,
            "project_agent",
            project="workspace-agent",
            world="workspace_access_support",
            scenario_pack="smoke",
            agent_command="python agent.py",
            agent_cwd=str(tmp_path),
            max_turns=1,
        )
    except WorldsimUnavailableError:
        pytest.skip("worldsim package is not installed in this environment")

    edge_results = [
        result
        for result in suite.scenario_results
        if any(status == "blocked" for status in result.step_statuses.values())
    ]
    assert edge_results
    assert all(not result.critical_failures for result in edge_results)
    assert all(
        assertion.get("status") != "failed"
        for result in edge_results
        for assertion in result.assertion_results
    )


def test_local_worldsim_client_fails_fast_when_generated_adapter_is_unwired(tmp_path: Path) -> None:
    _skip_without_worldsim_fixture()
    adapter = tmp_path / "wendell_agent_adapter.py"
    adapter.write_text(
        """
import sys

raise SystemExit(
    "Wendell adapter is not wired. Set WENDELL_APP_AGENT_COMMAND to a command "
    "that runs your production agent adapter, or replace scripts/wendell_agent_adapter.py."
)
""".strip(),
        encoding="utf-8",
    )

    client = LocalWorldsimClient()
    with pytest.raises(ValueError, match="Wendell adapter is not wired"):
        client.run_builtin_agent(
            WORKSPACE_INPUT,
            "project_agent",
            project="workspace-agent",
            world="workspace_access_support",
            scenario_pack="smoke",
            agent_command="python wendell_agent_adapter.py",
            agent_cwd=str(tmp_path),
            max_turns=1,
        )
