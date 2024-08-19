import typer

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
  import rich

  rich.print("Please uninstall and reinstall polars with your package manager.")
