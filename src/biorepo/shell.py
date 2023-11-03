import os
from enum import Enum
from pathlib import Path
from subprocess import PIPE, Popen
from typing import List, Optional

from .env import Envirment
from .exception import ShellException


class ShellEnum(Enum):
    PYTHON = 'python'
    CMD = 'shell'
    OTHER = 3

    def __str__(self):
        return self.name.lower()


class Shell:
    def __init__(
        self,
        working_dir: Path,
        run: List[str],
        envs: Optional[List[Envirment]] = None,
        shell_type: ShellEnum = ShellEnum.CMD,
    ):
        self.working_dir = working_dir
        self.shell_type = shell_type
        self.envs = envs or []
        self.run = run

    def execute(self):
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

    def _execute(self):
        self.set_env()
        cmd = Popen(
            self.run,
            stdout=PIPE,
            stderr=PIPE,
            shell=True,
            cwd=self.working_dir,
            env=os.environ.copy(),
        ).communicate()
        stdout, stderr = cmd
        self.unset_env()
        return stdout, stderr

    def execute(self):
        stdout, stderr = self._execute()
        if stderr:
            raise ShellException(stderr.decode())

class PythonShell(Shell):
    def execute(self):
        ...
