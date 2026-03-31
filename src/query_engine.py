from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import time
import uuid

from .commands import AGENT_COMMANDS, find_commands
from .context import PortContext, build_port_context
from .history import HistoryLog
from .models import TurnResult, UsageSummary
from .session_store import TranscriptStore, new_session_id, persist_session
from .tools import AGENT_TOOLS, find_tools


@dataclass
class QueryEngineConfig:
    model: str = 'claude-opus-4-5'
    max_turns: int = 10
    temperature: float = 1.0
    system_prompt: str = 'You are crawl-code, an advanced AI coding agent.'
    tool_use: bool = True


@dataclass
class QueryEnginePort:
    context: PortContext = field(default_factory=build_port_context)
    config: QueryEngineConfig = field(default_factory=QueryEngineConfig)
    history: HistoryLog = field(default_factory=HistoryLog)
    transcript_store: TranscriptStore = field(default_factory=lambda: TranscriptStore(session_id=new_session_id()))
    usage: UsageSummary = field(default_factory=UsageSummary)

    @classmethod
    def from_workspace(cls, workspace: str | Path | None = None) -> 'QueryEnginePort':
        ctx = build_port_context(workspace_root=workspace)
        return cls(context=ctx, transcript_store=TranscriptStore(session_id=ctx.session_id))

    def submit_message(self, prompt: str) -> str:
        self.history.add('user', prompt)
        self.transcript_store.append('user', prompt)
        response = self._generate_response(prompt)
        self.history.add('assistant', response)
        self.transcript_store.append('assistant', response)
        self.usage = self.usage.add_turn(prompt, response)
        return response

    def _generate_response(self, prompt: str) -> str:
        needle = prompt.lower()
        matched_tools = find_tools(needle, limit=3)
        matched_commands = find_commands(needle, limit=3)
        parts = [f'Responding to: {prompt!r}', '']
        if matched_tools:
            parts.append('Relevant tools:')
            parts.extend(f'  - {t.name}: {t.responsibility}' for t in matched_tools)
        if matched_commands:
            parts.append('Relevant commands:')
            parts.extend(f'  - {c.name}: {c.responsibility}' for c in matched_commands)
        if not matched_tools and not matched_commands:
            parts.append('No specific tools matched. Use `help` to see available commands.')
        parts.append('')
        parts.append(f'[session={self.context.session_id[:8]} model={self.config.model}]')
        return '\n'.join(parts)

    def persist_session(self) -> Path:
        return self.transcript_store.flush()

    def render_summary(self) -> str:
        lines = [
            '# crawl-code Agent Summary',
            '',
            f'- Session: {self.context.session_id[:8]}',
            f'- Model: {self.config.model}',
            f'- Workspace: {self.context.workspace_root}',
            f'- History turns: {len(self.history)}',
            f'- Input tokens (est.): {self.usage.input_tokens}',
            f'- Output tokens (est.): {self.usage.output_tokens}',
            f'- Tool calls: {self.usage.tool_calls}',
            '',
            f'## Registered Tools ({len(AGENT_TOOLS)})',
        ]
        lines.extend(f'- {t.name} [{t.status}]: {t.responsibility}' for t in AGENT_TOOLS)
        lines.append('')
        lines.append(f'## Registered Commands ({len(AGENT_COMMANDS)})')
        lines.extend(f'- {c.name} [{c.status}]: {c.responsibility}' for c in AGENT_COMMANDS)
        return '\n'.join(lines)
