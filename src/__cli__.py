import typer

from src import mount_plugins, unmount_plugins

app = typer.Typer(name="pp")


@app.command()
def mount() -> None:
  """
  Mount your plugins type hints
  """
  mount_plugins()


@app.command()
def unmount() -> None:
  """
  Unmount your plugins type hints
  """
  unmount_plugins()


if __name__ == "__main__":
  app()
