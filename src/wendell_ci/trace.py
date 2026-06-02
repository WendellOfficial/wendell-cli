from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class TraceEvent:
    index: int
    type: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "type": self.type,
            "source": self.source,
            "message": self.message,
            "payload": self.payload,
        }


@dataclass
class Trace:
    scenario_id: str
    agent_name: str
    run_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    events: list[TraceEvent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def record(self, event_type: str, source: str, payload: dict[str, Any] | None = None, message: str | None = None) -> TraceEvent:
        event = TraceEvent(
            index=len(self.events) + 1,
            type=event_type,
            source=source,
            payload=payload or {},
            message=message,
        )
        self.events.append(event)
        return event

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "agent_name": self.agent_name,
            "created_at": self.created_at,
            "metadata": self.metadata,
            "events": [event.to_dict() for event in self.events],
        }


class TraceUploader:
    def upload(self, trace: Trace) -> str:
        return f"local://traces/{trace.run_id}"

