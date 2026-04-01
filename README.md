# crawl-code

**Advanced AI agent harness runtime — inspired by [claw-code](https://github.com/instructkr/claw-code).**

> Same architecture. New code. Real execution. Built from scratch in Python.

---

## What is crawl-code?

`crawl-code` is a clean-room Python implementation of an AI agent harness runtime.
Inspired by the architectural patterns of `claw-code`, it provides a **fully functional** agent loop with:

- **Real tool execution** (BashTool, FileReadTool, FileWriteTool, ListDirTool, JsonParseTool)
- **Live command registry** (11 built-in commands with aliases)
- **Session persistence** (JSON-based transcript store)
- **Permission contexts** (role-based tool access control)
- **Turn loop runtime** (multi-turn agent conversation loop with tool routing)
- **Remote mode branching** (ssh, teleport, direct-connect, deep-link)
- **25+ CLI subcommands** via `python3 -m src.main`

---

## Repository Layout

```
.
├── src/                        # Core Python workspace
│   ├── __init__.py             # Package exports and version
│   ├── models.py               # AgentModule, TurnResult, UsageSummary, PersistedSession
│   ├── permissions.py          # ToolPermissionContext with role-based access
│   ├── tools.py                # LiveTool registry with real execution handlers
│   ├── commands.py             # LiveCommand registry with 11 built-in commands
│   ├── context.py              # PortContext with workspace environment builder
│   ├── history.py              # HistoryLog with conversation entry management
│   ├── session_store.py        # TranscriptStore with JSON session persistence
│   ├── query_engine.py         # QueryEnginePort with tool routing and response gen
│   ├── runtime.py              # PortRuntime with turn loop and remote mode branching
│   └── main.py                 # CLI entrypoint (25+ subcommands)
├── tests/                      # Unit tests
│   ├── test_tools.py           # Tests for tool registry and execution
│   └── test_runtime.py         # Tests for runtime, remote modes, and commands
├── .gitignore
└── README.md
```

---

## Quickstart

```bash
git clone https://github.com/mayankbot01/crawl-code
cd crawl-code
```

### Render agent summary
```bash
python3 -m src.main summary
```

### List all tools
```bash
python3 -m src.main tools
```

### List all commands
```bash
python3 -m src.main commands
```

### Route a prompt
```bash
python3 -m src.main route "read a file"
```

### Run a turn loop
```bash
python3 -m src.main turn-loop "list all python files" --max-turns 3
```

### Execute a tool directly
```bash
python3 -m src.main exec-tool JsonParseTool '{"hello": "world"}'
```

### Execute a command
```bash
python3 -m src.main exec-command version ""
python3 -m src.main exec-command doctor ""
```

### Remote mode branching
```bash
python3 -m src.main ssh-mode user@myserver.com
python3 -m src.main remote-mode my-cluster
```

### Flush and persist a session
```bash
python3 -m src.main flush-transcript "write a hello world script"
```

---

## Run Tests

```bash
python3 -m unittest discover -s tests -v
```

---

## Registered Tools

| Tool | Status | Description |
|------|--------|-------------|
| BashTool | active | Execute shell commands |
| FileReadTool | active | Read file contents from disk |
| FileWriteTool | active | Write content to disk |
| ListDirTool | active | List directory entries |
| JsonParseTool | active | Parse JSON payload into Python objects |
| WebFetchTool | planned | Fetch remote URLs and return content |
| MCPTool | planned | Model Context Protocol tool bridge |
| MemoryTool | planned | Persist and retrieve agent memory across turns |

---

## Registered Commands

| Command | Aliases | Type | Description |
|---------|---------|------|-------------|
| help | ?, h | core | Show available commands |
| clear | cls | core | Clear terminal output |
| status | | core | Show agent runtime status |
| version | --version, -v | core | Print version info |
| config | | core | Read/write config values |
| doctor | | core | Run environment health checks |
| init | | core | Initialize project workspace |
| diff | | core | Show diff for a path |
| memory | | skill | Query agent memory store |
| review | | skill | Request code review |
| mcp | | plugin | Start MCP bridge |

---

## Architecture Highlights

- **`PortRuntime`** — routes prompts against tool and command registries, runs multi-turn loops with real tool dispatch
- **`QueryEnginePort`** — stateful session engine with history tracking, token estimation, and transcript persistence
- **`ToolPermissionContext`** — immutable permission model with denied tools, denied prefixes, allowed tools, and strict mode
- **`HistoryLog`** — bounded message history with markdown rendering and token estimation
- **`TranscriptStore`** — per-session JSON file store at `~/.crawl-code/sessions/`

---

## Disclaimer

- This repository is **not affiliated with, endorsed by, or maintained by Anthropic**.
- All code is original and written from scratch, inspired only by the architectural patterns documented in public sources.
- This is an independent open-source project.

---

*Built with Python 3.11+ | MIT License*
