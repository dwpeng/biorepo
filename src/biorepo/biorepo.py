import datetime
import enum
import sys
from collections import OrderedDict
from typing import Dict, List, Optional, Union

import chardet
import pydantic
import tomlkit
from pydantic import BaseModel

from biorepo import exception
from biorepo.shell import ShellEnum
from biorepo.source import SourceEnum
from biorepo.ui import UI, _console


msg_replace = {
    "too_short": "Input is empty",
    "missing": "%s is required",
    "list_type": "%s must be a list",
}


def rich_error(title: str, e: pydantic.ValidationError, data: Dict):
    errors = e.errors()
    key_errors = {}
    for err in errors:
        for key in err["loc"]:
            if not isinstance(key, str):
                continue
            if key not in data:
                data[key] = ""
            if key not in key_errors:
                key_errors[key] = {}
            err["msg"] = msg_replace.get(err["type"], err["msg"])
            if "%" in err["msg"]:
                err["msg"] = err["msg"] % key
            if err["type"] == "list_type":
                err["msg"] = (
                    err["msg"]
                    + "  [blue]fix: [green][[/] %s [green]][/][/]" % data[key]
                )

            key_errors[key]["msg"] = err["msg"]
    _console.print(f"{title}")
    for key, value in data.items():
        if key in key_errors:
            key_len = len(key) + 3
            space = " " * key_len
            _console.print("")
            _console.print(f"[red bold]{key} = {value}[/]")
            _console.print("[red bold]%s↑" % space)
            _console.print(f"[red bold]%sERROR: {key_errors[key]['msg']}[/]" % space)
            _console.print("")
        else:
            _console.print(f"{key} = {value}")
    exit(1)


class OSEnum(enum.Enum):
    windows = "windows"
    linux = "linux"
    mac = "macos"

    def __str__(self):
        return self.value

class Base(BaseModel):
    ...


class BioRepoMeta(Base):
    version: str = pydantic.Field(min_length=1)
    name: str = pydantic.Field(min_length=1)
    description: Optional[str] = None
    author: Optional[str] = None
    email: Optional[pydantic.EmailStr] = None
    home: Optional[pydantic.HttpUrl] = None
    date: Optional[datetime.date] = None
    os: List[OSEnum] = [OSEnum.linux]
    require: Optional[List[str]] = None


class SourceModel(Base):
    name: str = pydantic.Field(min_length=1)
    bin: Union[List[str], str] = pydantic.Field(min_length=1)
    shell: Optional[ShellEnum] = ShellEnum.CMD
    group: Optional[Union[str, List[str]]] = None
    run: Optional[List[str]] = None
    envs: Optional[Dict[str, str]] = None


class URLSourceModel(SourceModel):
    url: pydantic.HttpUrl
    user_agent: Optional[str] = None
    proxy: Optional[pydantic.HttpUrl] = None
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None


class LoaclSourceModel(SourceModel):
    path: Union[pydantic.FilePath, pydantic.DirectoryPath]


class GitSourceModel(SourceModel):
    git_url: pydantic.AnyUrl
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None
    git_recursive: bool = False
    git_mirror: Optional[str] = None


source_map = {
    SourceEnum.URL: URLSourceModel,
    SourceEnum.LOCAL: LoaclSourceModel,
    SourceEnum.GIT: GitSourceModel,
}

ENV_COMMON = "__ENV_COMMON__"


class EnvManager:
    def __init__(self):
        self.data: Dict[OSEnum, Dict[str, Dict[str, str]]] = {
            OSEnum.linux: {ENV_COMMON: {}},
            OSEnum.windows: {ENV_COMMON: {}},
            OSEnum.mac: {ENV_COMMON: {}},
        }

    def set(
        self,
        key: str,
        value: str,
        target_bin: Optional[str] = None,
        target_os: Optional[OSEnum] = None,
    ):
        if target_bin is None:
            target_bin = ENV_COMMON
        update_os: List[OSEnum] = []
        if target_os is None:
            update_os.extend(
                [
                    OSEnum.linux,
                    OSEnum.windows,
                    OSEnum.mac,
                ]
            )
        else:
            update_os.append(target_os)
        for os in update_os:
            if target_bin not in self.data[os]:
                self.data[os][target_bin] = {}
            self.data[os][target_bin][key] = str(value)

    def get(
        self,
        key: str,
        default: Optional[str] = None,
        target_bin: Optional[str] = None,
        target_os: Optional[OSEnum] = None,
    ):
        if target_bin is None:
            target_bin = ENV_COMMON
        if target_os is None:
            target_os = OSEnum.linux
        if target_bin not in self.data[target_os]:
            return None
        return (
            self.data[target_os][target_bin].get(key)
            or self.data[target_os][ENV_COMMON].get(key)
            or default
        )

    def get_bin_envs(self, target_bin: str, target_os: OSEnum) -> Dict[str, str]:
        envs = {}
        common = self.data[target_os][ENV_COMMON]
        envs.update(common)
        if target_bin in self.data[target_os]:
            bin_env = self.data[target_os][target_bin]
            envs.update(bin_env)
        return envs


class SourceManager:
    def __init__(self, env: EnvManager):
        self.sources: Dict[
            OSEnum, Dict[str, Union[URLSourceModel, LoaclSourceModel, GitSourceModel]]
        ] = {
            OSEnum.linux: {},
            OSEnum.windows: {},
            OSEnum.mac: {},
        }
        self._env = env

    def add_source(
        self,
        source: Union[LoaclSourceModel, URLSourceModel, GitSourceModel],
        target_os: Optional[OSEnum],
    ):
        update_os = []
        if target_os is None:
            update_os = [OSEnum.linux, OSEnum.mac, OSEnum.windows]
        else:
            update_os = [target_os]
        for os in update_os:
            self.sources[os][source.name] = source
            if not source.envs:
                source.envs = {}
            source.envs.update(self._env.get_bin_envs(source.name, os))

    def list(self):
        sys_os = get_os()
        sources = self.sources[sys_os]
        return sources


def get_os() -> OSEnum:
    platform = sys.platform
    if platform == OSEnum.linux.value:
        return OSEnum.linux
    return OSEnum.linux


class BioRepo:

    def __init__(self):
        self.meta: Optional[BioRepoMeta] = None
        self.envs = EnvManager()
        self.sources = SourceManager(self.envs)

    def get_source_list(self):
        return self.sources.list()

    def get_require(self):
        assert self.meta
        return self.meta.require or []

    def get_allow_os(self):
        assert self.meta
        return self.meta.os or []

    @staticmethod
    def detect_encoding(path: str) -> str:
        encoding = "utf-8"
        with open(path, "rb") as fp:
            data = fp.read()
        c = chardet.detect(data).get("encoding") or "utf-8"
        if c != "ascii":
            encoding = c
        return encoding

    @staticmethod
    def guess_source_type(source: Dict):
        if "url" in source:
            return SourceEnum.URL
        elif "git_url" in source:
            return SourceEnum.GIT
        elif "path" in source:
            return SourceEnum.LOCAL
        raise exception.BioReopException(f"Invalid install config {source}")

    def load(self, path: str):
        encoding = self.detect_encoding(path)
        with open(path, "r", encoding=encoding) as fp:
            data = tomlkit.loads(fp.read())
            data = data.value

        if "biorepo" not in data:
            _console.print("[red bold]EOORO:[/] Invalid file: %s" % path)
            exit(1)

        biorepo = data["biorepo"]
        try:
            self.meta = BioRepoMeta(**biorepo)
        except pydantic.ValidationError as e:
            title = "\[biorepo]"  # type: ignore
            rich_error(title, e, biorepo)
        if "env" in data:
            envs = data["env"]
            for key, value in envs.items():
                if not isinstance(value, dict):
                    self.envs.set(key, value)
                    continue
                bin_name = key
                for key, value in value.items():
                    if not isinstance(value, dict):
                        self.envs.set(key, value, target_bin=bin_name)
                        continue
                    if key not in [os.value for os in list(OSEnum)]:
                        _console.print(
                            f"[red bold]ERROR:[/] env {key} must be in %s"
                            % ",".join([i.value for i in list(OSEnum)])
                        )
                        exit(1)
                    os = OSEnum(key)
                    for key, value in value.items():
                        self.envs.set(key, value, target_bin=bin_name, target_os=os)
        if "install" not in data:
            return self
        install = data["install"]
        for bin_name, source in install.items():
            if not isinstance(source, dict):
                raise exception.BioReopException("Invalid %s." % path)
            os_spec = OrderedDict()
            if "linux" in source:
                os_spec[OSEnum.linux] = (source.pop("linux"), "linux")
            if "windows" in source:
                os_spec[OSEnum.windows] = (source.pop("windows"), "windows")
            if "mac" in source:
                os_spec[OSEnum.mac] = (source.pop("mac"), "mac")

            if source:
                for os in list(OSEnum):
                    if os in os_spec:
                        continue
                    os_spec[os] = (source, "")

            oss = list(os_spec)
            oss.reverse()

            for os in oss:
                source = os_spec[os]
                source, display_os = source
                source_type = self.guess_source_type(source)
                try:
                    source["name"] = bin_name
                    s = source_map[source_type](**source)
                    self.sources.add_source(s, target_os=os)
                except pydantic.ValidationError as e:
                    source.pop("name")
                    if display_os:
                        title = f"\[install.{bin_name}.{display_os}]"  # type: ignore
                        rich_error(title, e, source)
                    else:
                        title = f"\[install.{bin_name}]"  # type: ignore
                        rich_error(title, e, source)
        return self

    def new(
        self,
        name: str,
        version: str,
        description: Optional[str] = None,
    ):
        biorepo = BioRepo()
        biorepo.meta = BioRepoMeta(
            name=name,
            version=version,
            description=description,
        )
        return self

    def dump(self, path: str):
        # write meta
        file = [
            '[biorepo]',
        ]
        assert self.meta
        for key, value in self.meta.model_dump().items():
            if not value:
                file.append(f'# {key} = ""')
                continue
            if isinstance(value, list):
                v = '[\n  '
                v += ",\n  ".join(['"' + str(i) + '"' for i in value])
                v += '\n]'
                file.append(f'{key} = {v}')
            else:
                v = value
                file.append(f'{key} = "{v}"')
        file.append("")
        with open(path, "w") as fp:
            fp.write("\n".join(file))
