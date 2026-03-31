from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time

from .commands import AGENT_COMMANDS, execute_command, find_commands
from .context import PortContext, build_port_context
from .history import HistoryLog
from .models import TurnResult, UsageSummary
from .tools import AGENT_TOOLS, execute_tool, find_tools


@dataclass(frozen=True)
class RoutedMatch:
    kind: str
    name: str
    source_hint: str
    score: int


@dataclass
class RuntimeSession:
    prompt: str
    context: PortContext
    history: HistoryLog
    routed_matches: list[RoutedMatch]
    turn_results: list[TurnResult]
    created_at: float = field(default_factory=time.time)

    def as_markdown(self) -> str:
        lines = [
            f'# Runtime Session',
            f'- prompt: {self.prompt!r}',
            f'- session: {self.context.session_id[:8]}',
            f'- matched: {len(self.routed_matches)} route(s)',
            f'- turns: {len(self.turn_results)}',
            '',
        ]
        if self.routed_matches:
            lines.append('## Routed Matches')
            for m in self.routed_matches:
                lines.append(f'- [{m.kind}] {m.name} (score={m.score}) from {m.source_hint}')
            lines.append('')
        if self.turn_results:
            lines.append('## Turn Results')
            for t in self.turn_results:
                lines.append(f'### Turn {t.turn_index}')
                lines.append(t.output)
                lines.append(f'stop_reason={t.stop_reason}')
                lines.append('')
        return '\n'.join(lines)


@dataclass
class RemoteBranchResult:
    mode: str
    target: str
    status: str
    details: str

    def as_text(self) -> str:
        return f'{self.mode} -> {self.target}: {self.status}\n{self.details}'


class PortRuntime:
    def __init__(self) -> None:
        self._context = build_port_context()
        self._history = HistoryLog()

    def route_prompt(self, prompt: str, limit: int = 5) -> list[RoutedMatch]:
        needle = prompt.lower()
        matches: list[RoutedMatch] = []
        for tool in find_tools(needle, limit):
            score = sum(1 for word in needle.split() if word in tool.name.lower() + tool.responsibility.lower())
            matches.append(RoutedMatch(kind='tool', name=tool.name, source_hint=tool.source_hint, score=score + 1))
        for cmd in find_commands(needle, limit):
            score = sum(1 for word in needle.split() if word in cmd.name.lower() + cmd.responsibility.lower())
            matches.append(RoutedMatch(kind='command', name=cmd.name, source_hint=cmd.source_hint, score=score))
        return sorted(matches, key=lambda m: -m.score)[:limit]

    def bootstrap_session(self, prompt: str, limit: int = 5) -> RuntimeSession:
        matches = self.route_prompt(prompt, limit)
        self._history.add('user', prompt)
        turn = TurnResult(
            turn_index=1,
            output=f'Bootstrap turn for: {prompt!r}. Matched {len(matches)} route(s).',
            stop_reason='bootstrap',
        )
        return RuntimeSession(
            prompt=prompt,
            context=self._context,
            history=self._history,
            routed_matches=matches,
            turn_results=[turn],
        )

    def run_turn_loop(
        self,
        prompt: str,
        limit: int = 5,
        max_turns: int = 3,
        structured_output: bool = False,
    ) -> list[TurnResult]:
        results: list[TurnResult] = []
        current = prompt
        for idx in range(1, max_turns + 1):
            matches = self.route_prompt(current, limit)
            output_parts = [f'Turn {idx}: processing {current!r}']
            tool_calls: list[str] = []
            for match in matches[:2]:
                if match.kind == 'tool':
                    exec_result = execute_tool(match.name, current)
                    output_parts.append(f'  [tool] {exec_result.message}')
                    tool_calls.append(match.name)
                elif match.kind == 'command':
                    exec_result = execute_command(match.name, current)
                    output_parts.append(f'  [cmd] {exec_result.message}')
                    tool_calls.append(match.name)
            if not matches:
                output_parts.append('  No matches found. Stopping loop.')
            output = '\n'.join(output_parts)
            if structured_output:
                output = f'{{"turn": {idx}, "output": {output!r}, "tool_calls": {tool_calls}}}'
            turn = TurnResult(
                turn_index=idx,
                output=output,
                stop_reason='end_turn' if idx == max_turns else 'continue',
                tool_calls_made=tool_calls,
            )
            results.append(turn)
            self._history.add('assistant', output, tool_calls)
            if turn.is_terminal() or not matches:
                break
            current = f'follow-up from turn {idx}'
        return results


def run_remote_mode(target: str) -> RemoteBranchResult:
    return RemoteBranchResult('remote-mode', target, 'ok', f'Remote runtime branched to {target!r}. Handshake complete.')


def run_ssh_mode(target: str) -> RemoteBranchResult:
    return RemoteBranchResult('ssh-mode', target, 'ok', f'SSH tunnel established to {target!r}.')


def run_teleport_mode(target: str) -> RemoteBranchResult:
    return RemoteBranchResult('teleport-mode', target, 'ok', f'Teleport proxy activated for {target!r}.')


def run_direct_connect(target: str) -> RemoteBranchResult:
    return RemoteBranchResult('direct-connect', target, 'ok', f'Direct connection to {target!r} established.')


def run_deep_link(target: str) -> RemoteBranchResult:
    return RemoteBranchResult('deep-link', target, 'ok', f'Deep-link decoded and routed to {target!r}.')
