import logging
import importlib
import importlib.util
import importlib.metadata
from typing import Any, Generator
from pathlib import Path
from itertools import chain
from dataclasses import field, asdict, dataclass

import toml
import libcst as cst

from polar_patch.models.plugin import PluginLockDC
from polar_patch.ast.plugin_visitor import PolarsPluginVisitor
from polar_patch.schemas.toml_schema import Config

logger = logging.getLogger(__name__)


PP_TOML_FILENAME = "polar_patch.toml"
PP_LOCK_FILENAME = "polar_patch.lock"


def yield_all_polar_patch_paths() -> Generator[tuple[str, Path], Any, None]:
  polar_patch = Config(**toml.loads(Path.cwd().joinpath(PP_TOML_FILENAME).read_text())).polar_patch
  yield from ((polar_patch.name, path) for path in polar_patch.include)
  for dist in filter(lambda dist: "polar-patch" in (dist.requires or []), importlib.metadata.distributions()):
    spec = importlib.util.find_spec(dist.metadata["Name"])
    if spec and spec.origin:
      patch_file = Path(spec.origin).with_name(PP_TOML_FILENAME)
      if patch_file.exists():
        yield from ((dist.metadata["Name"], path) for path in Config(**toml.loads(patch_file.read_text())).polar_patch.include)


@dataclass
class PolarsPluginCollector:
  plugin_visitor: PolarsPluginVisitor = field(default_factory=PolarsPluginVisitor)

  def process_file(self, pkg_name: str, path: "Path") -> Generator[PluginLockDC, Any, None]:
    plugin_visitor = PolarsPluginVisitor()
    cst.parse_module(path.read_text()).visit(plugin_visitor)
    parts = path.with_suffix("").parts
    yield from [PluginLockDC(**asdict(plugin), pkg_name=pkg_name, modname=".".join(parts)) for plugin in plugin_visitor.plugins]

  def collect(self) -> Generator[PluginLockDC, Any, None]:
    for modpath, path in yield_all_polar_patch_paths():
      if path.is_file():
        yield from self.process_file(modpath, path)
      elif path.is_dir():
        yield from chain.from_iterable(self.process_file(modpath, new_path) for new_path in path.rglob("*.py"))
