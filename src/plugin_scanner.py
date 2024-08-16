import logging
from pathlib import Path
from dataclasses import dataclass

import libcst as cst
import libcst.matchers as m

from src.polars_classes import POLARS_NAMESPACE_DECORATORS, POLARS_NAMESPACE_TO_DECORATOR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PluginInfoDC:
  modname: str
  polars_namespace: str
  namespace: str
  cls_name: str


MATCH_POLARS_PLUGIN_DECORATOR = m.Decorator(
  decorator=m.Call(
    func=m.Attribute(value=m.Name("pl"), attr=m.OneOf(*[m.Name(namespace_decorator) for namespace_decorator in POLARS_NAMESPACE_DECORATORS])),
    args=(m.Arg(m.SimpleString()),),
  )
)


class PolarsPluginCollector(m.MatcherDecoratableVisitor):
  def __init__(self, file_path: str, root_dir: str) -> None:
    self.plugins = list[PluginInfoDC]()
    self.current_module = ".".join(Path(file_path).relative_to(Path(root_dir)).with_suffix("").parts)

  @m.call_if_inside(MATCH_POLARS_PLUGIN_DECORATOR)
  @m.leave(m.ClassDef())
  def collect_plugin_info(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> None:
    for decorator in original_node.decorators:
      match decorator:
        case cst.Decorator(
          decorator=cst.Call(func=cst.Attribute(value=cst.Name("pl"), attr=cst.Name(attr_name)), args=[cst.Arg(value=cst.SimpleString(namespace_name))])
        ) if attr_name in POLARS_NAMESPACE_DECORATORS:
          self.plugins.append(
            PluginInfoDC(
              cls_name=original_node.name.value,
              polars_namespace=POLARS_NAMESPACE_TO_DECORATOR[attr_name],
              modname=self.current_module,
              namespace=namespace_name,
            )
          )
        case _:
          pass
