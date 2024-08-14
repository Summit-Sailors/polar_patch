# modules/utils.py

import toml
import libcst as cst
import logging

# Load the configuration
config = toml.load('config/config.toml')

def load_known_decorators(logger: logging.Logger) -> set:
    try:
        decorators = {k for k, v in config.get("decorators", {}).items() if v}
        if not decorators:
            logger.warning("No known decorators found in the configuration.")
        return decorators
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        logger.error(f"Failed to load configuration: {e}")
        return set()

def infer_type_from_default(default_value):
    """Infer the type from the default value using configuration."""
    if isinstance(default_value, cst.Integer):
        return "int"
    elif isinstance(default_value, cst.Float):
        return "float"
    elif isinstance(default_value, cst.BaseString):
        return "str"
    elif isinstance(default_value, cst.List):
        return "List[Any]"
    elif isinstance(default_value, cst.Dict):
        return "Dict[Any, Any]"
    elif isinstance(default_value, cst.Name):
        if default_value.value == "None":
            return "Optional[Any]"
        elif default_value.value in {"True", "False"}:
            return "bool"
    return None

def infer_type_from_name(name):
    """Infer the type from the parameter name using configuration (Heuristic-based inference)."""
    if any(keyword in name for keyword in config['parameter_names']['int_keywords']):
        return "int"
    elif any(keyword in name for keyword in config['parameter_names']['str_keywords']):
        return "str"
    elif any(keyword in name for keyword in config['parameter_names']['bool_keywords']):
        return "bool"
    return None
