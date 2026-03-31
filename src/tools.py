from __future__ import annotations

import subprocess
import os
import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from .models import AgentBacklog, AgentModule
from .permissions import ToolPermissionContext


@dataclass(frozen=True)
class ToolExecution:
    name: str
    source_hint: str
    payload: str
    handled: bool
    message: str
    output: Any = None
    exit_code: int = 0


@dataclass
class ToolRegistry:
    _tools: dict[str, 'LiveTool'] = field(default_factory=dict)

    def register(self, tool: 'LiveTool') -> None:
        self._tools[tool.name.lower()] = tool

    def get(self, name: str) -> 'LiveTool | None':
        return self._tools.get(name.lower())

    def all_names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, name: str, payload: str = '') -> ToolExecution:
        tool = self.get(name)
        if tool is None:
            return ToolExecution(name=name, source_hint='', payload=payload,
                                 handled=False, message=f'Unknown tool: {name}')
        return tool.run(payload)


@dataclass
class LiveTool:
    name: str
    description: str
    source_hint: str
    handler: Callable[[str], Any] = field(repr=False)

    def run(self, payload: str = '') -> ToolExecution:
        try:
            result = self.handler(payload)
            return ToolExecution(
                name=self.name,
                source_hint=self.source_hint,
                payload=payload,
                handled=True,
                message=f'Tool {self.name!r} executed successfully.',
                output=result,
                exit_code=0,
            )
        except Exception as exc:
            return ToolExecution(
                name=self.name,
                source_hint=self.source_hint,
                payload=payload,
                handled=False,
                message=f'Tool {self.name!r} failed: {exc}',
                output=None,
                exit_code=1,
            )


def _bash_handler(payload: str) -> str:
    result = subprocess.run(
        payload, shell=True, capture_output=True, text=True, timeout=30
    )
    return result.stdout + result.stderr


def _read_file_handler(payload: str) -> str:
    return Path(payload.strip()).read_text(encoding='utf-8')


def _write_file_handler(payload: str) -> str:
    parts = payload.split('|||', 1)
    if len(parts) != 2:
        raise ValueError('FileWriteTool expects payload as: <path>|||<content>')
    path, content = parts
    Path(path.strip()).write_text(content, encoding='utf-8')
    return f'Written to {path.strip()}'


def _list_dir_handler(payload: str) -> str:
    path = Path(payload.strip() or '.')
    entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
    return '\n'.join(str(e) for e in entries)


def _json_parse_handler(payload: str) -> Any:
    return json.loads(payload)


def build_live_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(LiveTool('BashTool', 'Execute shell commands safely', 'src/tools.py', _bash_handler))
    registry.register(LiveTool('FileReadTool', 'Read file contents', 'src/tools.py', _read_file_handler))
    registry.register(LiveTool('FileWriteTool', 'Write content to a file', 'src/tools.py', _write_file_handler))
    registry.register(LiveTool('ListDirTool', 'List directory contents', 'src/tools.py', _list_dir_handler))
    registry.register(LiveTool('JsonParseTool', 'Parse JSON payload', 'src/tools.py', _json_parse_handler))
    return registry


LIVE_TOOL_REGISTRY = build_live_tool_registry()


AGENT_TOOLS: tuple[AgentModule, ...] = (
    AgentModule(name='BashTool', responsibility='Execute shell commands', source_hint='src/tools.py', status='active', tags=('exec', 'shell'), priority=10),
    AgentModule(name='FileReadTool', responsibility='Read file contents from disk', source_hint='src/tools.py', status='active', tags=('io', 'read'), priority=9),
    AgentModule(name='FileWriteTool', responsibility='Write content to disk', source_hint='src/tools.py', status='active', tags=('io', 'write'), priority=8),
    AgentModule(name='ListDirTool', responsibility='List directory entries', source_hint='src/tools.py', status='active', tags=('io', 'read'), priority=7),
    AgentModule(name='JsonParseTool', responsibility='Parse JSON payload into Python objects', source_hint='src/tools.py', status='active', tags=('data',), priority=6),
    AgentModule(name='WebFetchTool', responsibility='Fetch remote URLs and return content', source_hint='src/tools.py', status='planned', tags=('network',), priority=5),
    AgentModule(name='MCPTool', responsibility='Model Context Protocol tool bridge', source_hint='src/tools.py', status='planned', tags=('mcp',), priority=4),
    AgentModule(name='MemoryTool', responsibility='Persist and retrieve agent memory across turns', source_hint='src/tools.py', status='planned', tags=('memory',), priority=3),
)


def get_tool(name: str) -> AgentModule | None:
    needle = name.lower()
    return next((t for t in AGENT_TOOLS if t.name.lower() == needle), None)


def get_tools(
    simple_mode: bool = False,
    include_mcp: bool = True,
    permission_context: ToolPermissionContext | None = None,
    tags: list[str] | None = None,
) -> tuple[AgentModule, ...]:
    tools = list(AGENT_TOOLS)
    if simple_mode:
        tools = [t for t in tools if t.name in {'BashTool', 'FileReadTool', 'FileWriteTool'}]
    if not include_mcp:
        tools = [t for t in tools if 'mcp' not in t.name.lower()]
    if tags:
        tools = [t for t in tools if any(tag in t.tags for tag in tags)]
    if permission_context:
        tools = [t for t in tools if permission_context.allows(t.name)]
    return tuple(sorted(tools, key=lambda t: -t.priority))


def find_tools(query: str, limit: int = 20) -> list[AgentModule]:
    needle = query.lower()
    return [
        t for t in AGENT_TOOLS
        if needle in t.name.lower() or needle in t.responsibility.lower() or needle in ' '.join(t.tags)
    ][:limit]


def execute_tool(name: str, payload: str = '') -> ToolExecution:
    return LIVE_TOOL_REGISTRY.execute(name, payload)


def render_tool_index(limit: int = 20, query: str | None = None) -> str:
    modules = find_tools(query, limit) if query else list(AGENT_TOOLS[:limit])
    lines = [f'Tool entries: {len(AGENT_TOOLS)}', '']
    if query:
        lines.append(f'Filtered by: {query}')
        lines.append('')
    lines.extend(f'- {t.name} [{t.status}] — {t.responsibility}' for t in modules)
    return '\n'.join(lines)


def build_tool_backlog() -> AgentBacklog:
    return AgentBacklog(title='Tool surface', modules=list(AGENT_TOOLS))
