from dvc_fs.fs import DVCFS

with DVCFS(
    "https://<GITHUB_PERSONAL_TOKEN>@github.com/covid-genomics/dvc_repo.git"
) as fs:
    for path in ["test_file1.txt", "dir/test_file2.txt"]:
        print(f"Does file {path} exists? {fs.exists(path)}")

