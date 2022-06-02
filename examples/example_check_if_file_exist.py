from dvc_fs.fs import DVCFS
from os import environ

with DVCFS(
    dvc_repo=f"https://{environ['GIT_TOKEN']}@github.com/covid-genomics/data-artifacts.git"
) as fs:
    # for path in ["gisaid//2020-10-10.meta.csv", "gisaid\\2020-10-10.meta.csv"]:
    #     print(fs.exists(path=path))
    # for path in fs.walk.files():
    #     # Print all paths in repo
    #     print(path)
    print(fs.exists("ada.txt"))