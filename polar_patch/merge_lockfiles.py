import logging
import importlib
import importlib.util
import importlib.metadata
from pathlib import Path

import toml
import libcst as cst

from polar_patch.ast.plugin_visitor import PolarsPluginVisitor
from polar_patch.schemas.toml_schema import Config
from polar_patch.models.lockfile_entry import PluginInfoPD, LockfileEntryPD

logger = logging.getLogger(__name__)

PP_TOML_FILENAME = "polar_patch.toml"
PP_LOCKFILE_FILENAME = "polar_patch_lock.yaml"


def _process_file(path: "Path") -> set[PluginInfoPD]:
  plugin_visitor = PolarsPluginVisitor()
  print(path)
  cst.parse_module(path.read_text()).visit(plugin_visitor)
  parts = path.with_suffix("").parts
  return {
    PluginInfoPD(
      plugin_namespace=plugin.plugin_namespace,
      impl_name=plugin.impl_name,
      polars_namespace=plugin.polars_namespace,
      modpath=".".join(parts),
    )
    for plugin in plugin_visitor.plugins  # type: ignore
  }


def get_project_lock_entry() -> LockfileEntryPD | None:
  project_toml_path = Path.cwd().joinpath(PP_TOML_FILENAME)
  if not project_toml_path.exists():
    return None
  polar_patch = Config(**toml.loads(project_toml_path.read_text())).polar_patch
  plugins = set[PluginInfoPD]()
  for path in polar_patch.include:
    if path.is_file():
      plugins.update(_process_file(path))
    elif path.is_dir():
      for new_path in path.rglob("*.py"):
        plugins.update(_process_file(new_path))
  return LockfileEntryPD(project_plugins=plugins, site_plugins=set[PluginInfoPD](), package_name=polar_patch.name)


def merge_lockfiles() -> LockfileEntryPD:
  project_entry = get_project_lock_entry() or LockfileEntryPD(package_name="", project_plugins=set[PluginInfoPD](), site_plugins=set[PluginInfoPD]())
  for dist in importlib.metadata.distributions():
    if "polar-patch" in (dist.requires or []):
      spec = importlib.util.find_spec(dist.metadata["Name"])
      if spec and spec.origin:
        patch_file = Path(spec.origin).with_name(PP_LOCKFILE_FILENAME)
        if patch_file.exists():
          project_entry.site_plugins.update(LockfileEntryPD.from_yaml_file(patch_file).project_plugins)
  return project_entry
