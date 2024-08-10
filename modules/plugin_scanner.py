# modules/plugin_scanner.py

import libcst as cst
import libcst.matchers as m
import logging

# logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PluginScanner(cst.CSTVisitor):
    """
    PluginScanner scans Python code to identify functions decorated with specific Polars decorators.
    """
    def __init__(self, known_polars_decorators=None):
        if known_polars_decorators is None:
            known_polars_decorators = {"custom_function", "another_plugin"}  # Placeholder for any custom decorators
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
                    logger.info(f"Detected plugin: {node.name.value}")

    def _is_polars_decorator(self, decorator: cst.CSTNode) -> bool:
        """
        Checks if a given decorator is one of the known Polars-related decorators.
        It matches against both fully qualified names (e.g., pl.api.custom_function)
        and directly imported decorator names with or without arguments.
        """
        # Match directly imported decorator names (e.g., `@custom_function` or `@custom_function(arg=True)`)
        if m.matches(decorator, m.Call(func=m.Name()) | m.Name()):
            func_name = decorator.func.value if isinstance(decorator, cst.Call) else decorator.value
            return func_name in self.known_polars_decorators

        # Match a pattern like `@pl.api.custom_function`
        if m.matches(decorator, m.Attribute(value=m.Name("pl"), attr=m.Name())):
            return decorator.attr.value in self.known_polars_decorators

        # Log if the decorator does not match known patterns
        logger.warning(f"Unknown decorator pattern: {decorator}")

        return False

    def scan_plugins(self, code: str):
        """
        Scans the provided code string for functions decorated with known Polars decorators.
        Returns a list of function names that are Polars plugins.
        """
        try:
            logger.info("Starting scan...")
            module = cst.parse_module(code)
            module.visit(self)
            return self.plugins
        except cst.ParserSyntaxError as e:
            logger.error(f"Error parsing code: {e}")
            return []

def scan_plugins_in_code(code: str, known_decorators=None):
    scanner = PluginScanner(known_decorators)
    return scanner.scan_plugins(code)
