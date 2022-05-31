from dvc_fs.fs import DVCFS
from os import environ

with DVCFS(
    f"https://{environ['GIT_TOKEN']}@github.com/covid-genomics/data-artifacts.git"
) as fs:
    for path in ["cirk/BVic HIs_SH2021.xlsx", "epiflu/A_H1_N1_2021_01.fasta"]:
        print(f"Does file {path} exists? {fs.exists(path)}")
