from __future__ import annotations

from dataclasses import dataclass, field
import tomllib
from pathlib import Path
from typing import Any, Literal


RunnerMode = Literal["advisory", "blocking"]


@dataclass(frozen=True)
class GateConfig:
    suite_min_score: float = 0.80
    scenario_min_score: float = 0.75
    critical_failures_allowed: int = 0
    required_step_statuses: tuple[str, ...] = ("completed", "blocked")


@dataclass(frozen=True)
class RunnerConfig:
    project: str
    mode: RunnerMode = "advisory"
    api_url: str | None = None
    api_key_env: str = "WENDELL_INKPASS_API_KEY"
    world: str | None = None
    world_version: str | None = None
    scenario_pack: str | None = None
    scenario_pack_version: str | None = None
    worldsim_input: str | None = None
    agent: str = "careful"
    agent_command: str | None = None
    agent_timeout_seconds: float = 120.0
    upload_traces: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    external_ci_ref: dict[str, Any] = field(default_factory=dict)
    gates: GateConfig = field(default_factory=GateConfig)
    project_dir: str | None = None

    @classmethod
    def from_file(cls, path: str | Path) -> "RunnerConfig":
        config_path = Path(path)
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        return cls.from_dict(data, base_dir=config_path.parent)

    @classmethod
    def from_dict(cls, data: dict[str, Any], base_dir: Path | None = None) -> "RunnerConfig":
        project = data.get("project")
        if not isinstance(project, str) or not project.strip():
            raise ValueError("config must include non-empty string field `project`.")
        gates_data = data.get("gates", {})
        if not isinstance(gates_data, dict):
            raise ValueError("config field `gates` must be a table.")
        allowed_gate_fields = set(GateConfig.__dataclass_fields__)
        unknown_gate_fields = sorted(str(key) for key in gates_data if key not in allowed_gate_fields)
        if unknown_gate_fields:
            raise ValueError(f"config field `gates` has unknown key(s): {', '.join(unknown_gate_fields)}.")
        gates = GateConfig(**gates_data)
        mode = data.get("mode", "advisory")
        if mode not in {"advisory", "blocking"}:
            raise ValueError("config field `mode` must be 'advisory' or 'blocking'.")
        agent_timeout_seconds = _positive_number(
            data.get("agent_timeout_seconds", 120.0),
            "agent_timeout_seconds",
        )
        worldsim_input = data.get("worldsim_input")
        if worldsim_input and base_dir:
            input_path = Path(worldsim_input)
            if not input_path.is_absolute():
                worldsim_input = str((base_dir / input_path).resolve())
        return cls(
            project=project.strip(),
            mode=mode,
            api_url=data.get("api_url"),
            api_key_env=str(data.get("api_key_env", "WENDELL_INKPASS_API_KEY")),
            world=data.get("world"),
            world_version=data.get("world_version"),
            scenario_pack=data.get("scenario_pack"),
            scenario_pack_version=data.get("scenario_pack_version"),
            worldsim_input=worldsim_input,
            agent=str(data.get("agent", "careful")),
            agent_command=data.get("agent_command"),
            agent_timeout_seconds=agent_timeout_seconds,
            upload_traces=bool(data.get("upload_traces", True)),
            metadata=dict(data.get("metadata", {})),
            external_ci_ref=dict(data.get("external_ci_ref", {})),
            gates=gates,
            project_dir=str(base_dir.resolve()) if base_dir else None,
        )


def _positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"config field `{label}` must be a positive number.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"config field `{label}` must be a positive number.") from exc
    if number <= 0:
        raise ValueError(f"config field `{label}` must be a positive number.")
    return number
