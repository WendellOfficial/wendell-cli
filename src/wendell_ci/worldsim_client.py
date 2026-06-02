from __future__ import annotations

from pathlib import Path
import shlex
from typing import Any, Callable

from .models import ScenarioResult, SuiteResult


class WorldsimUnavailableError(RuntimeError):
    pass


class LocalWorldsimClient:
    """Adapter for dogfooding Wendell CI against the existing worldsim package."""

    def compile_bundle(self, input_path: str | Path) -> dict[str, Any]:
        services, customer_inputs, _support_demo = _load_worldsim()
        bundle = customer_inputs.load_customer_input_bundle(Path(input_path))
        return services.compile_service(bundle)

    def run_builtin_agent(
        self,
        input_path: str | Path,
        agent_name: str,
        *,
        project: str,
        world: str | None,
        scenario_pack: str | None,
        agent_command: str | None = None,
        agent_cwd: str | None = None,
        max_turns: int = 1,
        on_scenario_result: Callable[[ScenarioResult], None] | None = None,
    ) -> SuiteResult:
        services, customer_inputs, support_demo = _load_worldsim()
        bundle = customer_inputs.load_customer_input_bundle(Path(input_path))
        agent = _agent(support_demo, agent_name, agent_command=agent_command, agent_cwd=agent_cwd)

        def on_scenario_report(report) -> None:
            if on_scenario_result is not None:
                on_scenario_result(scenario_result_from_worldsim_report(report.to_dict()))

        try:
            run = services.agent_run_service(bundle, agent, max_turns=max_turns, on_scenario_report=on_scenario_report)
        except Exception as exc:
            if exc.__class__.__name__ == "AgentSetupError":
                raise ValueError(str(exc)) from exc
            raise
        return suite_from_worldsim_agent_report(
            run["agent_report"],
            project=project,
            world=world or str(input_path),
            scenario_pack=scenario_pack,
            metadata={
                "compiled_fingerprint": run["compiled_fingerprint"],
                "trajectory_count": run["trajectory_count"],
                "source": "local_worldsim",
            },
        )


def suite_from_worldsim_agent_report(
    agent_report: dict[str, Any],
    *,
    project: str,
    world: str | None,
    scenario_pack: str | None,
    metadata: dict[str, Any] | None = None,
) -> SuiteResult:
    scenario_results = []
    for report in agent_report.get("scenario_reports", []):
        scenario_results.append(scenario_result_from_worldsim_report(report))

    return SuiteResult(
        project=project,
        world=world,
        scenario_pack=scenario_pack,
        scenario_results=tuple(scenario_results),
        metadata=dict(metadata or {}),
    )


def scenario_result_from_worldsim_report(report: dict[str, Any]) -> ScenarioResult:
    step_statuses = {
        str(step["step_id"]): str(step["status"])
        for step in report.get("step_reports", [])
    }
    trajectory = report.get("trajectory", {})
    evaluation_payload = _latest_evaluation_payload(trajectory)
    return ScenarioResult(
        scenario_id=str(report["scenario_id"]),
        score=float(report.get("overall_score", 0.0)),
        critical_failures=tuple(str(item) for item in report.get("critical_failures", [])),
        step_statuses=step_statuses,
        dimensions={
            str(key): float(value)
            for key, value in report.get("scores", {}).items()
        },
        assertion_results=tuple(
            dict(item)
            for item in evaluation_payload.get("assertion_results", [])
            if isinstance(item, dict)
        ),
        missed_expectations=tuple(str(item) for item in report.get("missed_expectations", [])),
        improvement_prompts=tuple(str(item) for item in report.get("improvement_prompts", [])),
        trace_id=str(trajectory.get("run_id")) if trajectory.get("run_id") else None,
        trajectory=trajectory,
    )


def _latest_evaluation_payload(trajectory: dict[str, Any]) -> dict[str, Any]:
    events = trajectory.get("events") if isinstance(trajectory, dict) else []
    if not isinstance(events, list):
        return {}
    for event in reversed(events):
        if isinstance(event, dict) and event.get("type") == "evaluation":
            payload = event.get("payload")
            return payload if isinstance(payload, dict) else {}
    return {}


def _agent(support_demo, agent_name: str, *, agent_command: str | None, agent_cwd: str | None):
    if agent_command:
        services, customer_inputs, _support_demo = _load_worldsim()
        del services, customer_inputs, _support_demo
        from worldsim.agent_eval import CompiledWorldCommandAgent

        command = agent_command
        if agent_cwd:
            command = f"cd {shlex.quote(agent_cwd)} && {agent_command}"
        return CompiledWorldCommandAgent(command=command, name=agent_name or "local_command_agent")
    return _builtin_agent(support_demo, agent_name)


def _builtin_agent(support_demo, agent_name: str):
    if agent_name == "careful":
        return support_demo.CarefulSupportAgent()
    if agent_name == "risky":
        return support_demo.RiskySupportAgent()
    raise ValueError("local worldsim integration supports built-in agents: careful, risky")


def _load_worldsim():
    try:
        from worldsim import customer_inputs, services, support_demo
    except ImportError as exc:
        raise WorldsimUnavailableError(
            "worldsim is not importable. Install the simulation package in the same environment "
            "to use legacy local/offline workflows."
        ) from exc
    return services, customer_inputs, support_demo
