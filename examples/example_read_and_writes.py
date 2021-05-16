from dvc_fs.fs import DVCFS

with DVCFS("https://<GITHUB_PERSONAL_TOKEN>@github.com/covid-genomics/dvc_repo.git") as fs:
    contents = fs.readtext('data/1.txt')
    print(f"THIS IS CONTENTS: {contents}")
    fs.writetext("test.txt", contents+"!")
