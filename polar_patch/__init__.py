import inspect
import logging
import importlib
import importlib.util
import importlib.metadata
from typing import TYPE_CHECKING
from pathlib import Path

import toml
import libcst as cst

from polar_patch.merge_lockfiles import PP_LOCKFILE_FILENAME, merge_lockfiles
from polar_patch.ast.pp_transformer import PolarsPatcher
from polar_patch.schemas.toml_schema import Config
from polar_patch.schemas.polars_classes import POLARS_NAMESPACES

if TYPE_CHECKING:
  from polar_patch.schemas.toml_schema import PolarPatchConfig

logger = logging.getLogger(__name__)


def get_pp_toml() -> "PolarPatchConfig":
  return Config(**toml.loads(Path.cwd().joinpath("polar_patch.toml").read_text())).polar_patch


def mount_plugins() -> None:
  lockfile = merge_lockfiles()
  lockfile.to_yaml_file(Path(PP_LOCKFILE_FILENAME))
  polars_namespace_to_plugins = merge_lockfiles().get_polars_namespace_to_plugins()
  pp = PolarsPatcher(polars_namespace_to_plugins)
  polars_module = importlib.import_module("polars")
  for ns in polars_namespace_to_plugins:
    logger.info(f"Preparing to patch polars namespace {ns}...")
    filepath = Path(inspect.getfile(getattr(polars_module, ns)))
    backup_path = filepath.with_suffix(".bak")
    ext = ".bak" if backup_path.is_file() else ".py"
    source_code = filepath.with_suffix(ext).read_text()
    if not backup_path.is_file():
      logger.info("Creating backup of polars file...")
      backup_path.write_text(source_code)
    else:
      logger.info("Backup file already exists")
    module = cst.parse_module(source_code)
    wrapper = cst.MetadataWrapper(module)
    logger.info("Patching...")
    new_code = wrapper.visit(pp).code
    logger.info("Saving...")
    filepath.write_text(new_code)
    logger.info("Complete")


def unmount_plugins() -> None:
  polars_module = importlib.import_module("polars")
  for ns in POLARS_NAMESPACES:
    filepath = Path(inspect.getfile(getattr(polars_module, ns)))
    backup_path = filepath.with_suffix(".bak")
    if backup_path.is_file():
      filepath.write_text(backup_path.read_text())
      backup_path.unlink()
