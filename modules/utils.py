import toml
import logging

def load_known_decorators(config_path: str, logger: logging.Logger) -> set:
    try:
        config = toml.load(config_path)
        decorators = set(config.get("polars", {}).get("known_decorators", []))
        if not decorators:
            logger.warning("No known decorators found in the configuration.")
        return decorators
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        logger.error(f"Failed to load configuration: {e}")
        return set()
