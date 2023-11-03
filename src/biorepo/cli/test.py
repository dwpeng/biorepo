import biorepo.model.model as model
import datetime
env = model.EnvModel(name="name", value="value")
require = model.RequireModel(name="make", version="4.5")

os = [
    model.OSModel.windows,
    model.OSModel.linux,
    model.OSModel.mac,
]

url_source = model.URLSourceModel(
    name='baidu',
    url='https://baidu.com',
    source_type=model.SourceEnum.URL,
    group='group',
    bin='bin',
    run='run',
    envs=[env],
)

local_source = model.LoaclSourceModel(
    name='local',
    path = 'path',
    source_type=model.SourceEnum.LOCAL,
    group='group',
    bin='bin',
    run='run',
    envs=[env],
)

git_source = model.GitSourceModel(
    name='git',
    source_type=model.SourceEnum.GIT,
    group='group',
    bin='bin',
    run='run',
    envs=[env],
    git_url='http://github.com/dwpeng/roa'
)

install = model.InstallModel(
    name='install',
    source=[url_source, local_source, git_source],
)

on_install = model.OnInstallModel(
    on=model.OSModel.windows,
    install=install,
)


repo = model.RepoModel(
    author='dwpeng',
    date=datetime.date.today(),
    version='1.0',
    install=[on_install],
    requires=[require],
    os=os,
)

print(
    repo.model_dump_json(
        indent=2
    )
)

import pydantic_yaml
print(pydantic_yaml.to_yaml_str(repo))
