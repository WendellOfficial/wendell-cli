from pathlib import Path

import pytest

from wendell_ci.config import GateConfig
from wendell_ci.gates import evaluate_gates
from wendell_ci.worldsim_client import LocalWorldsimClient, WorldsimUnavailableError


ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_INPUT = ROOT / "configs" / "customer_inputs" / "workspace_access_support_input.json"


def _skip_without_worldsim_fixture() -> None:
    if not WORKSPACE_INPUT.exists():
        pytest.skip("legacy worldsim fixture is not included in the public CLI repository")


def test_local_worldsim_client_compiles_existing_world() -> None:
    _skip_without_worldsim_fixture()
    client = LocalWorldsimClient()

    try:
        dto = client.compile_bundle(WORKSPACE_INPUT)
    except WorldsimUnavailableError:
        pytest.skip("worldsim package is not installed in this environment")

    assert dto["fingerprint"]
    assert dto["scenario_count"] > 0
    assert dto["rubric_count"] == dto["scenario_count"]


def test_local_worldsim_client_converts_real_agent_run_to_suite_result() -> None:
    _skip_without_worldsim_fixture()
    client = LocalWorldsimClient()

    try:
        suite = client.run_builtin_agent(
            WORKSPACE_INPUT,
            "careful",
            project="workspace-agent",
            world="workspace_access_support",
            scenario_pack="smoke",
            max_turns=1,
        )
    except WorldsimUnavailableError:
        pytest.skip("worldsim package is not installed in this environment")

    assert suite.project == "workspace-agent"
    assert suite.scenario_results
    assert suite.metadata["source"] == "local_worldsim"
    assert suite.metadata["compiled_fingerprint"]
    assert all(result.trace_id for result in suite.scenario_results)
    assert all(result.dimensions for result in suite.scenario_results)


def test_local_worldsim_result_can_drive_advisory_gates() -> None:
    _skip_without_worldsim_fixture()
    client = LocalWorldsimClient()

    try:
        suite = client.run_builtin_agent(
            WORKSPACE_INPUT,
            "risky",
            project="workspace-agent",
            world="workspace_access_support",
            scenario_pack="smoke",
            max_turns=1,
        )
    except WorldsimUnavailableError:
        pytest.skip("worldsim package is not installed in this environment")

    decision = evaluate_gates(suite, GateConfig(), mode="advisory")

    assert decision.exit_code == 0
    assert decision.blocking is False
    assert suite.critical_failure_count > 0 or suite.suite_score < 0.80
