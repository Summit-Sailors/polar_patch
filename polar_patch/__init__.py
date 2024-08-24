import inspect
import importlib
import importlib.util
import importlib.metadata
from typing import TYPE_CHECKING, Any, Generator
from pathlib import Path
from itertools import chain

import toml
from schemas.toml_schema import Config
from schemas.polars_classes import POLARS_NAMESPACES

from polar_patch.ast.patcher import PolarsPatcher
from polar_patch.ast.collector import PolarsPluginCollector

if TYPE_CHECKING:
  from schemas.toml_schema import PolarPatchConfig


def get_pp_toml() -> "PolarPatchConfig":
  return Config(**toml.loads(Path.cwd().joinpath("polar_patch.toml").read_text())).polar_patch


async def mount_plugins() -> None:
  plugin_collector = PolarsPluginCollector()
  await plugin_collector.collect()
  pp = PolarsPatcher(plugin_collector.plugins)
  pp.run_patcher()


def unmount_plugins() -> None:
  polars_module = importlib.import_module("polars")
  for ns in POLARS_NAMESPACES:
    file_path = Path(inspect.getfile(getattr(polars_module, ns)))
    backup_path = file_path.with_suffix(".bak")
    if backup_path.is_file():
      file_path.write_text(backup_path.read_text())
      backup_path.unlink()
