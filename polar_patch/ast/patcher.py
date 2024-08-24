import inspect
import logging
import importlib.util
from typing import Sequence, cast
from pathlib import Path
from collections import defaultdict

import libcst as cst
import libcst.matchers as m
from jinja2 import Template
from models.plugin import PluginInfoSM
from libcst.matchers import MatcherDecoratableTransformer
from schemas.polars_classes import POLARS_NAMESPACES

logger = logging.getLogger(__name__)

template = Template(Path(__file__).parent.parent.joinpath("templates/plugin_imports.py.j2").read_text())


class PolarsPatcher(MatcherDecoratableTransformer):
  def __init__(self, plugins: set["PluginInfoSM"]) -> None:
    super().__init__()
    self.polars_namespace_to_plugins = defaultdict[str, list[PluginInfoSM]](list)
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

  @m.call_if_inside(m.ClassDef(name=m.Name(value=m.MatchIfTrue(lambda name: name in POLARS_NAMESPACES))))
  @m.visit(m.ClassDef())
  def visit_ClassDef(self, node: cst.ClassDef) -> None:
    if node.body.body and isinstance(node.body.body[0], (cst.SimpleStatementLine, cst.Expr)):
      first_stmt = node.body.body[0]
      if (isinstance(first_stmt, cst.SimpleStatementLine) and m.matches(first_stmt.body[0], m.Expr(value=m.SimpleString()))) or (
        isinstance(first_stmt, cst.Expr) and m.matches(first_stmt.value, m.SimpleString())
      ):
        self.has_leading_docstring_or_comment = True

  @m.leave(m.ClassDef(name=m.Name(value=m.MatchIfTrue(lambda name: name in POLARS_NAMESPACES))))
  def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
    self.polars_namespace = original_node.name.value
    new_attributes = [
      cst.SimpleStatementLine(
        body=[
          cst.AnnAssign(target=cst.Name(plugin.namespace), annotation=cst.Annotation(cst.Name(plugin.cls_name)), value=None)
          for plugin in self.polars_namespace_to_plugins[original_node.name.value]
        ]
      )
    ]
    if self.has_leading_docstring_or_comment:
      new_body = list(updated_node.body.body)
      new_body = new_body[:1] + new_attributes + new_body[1:]
    else:
      new_body = new_attributes + list(updated_node.body.body)
    self.has_leading_docstring_or_comment = False
    return updated_node.with_changes(body=cst.IndentedBlock(body=cast(Sequence[cst.BaseStatement], new_body)))

  @m.leave(m.If(test=m.Name("TYPE_CHECKING")))
  def add_imports_to_type_checking(self, original_node: cst.If, updated_node: cst.If) -> cst.If:
    self.type_checking_found = True
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

  @m.leave(m.Module())
  def add_imports(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
    return updated_node.with_changes(
      body=[
        *original_node.body,
        *cst.parse_module(
          template.render(items=[(plugin.modname, plugin.cls_name) for plugin in self.polars_namespace_to_plugins[self.polars_namespace]]),
        ).body,
      ]
    )
