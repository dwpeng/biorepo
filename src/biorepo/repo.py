from pathlib import Path
from typing import List

from .env import Envirment


class Repo(object):
    def __init__(
        self,
        name: str,
        root: Path,
        env: List[Envirment],
        nthreads: int = 1,
    ):
        self.name = name
        self.root = root
        self.env = env
