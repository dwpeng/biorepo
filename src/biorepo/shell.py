import os
from enum import Enum
from pathlib import Path
from subprocess import PIPE, Popen
from typing import List, Optional

from rich.progress import Progress

from .env import Envirment
from .exception import ShellException


class ShellEnum(Enum):
    PYTHON = "python"
    CMD = "shell"
    OTHER = 3

    def __str__(self):
        return self.name.lower()


class Shell:
    def __init__(
        self,
        source_path: Path,
        download_path: Path,
        run: List[str],
        envs: Optional[List[Envirment]] = None,
        shell_type: ShellEnum = ShellEnum.CMD,
    ):
        self.source_path = source_path.absolute()
        self.download_path = download_path.absolute()
        self.shell_type = shell_type
        self.envs = envs or []
        self.run = run or []

    def execute(self, progress: Progress):
        raise NotImplementedError

    def __str__(self):
        return f"{self.shell_type} {self.run}"

    def __repr__(self) -> str:
        return "Shell(working_dir={self.working_dir}, shell_type={self.shell_type}, envs={self.envs}, run={self.run})"


class CMDShell(Shell):
    def set_env(self):
        for env in self.envs:
            env.set()

    def unset_env(self):
        for env in self.envs:
            env.unset()

    def replace_cmd(self, cmd: str):
        if "{PATH}" in cmd:
            return cmd.replace("{PATH}", str(self.download_path))
        if "{SOURCE_PATH}" in cmd:
            return cmd.replace("{SOURCE_PATH}", str(self.source_path))
        return cmd

    def _execute(self, run: str):
        self.set_env()
        cmd = Popen(
            run,
            stdout=PIPE,
            stderr=PIPE,
            shell=True,
            cwd=self.source_path,
            env=os.environ.copy(),
        ).communicate()
        stdout, stderr = cmd
        self.unset_env()
        return stdout, stderr

    def execute(self, progress: Progress):
        if not self.run:
            return

        for run in self.run:
            run = self.replace_cmd(run)
            stderr = ""
            try:
                stdout, stderr = self._execute(run)
                # TODO: handle stderr
                stderr = ""
            except Exception as e:
                stderr = str(e)
            if stderr:
                raise ShellException(stderr)


class PythonShell(Shell):
    def execute(self):
        ...
