import asyncio
import logging
from typing import TYPE_CHECKING, Iterable
from dataclasses import dataclass

import libcst as cst
import aiofiles
import libcst.matchers as m

from polar_patch.polars_classes import POLARS_NAMESPACE_DECORATORS, POLARS_NAMESPACE_TO_DECORATOR

if TYPE_CHECKING:
  from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PluginInfoDC:
  modname: str
  polars_namespace: str
  namespace: str
  cls_name: str


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


class PolarsPluginCollector(m.MatcherDecoratableVisitor):
  def __init__(self, root_dir: "Path") -> None:
    super().__init__()
    self.plugins = list[PluginInfoDC]()
    self.root_dir = root_dir
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

  async def scan_directory(self, scan_paths: Iterable["Path"]) -> None:
    async with self.tg:
      self.tg.create_task(self.task_creation_loop(scan_paths))

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
              modname=self.current_module,
              namespace=namespace_name.strip('"'),
            )
          )
        case _:
          pass
