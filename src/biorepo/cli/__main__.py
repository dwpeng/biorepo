from pathlib import Path

from ..install import Install, Run
from ..shell import CMDShell
from ..source import GitSource, LocalSource, UrlSource

from .test import *

def main():
    root = Path("./test-dir")
    url = "https://baidu.com/?a=1&b=2"
    local_path = Path("./src/")
    git_url = "https://hub.nuaa.cf/dwpeng/roa"
    # git_url = "https://github.com/dwpeng/roa"
    url_source = UrlSource(
        name="baidu",
        root=root,
        download_url=url
    )
    local_source = LocalSource(
        name="local",
        root=root,
        local_path=local_path,
    )
    git_source = GitSource(
        name="graph_struct",
        root=root,
        git_url=git_url,
        git_commit="2bb35dae0897c5c4e9a7189e985f45ae958ff923",
    )

    shell = CMDShell(
        working_dir=Path("."),
        run=["ls -l"],
    )

    run1 = Run(
        shell=shell,
        source=git_source,
    )
    run2 = Run(
        shell=shell,
        source=local_source,
    )
    run3 = Run(
        shell=shell,
        source=url_source,
    )
    runs = [run1, run2, run3]

    install = Install(
        runs=runs,
    )
    install.install()

    # url_source.remove()
    # local_source.remove()
    # git_source.remove()
