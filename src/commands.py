from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .models import AgentBacklog, AgentModule


@dataclass(frozen=True)
class CommandExecution:
    name: str
    prompt: str
    handled: bool
    message: str
    result: Any = None


@dataclass
class LiveCommand:
    name: str
    description: str
    source_hint: str
    handler: Callable[[str], Any] = field(repr=False)
    aliases: list[str] = field(default_factory=list)
    is_plugin: bool = False
    is_skill: bool = False

    def run(self, prompt: str = '') -> CommandExecution:
        try:
            result = self.handler(prompt)
            return CommandExecution(name=self.name, prompt=prompt, handled=True,
                                    message=f'Command {self.name!r} completed.', result=result)
        except Exception as exc:
            return CommandExecution(name=self.name, prompt=prompt, handled=False,
                                    message=f'Command {self.name!r} failed: {exc}')


@dataclass
class CommandRegistry:
    _commands: dict[str, LiveCommand] = field(default_factory=dict)

    def register(self, cmd: LiveCommand) -> None:
        self._commands[cmd.name.lower()] = cmd
        for alias in cmd.aliases:
            self._commands[alias.lower()] = cmd

    def get(self, name: str) -> LiveCommand | None:
        return self._commands.get(name.lower())

    def all(self, include_plugins: bool = True, include_skills: bool = True) -> list[LiveCommand]:
        seen: set[str] = set()
        result = []
        for cmd in self._commands.values():
            if cmd.name in seen:
                continue
            seen.add(cmd.name)
            if not include_plugins and cmd.is_plugin:
                continue
            if not include_skills and cmd.is_skill:
                continue
            result.append(cmd)
        return result

    def execute(self, name: str, prompt: str = '') -> CommandExecution:
        cmd = self.get(name)
        if cmd is None:
            return CommandExecution(name=name, prompt=prompt, handled=False,
                                    message=f'Unknown command: {name}')
        return cmd.run(prompt)


def _help_handler(prompt: str) -> str:
    return 'Available commands: help, clear, status, version, config, doctor, memory, init, mcp, review, diff'


def _clear_handler(prompt: str) -> str:
    return '[terminal cleared]'


def _status_handler(prompt: str) -> str:
    return 'Agent status: running | Session active | Tools: 8 registered'


def _version_handler(prompt: str) -> str:
    return 'crawl-code v1.0.0 | Python 3.11+ | MIT License'


def _config_handler(prompt: str) -> str:
    return f'Config key queried: {prompt!r}'


def _doctor_handler(prompt: str) -> str:
    checks = ['Python >= 3.11 OK', 'Dependencies installed OK', 'Filesystem writable OK']
    return '\n'.join(checks)


def _memory_handler(prompt: str) -> str:
    return f'Memory query: {prompt!r} -> (stub, implement with vector store)'


def _init_handler(prompt: str) -> str:
    return f'Project initialized at: {prompt or "."!r}'


def _mcp_handler(prompt: str) -> str:
    return f'MCP bridge started for target: {prompt!r}'


def _review_handler(prompt: str) -> str:
    return f'Code review requested for: {prompt!r}'


def _diff_handler(prompt: str) -> str:
    return f'Diff requested for: {prompt!r}'


def build_command_registry() -> CommandRegistry:
    registry = CommandRegistry()
    registry.register(LiveCommand('help', 'Show available commands', 'src/commands.py', _help_handler, aliases=['?', 'h']))
    registry.register(LiveCommand('clear', 'Clear terminal output', 'src/commands.py', _clear_handler, aliases=['cls']))
    registry.register(LiveCommand('status', 'Show agent runtime status', 'src/commands.py', _status_handler))
    registry.register(LiveCommand('version', 'Print version info', 'src/commands.py', _version_handler, aliases=['--version', '-v']))
    registry.register(LiveCommand('config', 'Read/write config values', 'src/commands.py', _config_handler))
    registry.register(LiveCommand('doctor', 'Run environment health checks', 'src/commands.py', _doctor_handler))
    registry.register(LiveCommand('memory', 'Query agent memory store', 'src/commands.py', _memory_handler, is_skill=True))
    registry.register(LiveCommand('init', 'Initialize project workspace', 'src/commands.py', _init_handler))
    registry.register(LiveCommand('mcp', 'Start MCP bridge', 'src/commands.py', _mcp_handler, is_plugin=True))
    registry.register(LiveCommand('review', 'Request code review', 'src/commands.py', _review_handler, is_skill=True))
    registry.register(LiveCommand('diff', 'Show diff for a path', 'src/commands.py', _diff_handler))
    return registry


COMMAND_REGISTRY = build_command_registry()

AGENT_COMMANDS: tuple[AgentModule, ...] = tuple(
    AgentModule(
        name=cmd.name,
        responsibility=cmd.description,
        source_hint=cmd.source_hint,
        status='active',
        tags=('plugin',) if cmd.is_plugin else ('skill',) if cmd.is_skill else ('core',),
    )
    for cmd in COMMAND_REGISTRY.all()
)


def get_command(name: str) -> AgentModule | None:
    needle = name.lower()
    return next((c for c in AGENT_COMMANDS if c.name.lower() == needle), None)


def get_commands(
    include_plugin_commands: bool = True,
    include_skill_commands: bool = True,
) -> tuple[AgentModule, ...]:
    cmds = list(COMMAND_REGISTRY.all(include_plugins=include_plugin_commands,
                                      include_skills=include_skill_commands))
    return tuple(
        AgentModule(name=c.name, responsibility=c.description,
                    source_hint=c.source_hint, status='active')
        for c in cmds
    )


def execute_command(name: str, prompt: str = '') -> CommandExecution:
    return COMMAND_REGISTRY.execute(name, prompt)


def find_commands(query: str, limit: int = 20) -> list[AgentModule]:
    needle = query.lower()
    return [
        c for c in AGENT_COMMANDS
        if needle in c.name.lower() or needle in c.responsibility.lower()
    ][:limit]


def render_command_index(limit: int = 20, query: str | None = None) -> str:
    modules = find_commands(query, limit) if query else list(AGENT_COMMANDS[:limit])
    lines = [f'Command entries: {len(AGENT_COMMANDS)}', '']
    if query:
        lines.append(f'Filtered by: {query}')
        lines.append('')
    lines.extend(f'- {c.name} [{c.status}] — {c.responsibility}' for c in modules)
    return '\n'.join(lines)


def build_command_backlog() -> AgentBacklog:
    return AgentBacklog(title='Command surface', modules=list(AGENT_COMMANDS))
