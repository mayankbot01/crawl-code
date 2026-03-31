from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import PersistedSession


DEFAULT_STORE_DIR = Path.home() / '.crawl-code' / 'sessions'


@dataclass
class TranscriptStore:
    session_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    flushed: bool = False
    store_dir: Path = field(default_factory=lambda: DEFAULT_STORE_DIR)

    def append(self, role: str, content: str, **kwargs: Any) -> None:
        self.messages.append({'role': role, 'content': content, 'ts': time.time(), **kwargs})

    def flush(self) -> Path:
        self.store_dir.mkdir(parents=True, exist_ok=True)
        path = self.store_dir / f'{self.session_id}.json'
        data = {
            'session_id': self.session_id,
            'messages': self.messages,
            'flushed_at': time.time(),
        }
        path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        self.flushed = True
        return path

    def token_count(self) -> int:
        return sum(len(m.get('content', '').split()) for m in self.messages)


def persist_session(
    session_id: str,
    messages: list[dict[str, Any]],
    input_tokens: int = 0,
    output_tokens: int = 0,
    store_dir: Path | None = None,
) -> Path:
    store = store_dir or DEFAULT_STORE_DIR
    store.mkdir(parents=True, exist_ok=True)
    path = store / f'{session_id}.json'
    session = PersistedSession(
        session_id=session_id,
        messages=messages,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    path.write_text(json.dumps(session.to_dict(), indent=2), encoding='utf-8')
    return path


def load_session(
    session_id: str,
    store_dir: Path | None = None,
) -> PersistedSession:
    store = store_dir or DEFAULT_STORE_DIR
    path = store / f'{session_id}.json'
    if not path.exists():
        raise FileNotFoundError(f'Session not found: {session_id} (looked in {store})')
    data = json.loads(path.read_text(encoding='utf-8'))
    return PersistedSession(
        session_id=data['session_id'],
        messages=data['messages'],
        input_tokens=data.get('input_tokens', 0),
        output_tokens=data.get('output_tokens', 0),
        created_at=data.get('created_at', 0.0),
        metadata=data.get('metadata', {}),
    )


def list_sessions(store_dir: Path | None = None) -> list[str]:
    store = store_dir or DEFAULT_STORE_DIR
    if not store.exists():
        return []
    return [p.stem for p in sorted(store.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)]


def delete_session(session_id: str, store_dir: Path | None = None) -> bool:
    store = store_dir or DEFAULT_STORE_DIR
    path = store / f'{session_id}.json'
    if path.exists():
        path.unlink()
        return True
    return False


def new_session_id() -> str:
    return str(uuid.uuid4())
