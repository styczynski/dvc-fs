from dvc_fs.fs import DVCFS

with DVCFS(
    "https://<GITHUB_PERSONAL_TOKEN>@github.com/covid-genomics/data-artifacts.git"
) as fs:
    fs.writetext("data/to_remove.txt", "TEST STRING ABCDEF 123456")
    fs.remove("data/to_remove.txt")
