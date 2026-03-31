from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import os
import time
import uuid


@dataclass
class PortContext:
    workspace_root: Path
    session_id: str
    model: str
    max_turns: int
    api_key: str
    environment: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self.workspace_root = Path(self.workspace_root).resolve()

    def as_dict(self) -> dict[str, Any]:
        return {
            'workspace_root': str(self.workspace_root),
            'session_id': self.session_id,
            'model': self.model,
            'max_turns': self.max_turns,
            'environment': self.environment,
            'metadata': self.metadata,
            'created_at': self.created_at,
        }

    def with_metadata(self, key: str, value: Any) -> 'PortContext':
        new_meta = {**self.metadata, key: value}
        return PortContext(
            workspace_root=self.workspace_root,
            session_id=self.session_id,
            model=self.model,
            max_turns=self.max_turns,
            api_key=self.api_key,
            environment=self.environment,
            metadata=new_meta,
        )


def build_port_context(
    workspace_root: str | Path | None = None,
    model: str = 'claude-opus-4-5',
    max_turns: int = 10,
    api_key: str = '',
) -> PortContext:
    root = Path(workspace_root).resolve() if workspace_root else Path.cwd()
    env = {
        'PYTHONPATH': str(root),
        'CRAWL_CODE_ROOT': str(root),
        'CRAWL_CODE_MODEL': model,
        'CRAWL_CODE_SESSION': str(uuid.uuid4()),
    }
    return PortContext(
        workspace_root=root,
        session_id=env['CRAWL_CODE_SESSION'],
        model=model,
        max_turns=max_turns,
        api_key=api_key or os.environ.get('ANTHROPIC_API_KEY', ''),
        environment=env,
    )


def render_context(ctx: PortContext) -> str:
    lines = [
        '## Context',
        f'- workspace: {ctx.workspace_root}',
        f'- session_id: {ctx.session_id}',
        f'- model: {ctx.model}',
        f'- max_turns: {ctx.max_turns}',
        f'- env_vars: {len(ctx.environment)}',
    ]
    return '\n'.join(lines)
