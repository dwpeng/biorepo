from pathlib import Path
from typing import Dict, Union

from biorepo.biorepo import BioRepo, GitSourceModel, LoaclSourceModel
from biorepo.env import Envirment
from biorepo.install import Install, Run
from biorepo.shell import CMDShell, PythonShell, Shell, ShellEnum
from biorepo.source import GitSource, LocalSource, SourceEnum, UrlSource


class Repo(object):
    def __init__(
        self,
        root: Path,
        biorepo: Path,
        nthread: int = 4,
    ):
        self.root = root
        self.dwonload_path = self.root / "download"
        self.mainfest_path = self.root / "mainfest.json"
        self._install = Install(nthread=nthread)
        self.biorepo = BioRepo().load(str(biorepo))
        assert self.biorepo
        self.sources: Dict[str, Union[GitSource, LocalSource, UrlSource]] = {}
        self._create_runs()

    def _create_runs(self):
        assert self.biorepo
        source_handle = {
            SourceEnum.GIT: GitSource,
            SourceEnum.LOCAL: LocalSource,
            SourceEnum.URL: UrlSource,
        }

        shell_handle = {
            ShellEnum.CMD: CMDShell,
            ShellEnum.PYTHON: PythonShell,
            ShellEnum.OTHER: Shell,
        }

        sources = self.biorepo.get_source_list()
        for name, source in sources.items():
            source_dict = source.model_dump()
            source_dict["root"] = self.dwonload_path
            if isinstance(source, GitSourceModel):
                source_type = SourceEnum.GIT
            elif isinstance(source, LoaclSourceModel):
                source_type = SourceEnum.LOCAL
            else:
                source_type = SourceEnum.URL
            shell_type = source.shell or ShellEnum.CMD

            run_command = source_dict.pop("run")
            run_envs = Envirment.from_dict(source_dict.pop("envs"))
            source = source_handle[source_type](**source_dict)
            shell = shell_handle[shell_type](
                source_path=source.source_path,
                download_path=source.path,
                run=run_command,
                envs=run_envs,
            )

            self.sources[name] = source
            run = Run(shell=shell, source=source)
            self._install.add_run(run)

    def list(self):
        ...

    def install(self):
        self._install.install()

    def remove(self):
        self._install.remove()

    def check_require(self):
        assert self.biorepo
        require = self.biorepo.get_require()
        for r in require:
            ...
