from __future__ import annotations

from dataclasses import dataclass

from .config import GateConfig, RunnerMode
from .models import SuiteResult


@dataclass(frozen=True)
class GateDecision:
    passed: bool
    blocking: bool
    exit_code: int
    reasons: tuple[str, ...]

    @property
    def status(self) -> str:
        if self.passed:
            return "pass"
        return "fail" if self.blocking else "needs_work"


def evaluate_gates(
    suite: SuiteResult,
    gates: GateConfig,
    mode: RunnerMode = "advisory",
) -> GateDecision:
    reasons: list[str] = []
    if suite.suite_score < gates.suite_min_score:
        reasons.append(
            f"suite score {suite.suite_score:.2f} is below required {gates.suite_min_score:.2f}"
        )
    if suite.critical_failure_count > gates.critical_failures_allowed:
        reasons.append(
            "critical failures "
            f"{suite.critical_failure_count} exceed allowed {gates.critical_failures_allowed}"
        )

    for result in suite.scenario_results:
        if result.score < gates.scenario_min_score:
            reasons.append(
                f"scenario {result.scenario_id} score {result.score:.2f} "
                f"is below required {gates.scenario_min_score:.2f}"
            )
        for step_id, status in result.step_statuses.items():
            if status not in gates.required_step_statuses:
                reasons.append(
                    f"scenario {result.scenario_id} step {step_id} status {status} "
                    f"is not one of {', '.join(gates.required_step_statuses)}"
                )

    passed = not reasons
    blocking = mode == "blocking"
    exit_code = 1 if blocking and not passed else 0
    return GateDecision(
        passed=passed,
        blocking=blocking,
        exit_code=exit_code,
        reasons=tuple(reasons),
    )

