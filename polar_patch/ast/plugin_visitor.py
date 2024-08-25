import logging

import libcst as cst
import libcst.matchers as m

from polar_patch.models.plugin import PluginInfoDC
from polar_patch.schemas.polars_classes import POLARS_NAMESPACE_DECORATORS, POLARS_NAMESPACE_TO_DECORATOR

logger = logging.getLogger(__name__)


MATCH_POLARS_PLUGIN_DECORATOR = m.ClassDef(
  decorators=[
    m.Decorator(
      decorator=m.Call(
        func=m.Attribute(
          value=m.Attribute(value=m.Name("pl"), attr=m.Name("api")),
          attr=m.OneOf(*[m.Name(namespace_decorator) for namespace_decorator in POLARS_NAMESPACE_DECORATORS]),
        ),
        args=(m.Arg(m.SimpleString()),),
      )
    )
  ]
)


class PolarsPluginVisitor(m.MatcherDecoratableVisitor):
  def __init__(self) -> None:
    super().__init__()
    self.plugins = list[PluginInfoDC]()

  @m.call_if_inside(MATCH_POLARS_PLUGIN_DECORATOR)
  @m.leave(m.ClassDef())
  def collect_plugin_info(self, original_node: cst.ClassDef) -> None:
    for decorator in original_node.decorators:
      match decorator:
        case cst.Decorator(
          decorator=cst.Call(
            func=cst.Attribute(value=cst.Attribute(value=cst.Name("pl"), attr=cst.Name("api")), attr=cst.Name(attr_name)),
            args=[cst.Arg(value=cst.SimpleString(namespace_name))],
          )
        ) if attr_name in POLARS_NAMESPACE_DECORATORS:
          self.plugins.append(
            PluginInfoDC(
              cls_name=original_node.name.value,
              polars_namespace=POLARS_NAMESPACE_TO_DECORATOR[attr_name],
              namespace=namespace_name.strip('"'),
            )
          )
        case _:
          pass
