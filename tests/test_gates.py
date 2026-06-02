from wendell_ci.config import GateConfig
from wendell_ci.gates import evaluate_gates
from wendell_ci.models import ScenarioResult, SuiteResult


def test_advisory_mode_reports_failure_without_blocking_exit() -> None:
    suite = SuiteResult(
        project="agent",
        world="world",
        scenario_pack="smoke",
        scenario_results=(ScenarioResult("s1", 0.50),),
    )

    decision = evaluate_gates(suite, GateConfig(), mode="advisory")

    assert decision.passed is False
    assert decision.status == "needs_work"
    assert decision.exit_code == 0


def test_blocking_mode_fails_exit_when_gates_fail() -> None:
    suite = SuiteResult(
        project="agent",
        world="world",
        scenario_pack="smoke",
        scenario_results=(ScenarioResult("s1", 0.50),),
    )

    decision = evaluate_gates(suite, GateConfig(), mode="blocking")

    assert decision.passed is False
    assert decision.status == "fail"
    assert decision.exit_code == 1


def test_critical_failure_fails_even_with_high_score() -> None:
    suite = SuiteResult(
        project="agent",
        world="world",
        scenario_pack="smoke",
        scenario_results=(ScenarioResult("s1", 0.95, critical_failures=("leaked secret",)),),
    )

    decision = evaluate_gates(suite, GateConfig(), mode="blocking")

    assert decision.passed is False
    assert decision.exit_code == 1
    assert any("critical failures" in reason for reason in decision.reasons)
