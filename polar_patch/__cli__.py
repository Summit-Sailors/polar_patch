import typer

app = typer.Typer(name="pp", pretty_exceptions_show_locals=False, pretty_exceptions_short=True)


@app.command(name="mount")
def mount() -> None:
  """
  Mount your plugins type hints
  """

  from polar_patch import mount_plugins

  mount_plugins()


@app.command()
def unmount() -> None:
  """
  Unmount your plugins type hints
  """
  from polar_patch import unmount_plugins

  unmount_plugins()
