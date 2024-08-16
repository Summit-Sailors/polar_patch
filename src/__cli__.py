import typer

app = typer.Typer(name="pp")


@app.command()
def mount(name: str, age: int) -> None:
  """
  Mount your plugins type hints
  """
  typer.echo(f"Hello {name}, you are {age} years old!")


@app.command()
def unmount(name: str, age: int) -> None:
  """
  Unmount your plugins type hints
  """
  typer.echo(f"Hello {name}, you are {age} years old!")


if __name__ == "__main__":
  app()
