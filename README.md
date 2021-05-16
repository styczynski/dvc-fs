# DVC filesystem abstraction layer (0.1.0)

This package provides high-level API work easy writing/reading/listing files inside the DVC.
It can be used for automation systems integrated with data pipelines.

dvc-fs provides basic compatibility (Still work in progress) with [PyFilesystem2 API](https://github.com/PyFilesystem/pyfilesystem2).

## Installation

To install this package please do:
```bash
  $ python3 -m pip install "dvc-fs==0.1.0"
```
Or with Poetry:
```bash
  $ poetry install dvc-fs
```

### Usage

Basically you can directly use DVC high-level api via the Client:
```python3
    from dvc_fs.client import Client
    from dvc_fs.dvc_upload import DVCPathUpload

    # Git repo with DVC configured
    client = Client("https://<GITHUB_PERSONAL_TOKEN>@github.com/covid-genomics/dvc_repo.git")
    client.update([
        # Upload local file ~/local_file_path.txt to DVC repo under path data/1.txt
        DVCPathUpload("data/1.txt", "~/local_file_path.txt"),
    ])
```

The dvc-fs package is integrated with [PyFilesystem](https://github.com/PyFilesystem/pyfilesystem2), so you can do:
```python3
from dvc_fs.fs import DVCFS
with DVCFS("https://<GITHUB_PERSONAL_TOKEN>@github.com/covid-genomics/dvc_repo.git") as fs:
    for path in fs.walk.files():
        # Print all paths in repo
        print(path)
```

Read and write contents:
```python3
from dvc_fs.fs import DVCFS
with DVCFS("https://<GITHUB_PERSONAL_TOKEN>@github.com/covid-genomics/dvc_repo.git") as fs:
    contents = fs.readtext('data/1.txt')
    print(f"THIS IS CONTENTS: {contents}")
    fs.writetext("test.txt", contents+"!")
```

### Versioning

To bump project version before release please use the following command (for developers):
```bash
    $ poetry run bump2version minor
```

