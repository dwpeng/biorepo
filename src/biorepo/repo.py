import shutil
import json
import sys
from pathlib import Path
from typing import Dict, Union, Optional, List

import subprocess

from biorepo.biorepo import BioRepo, GitSourceModel, LoaclSourceModel
from biorepo.env import Envirment
from biorepo.install import Install, Run
from biorepo.shell import CMDShell, PythonShell, Shell, ShellEnum
from biorepo.source import GitSource, LocalSource, SourceEnum, UrlSource
from biorepo import ui


class Repo(object):
    def __init__(
        self,
        root: Path,
        biorepo_path: Path,
        nthread: int = 4,
    ):
        self.root = root
        self.dwonload_path = self.root / "download"
        self.mainfest_path = self.root / "mainfest.json"
        self.bin_path = self.root / "bin"
        self._install = Install(nthread=nthread)
        self.biorepo = BioRepo().load(str(biorepo_path))
        self.biorepo_path = biorepo_path
        assert self.biorepo
        self.sources: Dict[str, Union[GitSource, LocalSource, UrlSource]] = {}
        self.bins: Dict[str, Path] = {}
        self._create_runs()

    def mainfest(self):
        with open(self.mainfest_path, "r", encoding="utf-8") as f:
            data = f.read()
        return json.loads(data)

    def set_mainfest(self, key: str, value):
        if not self.mainfest_path.exists():
            self.mainfest_path.touch()
            self.mainfest_path.write_text("{}")

        with open(self.mainfest_path, "r", encoding="utf-8") as f:
            raw_data = json.loads(f.read())
        if "." in key:
            keys = key.split(".")
        else:
            keys = [key]
        data = raw_data
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value
        with open(self.mainfest_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(raw_data, indent=4))

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
        self._install.list()

    def install(self):
        self._install.install()
        if not self.bin_path.exists():
            self.bin_path.mkdir(parents=True, exist_ok=True)
        for name, source in self.sources.items():
            for b in source.bin:
                exist_bin_path = source.source_path / b
                if not exist_bin_path.exists():
                    ui.error(f"bin {b} not found in {name}")
                shutil.copy(exist_bin_path, self.bin_path)
                self.set_mainfest(f"bin.{b}", str(self.bin_path / b))

    def remove(self, names: Optional[List[str]] = None):
        if not names:
            names = list(set(self.biorepo.sources.sources_names))
        self._install.remove(names)
        for name in names:
            self.biorepo.remove_source(name)
        self.biorepo.dump(str(self.biorepo_path))

    def run(self, name: str, *argv):
        bins = self.mainfest().get("bin", {})
        if name not in bins:
            ui.error(f"source {name} not found")
            return
        exe = bins[name]
        subprocess.Popen(
            executable=exe,
            args=argv,
        ).communicate()

    def check_require(self):
        assert self.biorepo
        require = self.biorepo.get_require()
        if not require:
            return
        spinner = ui.UI().open_spinner("Checking requirements")
        spinner.start()
        for r in require:
            try:
                spinner.update(f"Checking requirement [bold blue]{r}[/]")
                stdout, stderr = subprocess.Popen(
                    f"{r}",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding="utf-8",
                    shell=True,
                ).communicate()
                if "not found" in stderr or "not found" in stdout:
                    spinner.stop()
                    ui.error(f"Requirement [bold blue]{r}[/] not found")
                    exit(0)
            except Exception as e:
                spinner.stop()
                ui.error(f"Requirement [bold blue]{r}[/] not found")
                ui.error(str(e))
                exit(0)
        spinner.stop()
