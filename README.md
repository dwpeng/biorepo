
# Biorepo
Manage your bioinformatics soft with one command line

## Installation
```bash
pip install biorepo
```

## Usage
```bash
biorepo --help
```

```toml
# biorepo.toml
[biorepo]
version = "0.0.1"
name = "align"
os = [
  "linux"
]

[install.bsalign]
bin = ["bsalign"]
run = ["make clean", "make"]
git_url = "http://hub.nuaa.cf/ruanjue/bsalign.git"
```

```bash
biorepo install
```
