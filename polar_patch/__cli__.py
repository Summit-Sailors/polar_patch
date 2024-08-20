import inspect
import importlib
from pathlib import Path

import typer
from polars_classes import POLARS_NAMESPACES

app = typer.Typer(name="pp", pretty_exceptions_show_locals=False, pretty_exceptions_short=True)


@app.command(name="mount")
def mount() -> None:
  """
  Mount your plugins type hints
  """
  import asyncio

  from polar_patch import mount_plugins

  asyncio.run(mount_plugins())


@app.command()
def unmount() -> None:
  """
  Unmount your plugins type hints
  """
  polars_module = importlib.import_module("polars")
  for ns in POLARS_NAMESPACES:
    file_path = Path(inspect.getfile(getattr(polars_module, ns)))
    backup_path = file_path.with_suffix(".bak")
    if backup_path.is_file():
      file_path.write_text(backup_path.read_text())
      backup_path.unlink()
