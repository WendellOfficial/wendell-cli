from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    score: float
    critical_failures: tuple[str, ...] = ()
    step_statuses: dict[str, str] = field(default_factory=dict)
    dimensions: dict[str, float] = field(default_factory=dict)
    assertion_results: tuple[dict[str, Any], ...] = ()
    missed_expectations: tuple[str, ...] = ()
    improvement_prompts: tuple[str, ...] = ()
    trace_id: str | None = None
    trajectory: dict[str, Any] | None = None

    @property
    def critical_failure_count(self) -> int:
        return len(self.critical_failures)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "score": round(self.score, 4),
            "critical_failures": list(self.critical_failures),
            "step_statuses": self.step_statuses,
            "dimensions": self.dimensions,
            "assertion_results": list(self.assertion_results),
            "missed_expectations": list(self.missed_expectations),
            "improvement_prompts": list(self.improvement_prompts),
            "trace_id": self.trace_id,
            "trajectory": self.trajectory,
        }


@dataclass(frozen=True)
class SuiteResult:
    project: str
    world: str | None
    scenario_pack: str | None
    scenario_results: tuple[ScenarioResult, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def suite_score(self) -> float:
        if not self.scenario_results:
            return 0.0
        return sum(item.score for item in self.scenario_results) / len(self.scenario_results)

    @property
    def critical_failure_count(self) -> int:
        return sum(item.critical_failure_count for item in self.scenario_results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "world": self.world,
            "scenario_pack": self.scenario_pack,
            "suite_score": round(self.suite_score, 4),
            "critical_failure_count": self.critical_failure_count,
            "scenario_results": [item.to_dict() for item in self.scenario_results],
            "metadata": self.metadata,
        }
