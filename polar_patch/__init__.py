from pathlib import Path

import toml

from polar_patch.patcher import PolarsPatcher
from polar_patch.scanner import PolarsPluginCollector
from polar_patch.toml_schema import Config


async def mount_plugins() -> None:
  plugin_scanner = PolarsPluginCollector(root_dir=Path.cwd())
  toml_cfg = Config(**toml.loads(Path.cwd().joinpath("polar_patch.toml").read_text())).polar_patch
  await plugin_scanner.scan_directory(toml_cfg.scan_paths)
  pp = PolarsPatcher(set(plugin_scanner.plugins))
  pp.run_patcher()
