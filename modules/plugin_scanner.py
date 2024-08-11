import libcst as cst
import libcst.matchers as m
import logging
from typing import Optional, Set, List

from modules.utils import load_known_decorators

# set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PluginScanner(cst.CSTVisitor):
    def __init__(self, known_polars_decorators: Optional[Set[str]] = None, config_path="config/config.toml"):
        # initialize the scanner with known Polars decorators
        if known_polars_decorators is None:
            known_polars_decorators = load_known_decorators(config_path=config_path, logger=logger)
        self.known_polars_decorators = known_polars_decorators
        self.plugins: List[str] = []

    def visit_FunctionDef(self, node: cst.FunctionDef):
        # visit each function definition and check if it's decorated with a known Polars decorator
        if node.decorators:
            for decorator in node.decorators:
                if self._is_polars_decorator(decorator.decorator):
                    self.plugins.append(node.name.value)
                    logger.info(f"Detected plugin: {node.name.value}")

    def _is_polars_decorator(self, decorator: cst.CSTNode) -> bool:
        # check if the decorator matches any known Polars-related decorators
        if m.matches(decorator, m.Call(func=m.Name()) | m.Name()):
            func_name = decorator.func.value if isinstance(decorator, cst.Call) else decorator.value
            if func_name in self.known_polars_decorators:
                return True
        
        if m.matches(decorator, m.Attribute(value=m.Name("pl"), attr=m.Name())):
            return decorator.attr.value in self.known_polars_decorators
        
        logger.warning(f"Unknown decorator pattern: {decorator}")
        return False

    def scan_plugins(self, code: str) -> List[str]:
        # parse the code and scan for functions decorated as plugins
        try:
            logger.info("Starting scan...")
            module = cst.parse_module(code)
            module.visit(self)
            return self.plugins
        except cst.ParserSyntaxError as e:
            logger.error(f"Error parsing code: {e}")
            return []

def scan_plugins_in_code(code: str, known_decorators: Optional[Set[str]] = None) -> List[str]:
    # helper function to scan the code for Polars plugins
    scanner = PluginScanner(known_decorators)
    return scanner.scan_plugins(code)

# example testing
if __name__ == "__main__":
    sample_code = """
import polars as pl

@pl.api.custom_function
def my_plugin(df):
    return df

@pl.api.another_plugin
def another_plugin(df):
    return df

@other_decorator
def not_a_plugin(df):
    return df
    """

    plugins = scan_plugins_in_code(sample_code)
    print("Found plugins:", plugins)
