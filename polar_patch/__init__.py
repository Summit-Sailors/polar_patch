import inspect
import importlib
from typing import TYPE_CHECKING
from pathlib import Path

import toml

from polar_patch.patcher import PolarsPatcher
from polar_patch.collector import PolarsPluginCollector
from polar_patch.toml_schema import Config
from polar_patch.polars_classes import POLARS_NAMESPACES

if TYPE_CHECKING:
  from toml_schema import PolarPatchConfig


def get_pp_toml() -> "PolarPatchConfig":
  return Config(**toml.loads(Path.cwd().joinpath("polar_patch.toml").read_text())).polar_patch


async def mount_plugins() -> None:
  plugin_collector = PolarsPluginCollector()
  toml_cfg = get_pp_toml()
  await plugin_collector.scan_directory(toml_cfg.scan_paths)
  pp = PolarsPatcher(set(plugin_collector.plugins))
  pp.run_patcher()


def unmount_plugins() -> None:
  polars_module = importlib.import_module("polars")
  for ns in POLARS_NAMESPACES:
    file_path = Path(inspect.getfile(getattr(polars_module, ns)))
    backup_path = file_path.with_suffix(".bak")
    if backup_path.is_file():
      file_path.write_text(backup_path.read_text())
      backup_path.unlink()
