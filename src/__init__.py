import json
from typing import Any
from pathlib import Path


def mount_plugins() -> None:
  pass


def unmount_plugins() -> None:
  pass


def setup_vscode() -> None:
  """Set up VSCode to use the JSON schema for polar_patch.toml."""
  current_dir = Path.cwd()
  vscode_settings_path = current_dir.joinpath(".vscode", "settings.json")
  schema_path = current_dir.joinpath("schemas", "polar_patch_schema.json")
  vscode_settings_path.parent.mkdir(parents=True, exist_ok=True)
  settings: dict[str, list[Any]] = json.loads(vscode_settings_path.read_text()) if vscode_settings_path.exists() else {}
  json_schemas = settings.get("json.schemas", [])
  json_schemas.append({"fileMatch": ["/polar_patch.toml"], "url": str(schema_path)})
  settings["json.schemas"] = json_schemas
  vscode_settings_path.write_text(json.dumps(settings, indent=4))
