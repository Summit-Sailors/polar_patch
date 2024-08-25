import logging
from typing import TYPE_CHECKING, Sequence, cast
from pathlib import Path

import libcst as cst
import libcst.matchers as m
from jinja2 import Template
from libcst import BaseMetadataProvider
from libcst.matchers import MatcherDecoratableTransformer
from libcst.metadata import BatchableMetadataProvider

from polar_patch.schemas.polars_classes import POLARS_NAMESPACES

if TYPE_CHECKING:
  from polar_patch.models.plugin import PluginLockDC

logger = logging.getLogger(__name__)

template = Template(Path(__file__).parent.parent.joinpath("templates/plugin_imports.py.j2").read_text())


class PolarsClassProvider(BatchableMetadataProvider[BaseMetadataProvider[str]]):
  def __init__(self) -> None:
    logger.info("Finding Polars Class in file")
    super().__init__()
    self.polars_namespace = None

  def visit_ClassDef(self, node: cst.ClassDef) -> None:
    if m.matches(node, m.ClassDef(name=m.Name(value=m.MatchIfTrue(lambda name: name in POLARS_NAMESPACES)))):
      self.polars_namespace = node.name.value

  def leave_Module(self, original_node: cst.Module) -> None:
    self.set_metadata(original_node, self.polars_namespace)


class IfTypeCheckingProvider(BatchableMetadataProvider[BaseMetadataProvider[bool]]):
  def __init__(self) -> None:
    logger.info("Finding `if TYPE_CHECKING:` block in file")
    super().__init__()
    self.has_type_checking_block = False

  def visit_If(self, node: cst.If) -> None:
    if m.matches(node, m.If(test=m.Name("TYPE_CHECKING"))):
      self.has_type_checking_block = True

  def leave_Module(self, original_node: cst.Module) -> None:
    self.set_metadata(original_node, self.has_type_checking_block)


class PolarsPatcher(MatcherDecoratableTransformer):
  METADATA_DEPENDENCIES = (PolarsClassProvider, IfTypeCheckingProvider)

  def __init__(self, polars_namespace_to_plugins: dict[str, list["PluginLockDC"]]) -> None:
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
      plugin_nodes.append(cst.AnnAssign(target=cst.Name(plugin.namespace), annotation=cst.Annotation(cst.Name(plugin.cls_name)), value=None))
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
              template.render(items=[(plugin.modname, plugin.cls_name) for plugin in self.polars_namespace_to_plugins[self.polars_namespace]])
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
            template.render(items=[(plugin.modname, plugin.cls_name) for plugin in self.polars_namespace_to_plugins[self.polars_namespace]]),
          ).body,
        ]
      )
    return updated_node
