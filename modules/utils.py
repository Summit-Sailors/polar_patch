# modules/utils.py

import toml
import logging

def load_known_decorators(config_path: str, logger: logging.Logger) -> set:
    try:
        config = toml.load(config_path)
        decorators = {k for k, v in config.get("decorators", {}).items() if v}
        if not decorators:
            logger.warning("No known decorators found in the configuration.")
        return decorators
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        logger.error(f"Failed to load configuration: {e}")
        return set()
