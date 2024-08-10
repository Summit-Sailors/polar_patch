# tests/test_plugin_scanner.py

import unittest
from modules.plugin_scanner import scan_plugins_in_code

class TestPluginScanner(unittest.TestCase):
    def test_basic_detection(self):
        code = """
import polars as pl

@pl.api.custom_function
def my_plugin():
    pass
        """
        plugins = scan_plugins_in_code(code, known_decorators={"custom_function"})
        self.assertIn("my_plugin", plugins)

    def test_unknown_decorator(self):
        code = """
@unknown_decorator
def not_a_plugin():
    pass
        """
        plugins = scan_plugins_in_code(code, known_decorators={"custom_function"})
        self.assertNotIn("not_a_plugin", plugins)

    def test_decorator_with_arguments(self):
        code = """
import polars as pl

@custom_function(arg=True)
def another_plugin():
    pass
        """
        plugins = scan_plugins_in_code(code, known_decorators={"custom_function"})
        self.assertIn("another_plugin", plugins)

    def test_error_handling(self):
        code = """
def malformed_code(
"""
        plugins = scan_plugins_in_code(code, known_decorators={"custom_function"})
        self.assertEqual(plugins, [])

if __name__ == '__main__':
    unittest.main()
