import inspect
import logging
import importlib.util
from typing import Sequence, cast
from pathlib import Path
from collections import defaultdict

import libcst as cst
import libcst.matchers as m
from jinja2 import Template
from libcst.matchers import MatcherDecoratableTransformer

from polar_patch.scanner import PluginInfoDC
from polar_patch.polars_classes import POLARS_NAMESPACES

logger = logging.getLogger(__name__)

template = Template(Path(__file__).parent.joinpath("plugin_imports.py.j2").read_text())


class PolarsPatcher(MatcherDecoratableTransformer):
  def __init__(self, plugins: set["PluginInfoDC"]) -> None:
    super().__init__()
    self.polars_namespace_to_plugins = defaultdict[str, list[PluginInfoDC]](list)
    for plugin in plugins:
      self.polars_namespace_to_plugins[plugin.polars_namespace].append(plugin)

  def run_patcher(self) -> None:
    polars_module = importlib.import_module("polars")
    for ns in self.polars_namespace_to_plugins:
      file_path = Path(inspect.getfile(getattr(polars_module, ns)))
      backup_path = file_path.with_suffix(".bak")
      source_code = file_path.with_suffix(".bak" if backup_path.is_file() else ".py").read_text()
      if not backup_path.is_file():
        backup_path.write_text(source_code)
      new_code = cst.parse_module(source_code).visit(self).code
      file_path.write_text(new_code)

  @m.leave(m.ClassDef(name=m.Name(value=m.MatchIfTrue(lambda name: name in POLARS_NAMESPACES))))
  def add_attributes(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
    self.polars_namespace = original_node.name.value
    return updated_node.with_changes(
      body=cst.IndentedBlock(
        body=cast(
          Sequence[cst.BaseStatement],
          [
            cst.SimpleStatementLine(
              body=[
                cst.AnnAssign(target=cst.Name(plugin.namespace), annotation=cst.Annotation(cst.Name(plugin.cls_name)), value=None)
                for plugin in self.polars_namespace_to_plugins[original_node.name.value]
              ]
            ),
            *list(updated_node.body.body),
          ],
        )
      )
    )

  @m.leave(m.Module())
  def add_imports(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
    return updated_node.with_changes(
      body=[
        *updated_node.body,
        *cst.parse_module(
          template.render(items=[(plugin.modname, plugin.cls_name) for plugin in self.polars_namespace_to_plugins[self.polars_namespace]]),
        ).body,
      ]
    )
