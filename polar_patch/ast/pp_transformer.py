import logging
from typing import TYPE_CHECKING, Sequence, cast
from pathlib import Path

import libcst as cst
import libcst.matchers as m
from jinja2 import Template
from libcst.matchers import MatcherDecoratableTransformer

from polar_patch.schemas.polars_classes import POLARS_NAMESPACES
from polar_patch.ast.providers.polars_class_provider import PolarsClassProvider
from polar_patch.ast.providers.has_type_checking_block import IfTypeCheckingProvider

if TYPE_CHECKING:
  from polar_patch.models.lockfile_entry import PluginInfoPD

logger = logging.getLogger(__name__)

template = Template(Path(__file__).parent.parent.joinpath("templates/plugin_imports.py.j2").read_text())


class PolarsPatcher(MatcherDecoratableTransformer):
  METADATA_DEPENDENCIES = (PolarsClassProvider, IfTypeCheckingProvider)

  def __init__(self, polars_namespace_to_plugins: dict[str, list["PluginInfoPD"]]) -> None:
    super().__init__()
    self.polars_namespace_to_plugins = polars_namespace_to_plugins

  def visit_Module(self, node: cst.Module) -> None:
    self.has_type_checking_block = bool(self.get_metadata(IfTypeCheckingProvider, node, None))
    self.has_added_imports = False
    self.polars_namespace = str(self.get_metadata(PolarsClassProvider, node, None))

  @m.leave(m.ClassDef(name=m.Name(value=m.MatchIfTrue(lambda name: name in POLARS_NAMESPACES))))
  def add_new_attrs(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
    if original_node.name.value != self.polars_namespace:
      raise Exception("PANIC")
    plugins = self.polars_namespace_to_plugins[self.polars_namespace]
    plugin_nodes = list[cst.AnnAssign]()
    for plugin in plugins:
      logger.info(f"Adding {plugin}")
      plugin_nodes.append(cst.AnnAssign(target=cst.Name(plugin.plugin_namespace), annotation=cst.Annotation(cst.Name(plugin.impl_name)), value=None))
    new_body = list(updated_node.body.body)
    new_body = new_body[:1] + [cst.SimpleStatementLine(body=plugin_nodes)] + new_body[1:]
    return updated_node.with_changes(body=cst.IndentedBlock(body=cast(Sequence[cst.BaseStatement], new_body)))

  @m.leave(m.If(test=m.Name("TYPE_CHECKING")))
  def add_imports_to_type_checking(self, original_node: cst.If, updated_node: cst.If) -> cst.If:
    if not self.has_added_imports:
      logger.info("Adding plugin imports...")
      self.has_added_imports = True
      return updated_node.with_changes(
        body=updated_node.body.with_changes(
          body=[
            *original_node.body.body,
            *cst.parse_module(
              template.render(items=[(plugin.modpath, plugin.impl_name) for plugin in self.polars_namespace_to_plugins[self.polars_namespace]])
            ).body,
          ]
        )
      )
    return updated_node

  @m.leave(m.Module())
  def add_imports_at_end(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
    if not self.has_type_checking_block:
      logger.info("Adding plugin imports...")
      return updated_node.with_changes(
        body=[
          *original_node.body,
          cst.parse_expression("from typing import TYPE_CHECKING"),
          *cst.parse_module(
            template.render(items=[(plugin.modpath, plugin.impl_name) for plugin in self.polars_namespace_to_plugins[self.polars_namespace]]),
          ).body,
        ]
      )
    return updated_node
