from pathlib import Path

import typer
from typer import Option, Typer

from biorepo.repo import Repo
from biorepo.biorepo import BioRepo

app = Typer(
    name="biorepo",
    help="A tool to manage bioinformatics software",
    add_completion=False,
)


@app.command()
def install(
    file: Path = Option(Path("biorepo.toml")),
    prefix: Path = Option(Path(".biorepo")),
):
    repo = Repo(root=prefix, biorepo=file)
    repo.install()

@app.command()
def remove(
    file: Path = Option(Path("biorepo.toml")),
    prefix: Path = Option(Path(".biorepo")),
):
    repo = Repo(root=prefix, biorepo=file)
    repo.remove()


# @app.command()
# def list(
#     repo: Path = Option(Path("biorepo.toml")),
# ):
#     biorepo = BioRepo.load(str(repo))
#     for source in biorepo.sources:
#         typer.echo(f"{source.name}")


def main():
    app()
