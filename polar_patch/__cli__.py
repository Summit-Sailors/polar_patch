import asyncio

import typer

from polar_patch import mount_plugins

app = typer.Typer(name="pp", pretty_exceptions_show_locals=False, pretty_exceptions_short=True)


@app.command()
def mount() -> None:
  """
  Mount your plugins type hints
  """
  asyncio.run(mount_plugins())
