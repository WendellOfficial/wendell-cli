from pathlib import Path

import pytest

from wendell_ci.config import RunnerConfig


def test_config_resolves_worldsim_input_relative_to_config_file(tmp_path: Path) -> None:
    config = tmp_path / "configs" / "wendell.toml"
    config.parent.mkdir()
    config.write_text(
        "\n".join(
            [
                'project = "agent"',
                'worldsim_input = "../worlds/input.json"',
            ]
        ),
        encoding="utf-8",
    )

    loaded = RunnerConfig.from_file(config)

    assert loaded.worldsim_input == str((tmp_path / "worlds" / "input.json").resolve())


def test_config_requires_project(tmp_path: Path) -> None:
    config = tmp_path / "wendell.toml"
    config.write_text('agent_command = "python scripts/agent.py"\n', encoding="utf-8")

    with pytest.raises(ValueError, match="non-empty string field `project`"):
        RunnerConfig.from_file(config)


def test_config_rejects_unknown_gate_keys(tmp_path: Path) -> None:
    config = tmp_path / "wendell.toml"
    config.write_text(
        "\n".join(
            [
                'project = "agent"',
                "[gates]",
                "suite_minimum_score = 0.90",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown key"):
        RunnerConfig.from_file(config)


def test_config_requires_gates_to_be_table(tmp_path: Path) -> None:
    config = tmp_path / "wendell.toml"
    config.write_text(
        "\n".join(
            [
                'project = "agent"',
                'gates = "strict"',
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="`gates` must be a table"):
        RunnerConfig.from_file(config)


def test_config_reads_agent_timeout_seconds(tmp_path: Path) -> None:
    config = tmp_path / "wendell.toml"
    config.write_text(
        "\n".join(
            [
                'project = "agent"',
                "agent_timeout_seconds = 300",
            ]
        ),
        encoding="utf-8",
    )

    loaded = RunnerConfig.from_file(config)

    assert loaded.agent_timeout_seconds == 300.0


def test_config_rejects_invalid_agent_timeout_seconds(tmp_path: Path) -> None:
    config = tmp_path / "wendell.toml"
    config.write_text(
        "\n".join(
            [
                'project = "agent"',
                "agent_timeout_seconds = 0",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="`agent_timeout_seconds` must be a positive number"):
        RunnerConfig.from_file(config)
