"""Tests for src/runtime.py and src/commands.py"""

import unittest
from src.runtime import (
    PortRuntime,
    run_remote_mode,
    run_ssh_mode,
    run_teleport_mode,
    run_direct_connect,
    run_deep_link,
)
from src.commands import (
    execute_command,
    get_command,
    get_commands,
    find_commands,
    render_command_index,
    COMMAND_REGISTRY,
)
from src.models import TurnResult


class TestPortRuntime(unittest.TestCase):
    def setUp(self):
        self.runtime = PortRuntime()

    def test_route_prompt_returns_matches(self):
        matches = self.runtime.route_prompt('read file contents', limit=5)
        self.assertIsInstance(matches, list)

    def test_route_prompt_empty(self):
        matches = self.runtime.route_prompt('zzznomatch', limit=5)
        self.assertEqual(len(matches), 0)

    def test_bootstrap_session_returns_session(self):
        session = self.runtime.bootstrap_session('run bash command')
        self.assertIsNotNone(session)
        self.assertGreater(len(session.turn_results), 0)

    def test_turn_loop_returns_results(self):
        results = self.runtime.run_turn_loop('list files', max_turns=2)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_turn_loop_max_turns(self):
        results = self.runtime.run_turn_loop('random', max_turns=3)
        self.assertLessEqual(len(results), 3)

    def test_turn_loop_structured_output(self):
        results = self.runtime.run_turn_loop('bash', max_turns=1, structured_output=True)
        self.assertTrue(len(results) > 0)


class TestRemoteModes(unittest.TestCase):
    def test_remote_mode(self):
        r = run_remote_mode('server1')
        self.assertEqual(r.mode, 'remote-mode')
        self.assertEqual(r.target, 'server1')
        self.assertEqual(r.status, 'ok')

    def test_ssh_mode(self):
        r = run_ssh_mode('user@host')
        self.assertIn('SSH', r.details)

    def test_teleport_mode(self):
        r = run_teleport_mode('cluster.local')
        self.assertIn('Teleport', r.details)

    def test_direct_connect(self):
        r = run_direct_connect('192.168.1.1')
        self.assertIn('Direct', r.details)

    def test_deep_link(self):
        r = run_deep_link('crawl://session/abc')
        self.assertIn('deep-link', r.mode)

    def test_as_text(self):
        r = run_remote_mode('target')
        text = r.as_text()
        self.assertIsInstance(text, str)
        self.assertIn('target', text)


class TestCommandRegistry(unittest.TestCase):
    def test_execute_help(self):
        result = execute_command('help', '')
        self.assertTrue(result.handled)

    def test_execute_version(self):
        result = execute_command('version', '')
        self.assertTrue(result.handled)
        self.assertIn('crawl-code', result.result)

    def test_execute_doctor(self):
        result = execute_command('doctor', '')
        self.assertTrue(result.handled)

    def test_execute_unknown(self):
        result = execute_command('nonexistent', '')
        self.assertFalse(result.handled)

    def test_alias_support(self):
        result = execute_command('?', '')
        self.assertTrue(result.handled)

    def test_get_command(self):
        cmd = get_command('help')
        self.assertIsNotNone(cmd)

    def test_get_commands_all(self):
        cmds = get_commands()
        self.assertGreater(len(cmds), 0)

    def test_get_commands_no_plugins(self):
        all_cmds = get_commands(include_plugin_commands=True)
        no_plugin = get_commands(include_plugin_commands=False)
        self.assertLessEqual(len(no_plugin), len(all_cmds))

    def test_find_commands(self):
        matches = find_commands('memory')
        self.assertTrue(any('memory' in c.name.lower() for c in matches))

    def test_render_command_index(self):
        output = render_command_index()
        self.assertIn('Command entries', output)


if __name__ == '__main__':
    unittest.main()
