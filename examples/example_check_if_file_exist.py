from dvc_fs.fs import DVCFS
from os import environ

with DVCFS(
    dvc_repo=f"https://{environ['GIT_TOKEN']}@github.com/covid-genomics/data-artifacts.git"
) as fs:
    for path in ["cirk//BVic HIs_SH2021.xlsx"]:
         print(fs.exists(path=path))

        