# tests/test_ast_modifierpy

import unittest
from modules.ast_modifier import modify_code
from modules.utils import load_known_decorators
import logging

class TestASTModifier(unittest.TestCase):
    
    def setUp(self):
        # Load known plugins from the config file
        self.known_plugins = list(load_known_decorators('config/config.toml', logging.getLogger(__name__)))
    
    def test_modify_plugin_function(self):
        # Test modification of a function decorated with a known plugin
        code = """
import polars as pl

@pl.api.custom_function
def my_plugin(df):
    return df
"""
        expected_code = """
import polars as pl

@pl.api.custom_function
def my_plugin(df: DataFrame) -> Union[str, int]:
    return df
"""
        modified_code = modify_code(code, self.known_plugins)
        self.assertEqual(modified_code.strip(), expected_code.strip())

    def test_non_plugin_function(self):
        # Test that non-plugin functions are not modified
        code = """
def regular_function(df):
    return df
"""
        modified_code = modify_code(code, self.known_plugins)
        self.assertEqual(modified_code.strip(), code.strip())

    def test_unknown_decorator(self):
        # Test that functions with unknown decorators are not modified
        code = """
import polars as pl

@pl.api.unknown_plugin
def unknown_plugin_function(df):
    return df
"""
        modified_code = modify_code(code, self.known_plugins)
        self.assertEqual(modified_code.strip(), code.strip())

    def test_plugin_with_parameters(self):
        # Test modification of a function with parameters decorated with a known plugin
        code = """
import polars as pl

@pl.api.custom_function
def my_plugin(df, value, name="default"):
    return df
"""
        expected_code = """
import polars as pl

@pl.api.custom_function
def my_plugin(df: DataFrame, value: int, name: Optional[str] = "default") -> Union[str, int]:
    return df
"""
        modified_code = modify_code(code, self.known_plugins)
        self.assertEqual(modified_code.strip(), expected_code.strip())

if __name__ == '__main__':
    unittest.main()
