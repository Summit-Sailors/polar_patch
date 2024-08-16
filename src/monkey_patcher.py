import logging
from typing import Sequence, cast
from collections import defaultdict

import libcst as cst
import libcst.matchers as m
from libcst.matchers import MatcherDecoratableTransformer

from src.plugin_scanner import PluginInfoDC
from src.polars_classes import POLARS_NAMESPACES

logger = logging.getLogger(__name__)


class PolarsPatcher(MatcherDecoratableTransformer):
  def __init__(self, plugins: set["PluginInfoDC"]) -> None:
    self.polars_namespace_to_plugins = defaultdict[str, list[PluginInfoDC]](list)
    for plugin in plugins:
      self.polars_namespace_to_plugins[plugin.polars_namespace].append(plugin)

  @m.leave(m.ClassDef(name=m.Name(value=m.MatchIfTrue(lambda name: name in POLARS_NAMESPACES))))
  def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
    self.polars_namespace = original_node.name.value
    return updated_node.with_changes(
      body=[
        *cast(
          Sequence[cst.BaseStatement],
          [
            cst.AnnAssign(target=cst.Name(plugin.namespace), annotation=cst.Annotation(cst.Name(plugin.cls_name)))
            for plugin in self.polars_namespace_to_plugins[original_node.name.value]
          ],
        ),
        *cast(Sequence[cst.BaseStatement], updated_node.body.body),
      ]
    )

  @m.leave(m.Module())
  def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
    return updated_node.with_changes(
      body=[
        cst.Import(names=[cst.ImportAlias(name=cst.Name("TYPE_CHECKING"))]),
        cst.If(
          cst.Name("TYPE_CHECKING"),
          body=cst.IndentedBlock(
            body=cast(
              Sequence[cst.BaseStatement],
              [
                cst.ImportFrom(module=cst.Name(plugin.modname), names=[cst.ImportAlias(name=cst.Name(plugin.cls_name))])
                for plugin in self.polars_namespace_to_plugins[self.polars_namespace]
              ],
            )
          ),
        ),
        *updated_node.body,
      ]
    )
