from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class ToolPermissionContext:
    denied_tools: frozenset[str] = field(default_factory=frozenset)
    denied_prefixes: frozenset[str] = field(default_factory=frozenset)
    allowed_tools: frozenset[str] = field(default_factory=frozenset)
    strict_mode: bool = False

    @classmethod
    def from_iterables(
        cls,
        denied_tools: Iterable[str] = (),
        denied_prefixes: Iterable[str] = (),
        allowed_tools: Iterable[str] = (),
        strict_mode: bool = False,
    ) -> 'ToolPermissionContext':
        return cls(
            denied_tools=frozenset(t.lower() for t in denied_tools),
            denied_prefixes=frozenset(p.lower() for p in denied_prefixes),
            allowed_tools=frozenset(t.lower() for t in allowed_tools),
            strict_mode=strict_mode,
        )

    def blocks(self, tool_name: str) -> bool:
        name_lower = tool_name.lower()
        if self.strict_mode and self.allowed_tools:
            return name_lower not in self.allowed_tools
        if name_lower in self.denied_tools:
            return True
        return any(name_lower.startswith(prefix) for prefix in self.denied_prefixes)

    def allows(self, tool_name: str) -> bool:
        return not self.blocks(tool_name)

    def with_denied_tool(self, tool_name: str) -> 'ToolPermissionContext':
        return ToolPermissionContext(
            denied_tools=self.denied_tools | {tool_name.lower()},
            denied_prefixes=self.denied_prefixes,
            allowed_tools=self.allowed_tools,
            strict_mode=self.strict_mode,
        )

    def summary(self) -> str:
        parts = []
        if self.denied_tools:
            parts.append(f'denied={sorted(self.denied_tools)}')
        if self.denied_prefixes:
            parts.append(f'prefixes={sorted(self.denied_prefixes)}')
        if self.strict_mode:
            parts.append('strict=True')
        return 'ToolPermissionContext(' + ', '.join(parts) + ')'


DEFAULT_PERMISSION_CONTEXT = ToolPermissionContext()

SAFE_CONTEXT = ToolPermissionContext.from_iterables(
    denied_prefixes=['shell', 'exec', 'bash', 'system'],
)

READ_ONLY_CONTEXT = ToolPermissionContext.from_iterables(
    denied_tools=['FileEditTool', 'FileWriteTool', 'BashTool'],
    denied_prefixes=['write', 'exec', 'delete'],
)
