"""Timeline helpers for DR timing (RTO measurement)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text).astimezone(timezone.utc)


@dataclass
class TimelineEvent:
    name: str
    at: datetime
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "at": self.at.astimezone(timezone.utc).isoformat(),
            "note": self.note,
        }


@dataclass
class Timeline:
    """Ordered named events for a recovery drill."""

    events: list[TimelineEvent] = field(default_factory=list)

    def mark(self, name: str, at: str | datetime | None = None, note: str = "") -> TimelineEvent:
        event = TimelineEvent(name=name, at=parse_time(at) if at else utc_now(), note=note)
        self.events.append(event)
        return event

    def get(self, name: str) -> TimelineEvent | None:
        for event in reversed(self.events):
            if event.name == name:
                return event
        return None

    def duration_seconds(self, start: str, end: str) -> float | None:
        a = self.get(start)
        b = self.get(end)
        if not a or not b:
            return None
        return (b.at - a.at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        return {"events": [e.to_dict() for e in self.events]}
