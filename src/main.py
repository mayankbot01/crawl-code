from __future__ import annotations

import argparse

from .commands import execute_command, get_command, get_commands, render_command_index
from .context import build_port_context
from .permissions import ToolPermissionContext
from .query_engine import QueryEnginePort
from .runtime import PortRuntime, run_deep_link, run_direct_connect, run_remote_mode, run_ssh_mode, run_teleport_mode
from .session_store import load_session, list_sessions
from .tools import execute_tool, get_tool, get_tools, render_tool_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='crawl-code',
        description='Advanced AI agent harness runtime — crawl-code',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('summary', help='Render agent summary with tools and commands')
    subparsers.add_parser('doctor', help='Run environment health checks')
    subparsers.add_parser('version', help='Print version info')

    list_p = subparsers.add_parser('subsystems', help='List registered subsystems')
    list_p.add_argument('--limit', type=int, default=32)

    cmds_p = subparsers.add_parser('commands', help='List registered commands')
    cmds_p.add_argument('--limit', type=int, default=20)
    cmds_p.add_argument('--query')
    cmds_p.add_argument('--no-plugin-commands', action='store_true')
    cmds_p.add_argument('--no-skill-commands', action='store_true')

    tools_p = subparsers.add_parser('tools', help='List registered tools')
    tools_p.add_argument('--limit', type=int, default=20)
    tools_p.add_argument('--query')
    tools_p.add_argument('--simple-mode', action='store_true')
    tools_p.add_argument('--no-mcp', action='store_true')
    tools_p.add_argument('--deny-tool', action='append', default=[])
    tools_p.add_argument('--deny-prefix', action='append', default=[])

    route_p = subparsers.add_parser('route', help='Route a prompt to matching tools/commands')
    route_p.add_argument('prompt')
    route_p.add_argument('--limit', type=int, default=5)

    boot_p = subparsers.add_parser('bootstrap', help='Bootstrap a runtime session from a prompt')
    boot_p.add_argument('prompt')
    boot_p.add_argument('--limit', type=int, default=5)

    loop_p = subparsers.add_parser('turn-loop', help='Run a stateful agent turn loop')
    loop_p.add_argument('prompt')
    loop_p.add_argument('--limit', type=int, default=5)
    loop_p.add_argument('--max-turns', type=int, default=3)
    loop_p.add_argument('--structured-output', action='store_true')

    flush_p = subparsers.add_parser('flush-transcript', help='Flush and persist session transcript')
    flush_p.add_argument('prompt')

    load_p = subparsers.add_parser('load-session', help='Load a persisted session by ID')
    load_p.add_argument('session_id')

    sessions_p = subparsers.add_parser('list-sessions', help='List all persisted sessions')

    remote_p = subparsers.add_parser('remote-mode', help='Branch to remote runtime')
    remote_p.add_argument('target')

    ssh_p = subparsers.add_parser('ssh-mode', help='Branch to SSH runtime')
    ssh_p.add_argument('target')

    tel_p = subparsers.add_parser('teleport-mode', help='Branch via Teleport proxy')
    tel_p.add_argument('target')

    dc_p = subparsers.add_parser('direct-connect-mode', help='Direct connect runtime branch')
    dc_p.add_argument('target')

    dl_p = subparsers.add_parser('deep-link-mode', help='Deep-link runtime branch')
    dl_p.add_argument('target')

    sc_p = subparsers.add_parser('show-command', help='Show command details by name')
    sc_p.add_argument('name')

    st_p = subparsers.add_parser('show-tool', help='Show tool details by name')
    st_p.add_argument('name')

    ec_p = subparsers.add_parser('exec-command', help='Execute a command by name')
    ec_p.add_argument('name')
    ec_p.add_argument('prompt')

    et_p = subparsers.add_parser('exec-tool', help='Execute a tool by name')
    et_p.add_argument('name')
    et_p.add_argument('payload')

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == 'summary':
        print(QueryEnginePort.from_workspace().render_summary())
        return 0

    if args.command == 'doctor':
        result = execute_command('doctor', '')
        print(result.result or result.message)
        return 0

    if args.command == 'version':
        result = execute_command('version', '')
        print(result.result or result.message)
        return 0

    if args.command == 'subsystems':
        tools = get_tools()[:args.limit]
        for t in tools:
            print(f'{t.name}\t{t.status}\t{t.responsibility}')
        return 0

    if args.command == 'commands':
        if args.query:
            print(render_command_index(limit=args.limit, query=args.query))
        else:
            commands = get_commands(
                include_plugin_commands=not args.no_plugin_commands,
                include_skill_commands=not args.no_skill_commands,
            )
            print(f'Command entries: {len(commands)}')
            for c in commands[:args.limit]:
                print(f'- {c.name} \u2014 {c.responsibility}')
        return 0

    if args.command == 'tools':
        if args.query:
            print(render_tool_index(limit=args.limit, query=args.query))
        else:
            perm = ToolPermissionContext.from_iterables(args.deny_tool, args.deny_prefix)
            tools = get_tools(simple_mode=args.simple_mode, include_mcp=not args.no_mcp, permission_context=perm)
            print(f'Tool entries: {len(tools)}')
            for t in tools[:args.limit]:
                print(f'- {t.name} [{t.status}] \u2014 {t.responsibility}')
        return 0

    if args.command == 'route':
        matches = PortRuntime().route_prompt(args.prompt, limit=args.limit)
        if not matches:
            print('No matches found.')
            return 0
        for m in matches:
            print(f'{m.kind}\t{m.name}\t{m.score}\t{m.source_hint}')
        return 0

    if args.command == 'bootstrap':
        print(PortRuntime().bootstrap_session(args.prompt, limit=args.limit).as_markdown())
        return 0

    if args.command == 'turn-loop':
        results = PortRuntime().run_turn_loop(
            args.prompt, limit=args.limit, max_turns=args.max_turns,
            structured_output=args.structured_output
        )
        for r in results:
            print(f'## Turn {r.turn_index}')
            print(r.output)
            print(f'stop_reason={r.stop_reason}')
        return 0

    if args.command == 'flush-transcript':
        engine = QueryEnginePort.from_workspace()
        engine.submit_message(args.prompt)
        path = engine.persist_session()
        print(path)
        print(f'flushed={engine.transcript_store.flushed}')
        return 0

    if args.command == 'load-session':
        session = load_session(args.session_id)
        print(f'{session.session_id}\n{len(session.messages)} messages\nin={session.input_tokens} out={session.output_tokens}')
        return 0

    if args.command == 'list-sessions':
        sessions = list_sessions()
        if not sessions:
            print('No persisted sessions found.')
        for s in sessions:
            print(s)
        return 0

    if args.command == 'remote-mode':
        print(run_remote_mode(args.target).as_text())
        return 0
    if args.command == 'ssh-mode':
        print(run_ssh_mode(args.target).as_text())
        return 0
    if args.command == 'teleport-mode':
        print(run_teleport_mode(args.target).as_text())
        return 0
    if args.command == 'direct-connect-mode':
        print(run_direct_connect(args.target).as_text())
        return 0
    if args.command == 'deep-link-mode':
        print(run_deep_link(args.target).as_text())
        return 0

    if args.command == 'show-command':
        module = get_command(args.name)
        if module is None:
            print(f'Command not found: {args.name}')
            return 1
        print(f'{module.name}\n{module.source_hint}\n{module.responsibility}')
        return 0

    if args.command == 'show-tool':
        module = get_tool(args.name)
        if module is None:
            print(f'Tool not found: {args.name}')
            return 1
        print(f'{module.name}\n{module.source_hint}\n{module.responsibility}')
        return 0

    if args.command == 'exec-command':
        result = execute_command(args.name, args.prompt)
        print(result.message)
        return 0 if result.handled else 1

    if args.command == 'exec-tool':
        result = execute_tool(args.name, args.payload)
        print(result.message)
        return 0 if result.handled else 1

    parser.error(f'unknown command: {args.command}')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
