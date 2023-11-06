import hashlib
import shutil
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set

import git
import httpx
from httpx import Client

from biorepo.exception import SourceException


class SourceEnum(Enum):
    URL = "url"
    GIT = "git"
    LOCAL = "local"


class SourceManager:
    def __init__(self, name: str, root: Path):
        self.name = name
        self.root = root
        self.os = ""

    @property
    def path(self) -> Path:
        h = hashlib.sha256()
        h.update(self.name.encode())
        h = h.hexdigest()
        p = Path(h[0:2], h[2:4], h[4:], self.name)
        return self.root.joinpath(p)

    @property
    def source_path(self) -> Path:
        return self.path / "source"

    @property
    def bin_path(self) -> Path:
        return self.path / "bin"

    @property
    def version_path(self) -> Path:
        return self.path / "version"

    def remove_source(self):
        if self.source_path.exists():
            shutil.rmtree(self.source_path)

    def remove(self):
        if self.path.exists():
            shutil.rmtree(self.path)

    def cache(self):
        if self.path.exists():
            return True
        return False


class BaseSource(SourceManager):
    def __init__(
        self,
        name: str,
        root: Path,
        bin: List[str],
        git_url: Optional[str] = None,
        git_branch: Optional[str] = None,
        git_commit: Optional[str] = None,
        git_recursive: bool = False,
        url: Optional[str] = None,
        user_agent: Optional[str] = None,
        path: Optional[Path] = None,
        **kwargs,
    ):
        super().__init__(name, root)
        self.git_url = str(git_url) if git_url else None
        self.git_branch = git_branch
        self.git_commit = git_commit
        self.git_recursive = git_recursive
        self.download_url = str(url) if url else None
        self.user_agent = user_agent
        self.local_path = path
        if self.download_url:
            self.source_type = SourceEnum.URL
        elif self.git_url:
            self.source_type = SourceEnum.GIT
        elif self.local_path:
            self.source_type = SourceEnum.LOCAL
        else:
            raise Exception("No source provided")
        self.group: Set[str] = set()
        self.deps: List[BaseSource] = []
        self.bin = bin

    def add_dep(self, dep: "BaseSource"):
        self.deps.append(dep)

    def set_group(self, group: str):
        self.group.add(group)

    def create_source(self):
        raise NotImplementedError

    def copy_bin(self):
        if not self.bin_path.exists():
            self.bin_path.mkdir(parents=True, exist_ok=True)
        for b in self.bin:
            exist_bin_path = self.source_path / b
            if not exist_bin_path.exists():
                raise SourceException(f"Bin {b} not found")
            shutil.copy(exist_bin_path, self.bin_path)

    @property
    def source_uri(self):
        if self.__class__ == GitSource:
            return str(self.git_url)
        elif self.__class__ == UrlSource:
            return str(self.download_url)
        else:
            return str(self.local_path)

    @property
    def version(self) -> str:
        if not self.source_path.exists():
            return ""
        if self.version_path.exists():
            with open(self.version_path, "r") as f:
                return f.read()
        return ""

    @version.setter
    def version(self, version: str):
        if not self.version_path.parent.exists():
            self.version_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.version_path, "w") as f:
            f.write(str(version))


class UrlSource(BaseSource):
    def get_response_modtime(self, url: str) -> float:
        try:
            client = Client(headers={"user-agent": self.user_agent or "biorepo/0.0.1"})
        except:  # noqa: E722
            return 0.0
        r = client.head(url)
        if "Last-Modified" not in r.headers:
            return 0.0
        return float(r.headers["Last-Modified"]) or 0.0

    def create_source(self):
        assert self.download_url
        old_version = float(self.version or 0.0)
        new_version = self.get_response_modtime(self.download_url)
        if new_version < old_version:
            return
        self.version = str(new_version)
        if self.source_path.exists():
            shutil.rmtree(self.source_path)
        self.source_path.mkdir(parents=True, exist_ok=True)
        assert self.download_url
        client = Client()
        try:
            r = client.get(
                self.download_url,
            )
            with open(self.source_path / self.name, "wb") as f:
                f.write(r.content)
        except httpx.HTTPError as e:
            client.close()
            self.remove()
            raise SourceException(f"Download {self.download_url} failed: {e}")
        except Exception as e:
            self.remove()
            raise SourceException(f"Download {self.download_url} failed: {e}")

    def __str__(self):
        return "URL(url=%s)" % self.download_url


class GitSource(BaseSource):
    class GitVersion:
        def __init__(
            self,
            url: str,
            commit: str,
            branch: str,
        ):
            self.url = url
            self.commit = commit
            self.branch = branch

        def __eq__(self, other: "GitSource.GitVersion"):
            return (
                self.url == other.url
                and self.commit == other.commit
                and self.branch == other.branch
            )

        def __str__(self) -> str:
            return f"{self.url}\n{self.commit}\n{self.branch}"

        @classmethod
        def from_str(cls, s: str) -> "GitSource.GitVersion":
            if not s:
                return cls("", "", "")
            url, commit, branch = s.split("\n")
            return cls(url, commit, branch)

        def save(self, path: Path):
            with open(path, "w") as f:
                f.write(str(self))

    def _create_source(self):
        assert self.git_url
        git_version = self.GitVersion(
            url=self.git_url,
            commit=self.git_commit or "",
            branch=self.git_branch or "",
        )

        old_version = self.GitVersion.from_str(self.version)
        if git_version == old_version:
            return

        self.version = str(git_version)
        if self.source_path.exists():
            shutil.rmtree(self.source_path)

        self.path.mkdir(parents=True, exist_ok=True)
        assert self.git_url
        git.Repo.clone_from(
            url=self.git_url,
            to_path=self.source_path,
            branch=self.git_branch,
            recursive=self.git_recursive,
        )
        if self.git_commit:
            repo = git.Repo(self.source_path)
            repo.git.checkout(self.git_commit)
            repo.git.reset("--hard", self.git_commit)

    def create_source(self):
        try:
            self._create_source()
        except git.GitCommandError as e:
            self.remove()
            raise SourceException(f"Git clone {self.git_url} failed: {e}")


class LocalSource(BaseSource):
    @staticmethod
    def get_local_version(path: Path, now: float) -> float:
        paths: List[Path] = []
        paths.append(path)
        max_mtime = 0
        while paths:
            p = paths.pop()
            if p.is_file():
                max_mtime = max(max_mtime, p.stat().st_mtime)
                if now < max_mtime:
                    return max_mtime
            elif p.is_dir():
                for pp in p.iterdir():
                    paths.append(pp)
        return now

    def _create_source(self):
        assert self.local_path
        old_version = float(self.version or 0.0)
        new_version = self.get_local_version(self.local_path, old_version)
        if new_version <= old_version:
            return

        self.version = str(new_version)
        if self.source_path.exists():
            shutil.rmtree(self.source_path)
        shutil.copytree(self.local_path, self.source_path)

    def create_source(self):
        try:
            self._create_source()
        except Exception as e:
            self.remove()
            raise SourceException(f"Copy {self.local_path} failed: {e}")
