from pathlib import Path

import libcst as cst
from hypothesis import (
  given,
  strategies as st,
)

from polar_patch.plugin_scanner import PluginInfoDC, PolarsPluginCollector

identifier = st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True)
file_path_strategy = st.builds(lambda parts: str(Path(*parts)), st.lists(identifier, min_size=1, max_size=5))
root_dir_strategy = st.builds(lambda parts: str(Path(*parts)), st.lists(identifier, min_size=1, max_size=3))
class_name_strategy = identifier

namespace_name_strategy = st.sampled_from(
  ["register_expr_namespace", "register_dataframe_namespace", "register_lazyframe_namespace", "register_series_namespace"]
)

decorator_call_strategy = st.builds(
  lambda namespace: cst.Decorator(
    decorator=cst.Call(
      func=cst.Attribute(value=cst.Name("pl"), attr=cst.Name(namespace)),
      args=[cst.Arg(value=cst.SimpleString(f'"{namespace}_namespace"'))],
    )
  ),
  namespace_name_strategy,
)

class_def_strategy = st.builds(
  lambda class_name, decorators: cst.ClassDef(name=cst.Name(class_name), body=cst.IndentedBlock(body=[]), decorators=decorators),
  class_name_strategy,
  st.lists(decorator_call_strategy, min_size=1, max_size=3),
)


@given(file_path=file_path_strategy, root_dir=root_dir_strategy, class_def=class_def_strategy)
def test_polars_plugin_collector(file_path: str, root_dir: str, class_def: cst.ClassDef) -> None:
  module = cst.Module(body=[class_def])
  collector = PolarsPluginCollector(file_path=file_path, root_dir=root_dir)
  module.visit(collector)
  expected_plugins = [
    PluginInfoDC(
      cls_name=class_def.name.value,
      polars_namespace=decorator.decorator.func.attr.value,
      modname=".".join(Path(file_path).relative_to(Path(root_dir)).with_suffix("").parts),
      namespace=decorator.decorator.args[0].value.value.strip('"'),
    )
    for decorator in class_def.decorators
  ]
  assert collector.plugins == expected_plugins


if __name__ == "__main__":
  test_polars_plugin_collector()
