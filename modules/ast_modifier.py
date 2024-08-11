# modules/ast_modifier.py

import libcst as cst
import libcst.matchers as m
import logging
from typing import List

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ASTModifier(cst.CSTTransformer):
    def __init__(self, known_plugins: List[str]):
        self.known_plugins = known_plugins
        self.modified_functions = []

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
         # modify function definitions that have known Polars decorators
        if original_node.name.value in self.known_plugins:
            logger.info(f"Modifying function: {original_node.name.value}")
            modified_node = self._add_type_annotations(updated_node)
            self.modified_functions.append(original_node.name.value)
            return modified_node
        return updated_node

    # should be tailored to match the specific types used in a codebase
    def _add_type_annotations(self, node: cst.FunctionDef) -> cst.FunctionDef:
        logger.info(f"Adding type annotations to function: {node.name.value}")
        # example specific return type
        return_type = cst.Annotation(annotation=cst.Name("Union[str, int]"))
        
        # annotate parameters with example types
        parameters = []
        for param in node.params.params:
            param_name = param.name.value
            param_annotation = cst.Annotation(annotation=cst.Name("Any"))  # default to Any
            if param.default is not None:
                param_annotation = cst.Annotation(annotation=cst.Name("Optional[Any]"))
            elif param_name == 'df':
                param_annotation = cst.Annotation(annotation=cst.Name("DataFrame"))  # example for a DataFrame
            elif param_name == 'value':
                param_annotation = cst.Annotation(annotation=cst.Name("int"))  # example for an int parameter
            elif param_name == 'name':
                param_annotation = cst.Annotation(annotation=cst.Name("str"))  # example for a str parameter
            parameters.append(param.with_changes(annotation=param_annotation))

        # update return type
        updated_node = node.with_changes(
            params=node.params.with_changes(params=parameters),
            returns=return_type
        )

        logger.info(f"Added type annotations to function: {node.name.value}")
        return updated_node

    def modify_ast(self, code: str) -> str:
        # Parse the code and modify the AST based on known Polars decorators
        try:
            logger.info("Starting AST modification...")
            module = cst.parse_module(code)
            modified_module = module.visit(self)
            logger.info("AST modification complete.")
            return modified_module.code
        except cst.ParserSyntaxError as e:
            logger.error(f"Error parsing code: {e}")
            return code

def modify_code(code: str, known_plugins: List[str]) -> str:
    # Helper function to modify the AST of the provided code
    modifier = ASTModifier(known_plugins)
    return modifier.modify_ast(code)

# Example testing
if __name__ == "__main__":
    from modules.plugin_scanner import scan_plugins_in_code
    
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
    modified_code = modify_code(sample_code, plugins)
    print("Modified code:", modified_code)
