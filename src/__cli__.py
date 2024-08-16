import typer

from src import setup_vscode, mount_plugins, unmount_plugins

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


@app.command()
def vsc_schema() -> None:
  """Set up VSCode to use the JSON schema for polar_patch.toml."""
  setup_vscode()


if __name__ == "__main__":
  app()
