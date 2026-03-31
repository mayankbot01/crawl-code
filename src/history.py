from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class HistoryEntry:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    tool_calls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp,
            'tool_calls': self.tool_calls,
            'metadata': self.metadata,
        }


@dataclass
class HistoryLog:
    entries: list[HistoryEntry] = field(default_factory=list)
    max_size: int = 1000

    def add(self, role: str, content: str, tool_calls: list[str] | None = None) -> None:
        entry = HistoryEntry(role=role, content=content, tool_calls=tool_calls or [])
        self.entries.append(entry)
        if len(self.entries) > self.max_size:
            self.entries = self.entries[-self.max_size:]

    def last_n(self, n: int) -> list[HistoryEntry]:
        return self.entries[-n:]

    def user_turns(self) -> list[HistoryEntry]:
        return [e for e in self.entries if e.role == 'user']

    def assistant_turns(self) -> list[HistoryEntry]:
        return [e for e in self.entries if e.role == 'assistant']

    def to_messages(self) -> list[dict[str, str]]:
        return [{'role': e.role, 'content': e.content} for e in self.entries]

    def render_markdown(self) -> str:
        lines = ['## Conversation History', '']
        for e in self.entries:
            prefix = 'User' if e.role == 'user' else 'Assistant'
            lines.append(f'**{prefix}** ({time.strftime("%H:%M:%S", time.localtime(e.timestamp))}):')
            lines.append(e.content[:200] + ('...' if len(e.content) > 200 else ''))
            if e.tool_calls:
                lines.append(f'  _tools used: {", ".join(e.tool_calls)}_')
            lines.append('')
        return '\n'.join(lines)

    def token_estimate(self) -> int:
        return sum(len(e.content.split()) for e in self.entries)

    def clear(self) -> None:
        self.entries.clear()

    def __len__(self) -> int:
        return len(self.entries)
