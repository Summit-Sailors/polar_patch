# modules/plugin_scanner.py

import libcst as cst
import libcst.matchers as m

class PluginScanner(cst.CSTVisitor):
    """
    PluginScanner scans Python code to identify functions decorated with specific Polars decorators.
    """
    def __init__(self, known_polars_decorators=None):
        if known_polars_decorators is None:
            known_polars_decorators = {"custom_function", "another_plugin"}
        self.known_polars_decorators = known_polars_decorators
        self.plugins = []

    def visit_FunctionDef(self, node: cst.FunctionDef):
        """
        This method is called for every function definition in the code.
        It checks if the function is decorated with any known Polars decorators.
        """
        if node.decorators:
            for decorator in node.decorators:
                if self._is_polars_decorator(decorator.decorator):
                    self.plugins.append(node.name.value)

    def _is_polars_decorator(self, decorator: cst.CSTNode) -> bool:
        """
        Checks if a given decorator is one of the known Polars-related decorators.
        It matches against both fully qualified names (e.g., pl.api.custom_function)
        and directly imported decorator names.
        """
        # Match a pattern like `@pl.api.custom_function`
        if m.matches(decorator, m.Attribute(value=m.Name("pl"), attr=m.Name())):
            return True
        
        # Match directly imported decorator names (e.g., `@custom_function`)
        if m.matches(decorator, m.Name()):
            return decorator.value in self.known_polars_decorators
        
        return False

    def scan_plugins(self, code: str):
        """
        Scans the provided code string for functions decorated with known Polars decorators.
        Returns a list of function names that are Polars plugins.
        """
        module = cst.parse_module(code)
        module.visit(self)
        return self.plugins

