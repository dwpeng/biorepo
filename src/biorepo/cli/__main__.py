import os
import sys
from pathlib import Path

from typing import List, Optional
from typer import Option, Typer, Argument

from biorepo.repo import Repo
from biorepo.biorepo import BioRepo, OSEnum
from biorepo.ui import error, info, ask

app = Typer(
    name="biorepo",
    help="A tool to manage bioinformatics software",
    add_completion=False,
    pretty_exceptions_enable=False,
)


@app.command()
def install(
    file: Path = Option(Path("biorepo.toml")),
    prefix: Path = Option(Path(".biorepo")),
):
    if not file.exists():
        error(f"biorepo.toml not found in {file}")
        info("Please run `biorepo new` to create a biorepo.toml")
        return
    repo = Repo(root=prefix, biorepo_path=file)
    repo.check_require()
    repo.install()


@app.command()
def remove(
    file: Path = Option(Path("biorepo.toml")),
    prefix: Path = Option(Path(".biorepo")),
    names: Optional[List[str]] = Argument(None),
):
    if not file.exists():
        error(f"biorepo.toml not found in {file}")
        return
    repo = Repo(root=prefix, biorepo_path=file)
    repo.remove(names)


@app.command()
def list(
    file: Path = Option(Path("biorepo.toml")),
    prefix: Path = Option(Path(".biorepo")),
):
    if not file.exists():
        error(f"biorepo.toml not found in {file}")
        return
    repo = Repo(
        root=prefix,
        biorepo_path=file,
    )
    assert repo
    repo.list()


@app.command()
def new(
    file: Path = Option(Path("biorepo.toml")),
):
    p = Path(os.path.curdir).cwd()
    biorepo_file = p / file
    dirname = p.name
    if biorepo_file.exists():
        error(f"{file} already exists")
        goon = ask("Continue? [[cyan]y/n[/]]: ", "n")
        if goon.lower() != "y":
            return
    name = ask(f"Biorepo name [[cyan]{dirname}[/]]: ", dirname)
    version = ask("Version [[cyan]0.0.1[/]]: ", "0.0.1")
    description = ask("Description: ", " ")
    bio = BioRepo.new(
        name=name,
        version=version,
        description=description,
        os=[OSEnum.linux],
    )
    if not file.parent.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
    bio.dump(str(biorepo_file))


def run(
    name: str,
    argv: List[str],
):
    file = Path("biorepo.toml")
    prefix = Path(".biorepo")
    if not file.exists():
        error(f"biorepo.toml not found in {file}")
        return
    if not prefix.exists():
        error("This is not a biorepo directory")
        return
    repo = Repo(
        root=prefix,
        biorepo_path=file,
    )
    assert repo
    print(*sys.argv[sys.argv.index(name) + 1 :])
    repo.run(name, *sys.argv[sys.argv.index(name) + 1 :])

@app.command(name='run')
def typer_run(
    name: str,
    argv: List[str],
):
    pass


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        if len(sys.argv) >= 3:
            run(sys.argv[2], sys.argv[3:])
            return
    app()
