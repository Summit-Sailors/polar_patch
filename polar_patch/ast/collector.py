import asyncio
import logging
import importlib
import importlib.util
import importlib.metadata
from typing import Any, Iterable, Generator
from pathlib import Path
from itertools import chain

import toml
import libcst as cst
import aiofiles
import libcst.matchers as m
from models.plugin import PluginInfoSM
from schemas.toml_schema import Config
from schemas.polars_classes import POLARS_NAMESPACE_DECORATORS, POLARS_NAMESPACE_TO_DECORATOR

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

semaphore = asyncio.Semaphore(32)


def yield_all_polar_patch_paths() -> Generator[Path, Any, None]:
  yield from Config(**toml.loads(Path.cwd().read_text())).polar_patch.include
  yield from chain.from_iterable(
    Config(**toml.loads(patch_file.read_text())).polar_patch.include
    for dist in filter(lambda dist: "polar-patch" in (dist.requires or []), importlib.metadata.distributions())
    if ((spec := importlib.util.find_spec(dist.metadata["Name"])) and spec.origin and (patch_file := Path(spec.origin).with_name("polar_patch.toml")).exists())
  )


class PolarsPluginCollector(m.MatcherDecoratableVisitor):
  def __init__(self) -> None:
    super().__init__()
    self.plugins = set[PluginInfoSM]()
    self.tg = asyncio.TaskGroup()

  async def process_file(self, path: "Path") -> None:
    async with semaphore, aiofiles.open(path, "r") as f:
      content = await f.read()
    self.current_module = ".".join(path.with_suffix("").parts)
    cst.parse_module(content).visit(self)

  async def task_creation_loop(self, scan_paths: Iterable["Path"]) -> None:
    for path in scan_paths:
      if path.is_file() and path.suffix == ".py":
        self.tg.create_task(self.process_file(path))
      elif path.is_dir():
        self.tg.create_task(self.task_creation_loop(path.rglob("*.py")))

  async def collect(self) -> None:
    async with self.tg:
      self.tg.create_task(self.task_creation_loop(yield_all_polar_patch_paths()))

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
          self.plugins.add(
            PluginInfoSM(
              cls_name=original_node.name.value,
              polars_namespace=POLARS_NAMESPACE_TO_DECORATOR[attr_name],
              modname=self.current_module,
              namespace=namespace_name.strip('"'),
            )
          )
        case _:
          pass
