"""crawl-code: Advanced AI agent harness runtime."""

__version__ = '1.0.0'
__author__ = 'mayankbot01'
__description__ = 'Advanced AI agent harness runtime — inspired by claw-code'

from .models import AgentModule, AgentBacklog, TurnResult, UsageSummary, PersistedSession
from .permissions import ToolPermissionContext
from .tools import AGENT_TOOLS, get_tool, get_tools, execute_tool
from .commands import AGENT_COMMANDS, get_command, get_commands, execute_command
from .context import PortContext, build_port_context
from .history import HistoryLog
from .session_store import TranscriptStore, load_session, persist_session
from .query_engine import QueryEnginePort, QueryEngineConfig
from .runtime import PortRuntime, RuntimeSession, RoutedMatch

__all__ = [
    '__version__',
    'AgentModule',
    'AgentBacklog',
    'TurnResult',
    'UsageSummary',
    'PersistedSession',
    'ToolPermissionContext',
    'AGENT_TOOLS',
    'get_tool',
    'get_tools',
    'execute_tool',
    'AGENT_COMMANDS',
    'get_command',
    'get_commands',
    'execute_command',
    'PortContext',
    'build_port_context',
    'HistoryLog',
    'TranscriptStore',
    'load_session',
    'persist_session',
    'QueryEnginePort',
    'QueryEngineConfig',
    'PortRuntime',
    'RuntimeSession',
    'RoutedMatch',
]
