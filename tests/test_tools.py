"""Tests for src/tools.py"""

import unittest
from src.tools import (
    get_tool,
    get_tools,
    find_tools,
    execute_tool,
    render_tool_index,
    build_tool_backlog,
    AGENT_TOOLS,
    LIVE_TOOL_REGISTRY,
)
from src.permissions import ToolPermissionContext


class TestGetTool(unittest.TestCase):
    def test_get_existing_tool(self):
        tool = get_tool('BashTool')
        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, 'BashTool')

    def test_get_tool_case_insensitive(self):
        self.assertIsNotNone(get_tool('bashtool'))
        self.assertIsNotNone(get_tool('BASHTOOL'))

    def test_get_nonexistent_tool(self):
        self.assertIsNone(get_tool('NonExistentTool'))


class TestGetTools(unittest.TestCase):
    def test_all_tools_returned(self):
        tools = get_tools()
        self.assertGreater(len(tools), 0)

    def test_simple_mode(self):
        tools = get_tools(simple_mode=True)
        names = {t.name for t in tools}
        self.assertIn('BashTool', names)
        self.assertIn('FileReadTool', names)

    def test_no_mcp(self):
        tools_with_mcp = get_tools(include_mcp=True)
        tools_without_mcp = get_tools(include_mcp=False)
        self.assertLessEqual(len(tools_without_mcp), len(tools_with_mcp))

    def test_permission_context_blocks_tool(self):
        ctx = ToolPermissionContext.from_iterables(denied_tools=['BashTool'])
        tools = get_tools(permission_context=ctx)
        names = {t.name for t in tools}
        self.assertNotIn('BashTool', names)

    def test_tag_filter(self):
        tools = get_tools(tags=['exec'])
        self.assertTrue(all('exec' in t.tags or 'shell' in t.tags for t in tools))


class TestFindTools(unittest.TestCase):
    def test_find_by_name(self):
        matches = find_tools('bash')
        self.assertTrue(any('Bash' in t.name for t in matches))

    def test_find_limit(self):
        matches = find_tools('tool', limit=2)
        self.assertLessEqual(len(matches), 2)

    def test_find_no_match(self):
        matches = find_tools('zzznomatch')
        self.assertEqual(len(matches), 0)


class TestExecuteTool(unittest.TestCase):
    def test_execute_json_parse(self):
        result = execute_tool('JsonParseTool', '{"key": "value"}')
        self.assertTrue(result.handled)
        self.assertEqual(result.output, {'key': 'value'})

    def test_execute_unknown(self):
        result = execute_tool('DoesNotExist', 'payload')
        self.assertFalse(result.handled)
        self.assertIn('Unknown', result.message)


class TestRenderToolIndex(unittest.TestCase):
    def test_render_returns_string(self):
        output = render_tool_index()
        self.assertIsInstance(output, str)
        self.assertIn('Tool entries', output)

    def test_render_with_query(self):
        output = render_tool_index(query='bash')
        self.assertIn('Filtered by', output)


class TestBuildToolBacklog(unittest.TestCase):
    def test_backlog_title(self):
        backlog = build_tool_backlog()
        self.assertEqual(backlog.title, 'Tool surface')

    def test_backlog_modules(self):
        backlog = build_tool_backlog()
        self.assertGreater(len(backlog.modules), 0)


if __name__ == '__main__':
    unittest.main()
