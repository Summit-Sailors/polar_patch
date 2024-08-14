# modules/ast_modifier.py

import libcst as cst
import logging
from typing import List

from polar_patch.utils import infer_type_from_default, infer_type_from_name

# logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ASTModifier(cst.CSTTransformer):
    def __init__(self, known_plugins: List[str], default_type: str = "Any"):
        self.known_plugins = known_plugins
        self.modified_functions = []
        self.default_type = default_type # default type for dynamic annotations

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        # modify function definitions that have known Polars decorators
        for decorator in original_node.decorators:
            # handle both simple names and attributes in decorators
            decorator_name = None
            if isinstance(decorator.decorator, cst.Name):
                decorator_name = decorator.decorator.value
            elif isinstance(decorator.decorator, cst.Attribute):
                decorator_name = decorator.decorator.attr.value

            if decorator_name in self.known_plugins:
                logger.info(f"Modifying function: {original_node.name.value}")
                modified_node = self._add_type_annotations(updated_node)
                self.modified_functions.append(original_node.name.value)
                return modified_node

        return updated_node

    def _add_type_annotations(self, node: cst.FunctionDef) -> cst.FunctionDef:
        logger.info(f"Adding type annotations to function: {node.name.value}")
        updated_params = []

        for param in node.params.params:
            # only add annotation if it doesn't already exist
            if param.annotation is None:
                param_type = self._determine_param_type(param)
                updated_params.append(
                    param.with_changes(annotation=cst.Annotation(annotation=cst.Name(param_type)))
                )
            else:
                updated_params.append(param)

        # add return type annotation if not present
        if node.returns is None:
            return_type = cst.Annotation(annotation=cst.Name(self.default_type))
            node = node.with_changes(returns=return_type)

        return node.with_changes(params=cst.Parameters(params=updated_params))
    
    def _determine_param_type(self, param: cst.Param) -> str:
        """Determine the type of the parameter using configuration-based inference."""
        if param.default:
            inferred_type = infer_type_from_default(param.default)
            if inferred_type:
                return inferred_type
        
        inferred_type = infer_type_from_name(param.name.value)
        if inferred_type:
            return inferred_type
        
        return self.default_type  # fallback to a default type if no inference is possible


    def modify_ast(self, code: str) -> str:
        # parse the code and modify the AST based on known Polars decorators
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
    # helper function to modify the AST of the provided code
    modifier = ASTModifier(known_plugins)
    return modifier.modify_ast(code)

# Example testing
if __name__ == "__main__":
    from polar_patch.plugin_scanner import scan_plugins_in_code
    
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
