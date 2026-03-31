from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import time
import uuid


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    DONE = "done"
    ERROR = "error"


class ToolStatus(str, Enum):
    AVAILABLE = "available"
    BLOCKED = "blocked"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class Subsystem:
    name: str
    path: str
    file_count: int
    notes: str
    version: str = "1.0.0"


@dataclass(frozen=True)
class AgentModule:
    name: str
    responsibility: str
    source_hint: str
    status: str = "planned"
    tags: tuple[str, ...] = field(default_factory=tuple)
    priority: int = 0


@dataclass(frozen=True)
class PermissionDenial:
    tool_name: str
    reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class UsageSummary:
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def add_turn(self, prompt: str, output: str, tool_calls: int = 0) -> 'UsageSummary':
        return UsageSummary(
            input_tokens=self.input_tokens + len(prompt.split()),
            output_tokens=self.output_tokens + len(output.split()),
            tool_calls=self.tool_calls + tool_calls,
            session_id=self.session_id,
        )

    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class AgentBacklog:
    title: str
    modules: list[AgentModule] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def summary_lines(self) -> list[str]:
        return [
            f'- {m.name} [{m.status}] — {m.responsibility} (from {m.source_hint}) priority={m.priority}'
            for m in self.modules
        ]

    def filter_by_status(self, status: str) -> list[AgentModule]:
        return [m for m in self.modules if m.status == status]

    def filter_by_tag(self, tag: str) -> list[AgentModule]:
        return [m for m in self.modules if tag in m.tags]


@dataclass(frozen=True)
class TurnResult:
    turn_index: int
    output: str
    stop_reason: str
    tool_calls_made: list[str] = field(default_factory=list)
    usage: Optional[UsageSummary] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        return self.stop_reason in ('end_turn', 'max_turns', 'error')


@dataclass
class PersistedSession:
    session_id: str
    messages: list[dict[str, Any]]
    input_tokens: int = 0
    output_tokens: int = 0
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'session_id': self.session_id,
            'messages': self.messages,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'created_at': self.created_at,
            'metadata': self.metadata,
        }
