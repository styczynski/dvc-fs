import os

from fs.opener import Opener

from .dvcfs import DVCFS


class DVCFSOpener(Opener):
    protocols = ["dvc"]

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        repo_protocol = "https"
        token = parse_result.username
        if len(token) > 0 or "":
            token = f"{token}@"
        elif "GIT_TOKEN" in os.environ:
            token = f"{os.environ['GIT_TOKEN']}@"

        [
            repo_host,
            repo_owner,
            repo_name,
            *rest,
        ] = parse_result.resource.split("/", maxsplit=3)
        if len(rest) > 0:
            raise Exception(
                "DVC FS does not support subdirectories inside the repo yet."
            )

        if not repo_host:
            raise Exception(f"Missing GIT repository host '{fs_url}'")
        if not repo_owner:
            raise Exception(f"Missing GIT repository owner '{fs_url}'")
        if not repo_name:
            raise Exception(f"Missing GIT repository name '{fs_url}'")

        if token in ["ssh@"]:
            dvc_repo = f"git@{repo_host}:{repo_owner}/{repo_name}.git"
        else:
            dvc_repo = f"{repo_protocol}://{token}{repo_host}/{repo_owner}/{repo_name}"
        dvc_fs = DVCFS(
            dvc_repo=dvc_repo,
        )
        return dvc_fs
