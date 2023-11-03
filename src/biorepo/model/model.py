from enum import Enum
from typing import List, Optional, Union
import datetime
from pydantic import BaseModel

from biorepo.source import SourceEnum
from biorepo.shell import ShellEnum

class EnvModel(BaseModel):
    name: str
    value: str


class OSModel(Enum):
    windows = "windows"
    linux = "linux"
    mac = "mac"


class SourceModel(BaseModel):
    name: str
    source_type: SourceEnum
    group: Optional[Union[str, List[str]]] = None
    bin: Optional[Union[str, List[str]]] = None
    shell: Optional[ShellEnum] = ShellEnum.CMD
    run: Optional[Union[str, List[str]]] = None
    envs: Optional[List[EnvModel]] = None


class URLSourceModel(SourceModel):
    url: str
    user_agent: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None


class LoaclSourceModel(SourceModel):
    path: str


class GitSourceModel(SourceModel):
    git_url: str
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None
    git_recursive: bool = False
    git_mirror: Optional[str] = None


class InstallModel(BaseModel):
    name: str
    source: List[SourceModel]


class OnInstallModel(BaseModel):
    on: OSModel
    install: InstallModel


class RequireModel(BaseModel):
    name: str
    version: str


class RepoModel(BaseModel):
    version: str
    author: str
    date: datetime.date
    description: Optional[str] = None
    requires: Optional[List[RequireModel]] = None
    os: Optional[List[OSModel]] = None
    envs: Optional[List[EnvModel]] = None
    install: List[OnInstallModel]
