from dvc_fs.fs import DVCFS

with DVCFS(
    "https://<GITHUB_PERSONAL_TOKEN>@github.com/covid-genomics/dvc_repo.git"
) as fs:
    for path in fs.walk.files():
        print(path)
