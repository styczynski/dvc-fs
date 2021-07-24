import os
import random
import string
from dataclasses import dataclass
from typing import List, Optional, Tuple

from fs.base import FS
from git import exc
from github import Github, GithubException

from dvc_fs.client import Client, clone_repo
from dvc_fs.dvc_upload import DVCUpload
from dvc_fs.fs import DVCFS
from dvc_fs.logs import LOGS

from .exceptions import DVCMissingGithubToken, DVCRepoCreationError
from .remotes import DVCRemoteStorage, DVCS3RemoteStorage

ENV_VARIABLES_WITH_GIT_TOKEN = ["GITHUB_TOKEN", "DVC_GITHUB_REPO_TOKEN"]


@dataclass
class GithubDVCRepo:
    client: Client
    remote_storage: Optional[DVCRemoteStorage]
    owner: str
    repo_name: str
    _github_token: str
    _repo_url: str
    debug_repo_url: str
    temporary: bool

    _fs: Optional[Tuple[DVCFS, FS]]

    def remove(self):
        try:
            if self.remote_storage is not None:
                self.remote_storage.remove()
            g = Github(self._github_token)
            org = g.get_organization(self.owner)
            repo = org.get_repo(self.repo_name)
            repo.delete()
        except GithubException as e:
            raise DVCRepoCreationError(self.debug_repo_url, "Github", e)

    def __enter__(self) -> FS:
        if self._fs is None:
            dvcfs = DVCFS(self._repo_url)
            fs = dvcfs.__enter__()
            self._fs = (dvcfs, fs)
        return self._fs[1]

    def __exit__(self, type, value, tb):
        self._fs[0].__exit__(type, value, tb)
        self._fs = None
        if self.temporary:
            self.remove()


def get_github_token(github_token: Optional[str]) -> str:
    if github_token is not None:
        return github_token
    for env_var in ENV_VARIABLES_WITH_GIT_TOKEN:
        if env_var in os.environ:
            return os.environ[env_var]
    raise DVCMissingGithubToken(ENV_VARIABLES_WITH_GIT_TOKEN)


def create_github_dvc_temporary_repo_with_s3(
    owner: str,
    repo_name_prefix: str,
    initial_files: Optional[List[DVCUpload]] = None,
    github_token: Optional[str] = None,
) -> GithubDVCRepo:
    assert len(repo_name_prefix) > 0
    random_postfix = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=20)
    )
    repo_name = f"{repo_name_prefix}{random_postfix}"
    return create_github_dvc_repo(
        owner,
        repo_name,
        temporary=True,
        remote_storage=DVCS3RemoteStorage(random_postfix),
        initial_files=initial_files,
        github_token=github_token,
    )


def create_github_dvc_repo(
    owner: str,
    repo_name: str,
    temporary: bool = False,
    remote_storage: Optional[DVCRemoteStorage] = None,
    initial_files: Optional[List[DVCUpload]] = None,
    github_repo_exists: bool = False,
    github_token: Optional[str] = None,
):
    github_token = get_github_token(github_token)
    debug_repo_url = f"https://github.com/{owner}/{repo_name}.git"
    try:
        g = Github(github_token)
        org = g.get_organization(owner)

        if github_repo_exists:
            LOGS.create_dvc_repo.debug(
                f"Repo {repo_name} won't be created as github_repo_exists is set to True"
            )
        else:
            LOGS.create_dvc_repo.debug(
                f"Create new repository (owner will be {owner})"
            )
            org.create_repo(name=repo_name, auto_init=True, private=True)
        repo_url = f"https://{github_token}@github.com/{owner}/{repo_name}.git"

        LOGS.create_dvc_repo.debug("Clone created repository")
        cloned_repo = clone_repo(repo_url)

        LOGS.create_dvc_repo.debug("Init DVC storage")
        if remote_storage is not None:
            remote_storage.init_storage()
            cloned_repo.dvc.init_dvc(remote_storage.get_url())
        else:
            cloned_repo.dvc.init_dvc()
    except GithubException as e:
        raise DVCRepoCreationError(debug_repo_url, "Github", e)

    try:
        LOGS.create_dvc_repo.debug("Add DVC files to git")
        cloned_repo.repo.index.add([".dvc"])

        LOGS.create_dvc_repo.debug("Commit")
        cloned_repo.repo.index.commit("Create new DVC repository (dvc-fs)")

        LOGS.create_dvc_repo.debug("Git push")
        cloned_repo.repo.remotes.origin.push()
    except exc.GitError as e:
        raise DVCRepoCreationError(debug_repo_url, "Github", e)

    client = Client(repo_url)
    assert len(client.list_files()) == 0

    if initial_files is not None:
        client.update(initial_files, "Commit initial files (dvc-fs)")

    return GithubDVCRepo(
        client=client,
        remote_storage=remote_storage,
        owner=owner,
        repo_name=repo_name,
        _github_token=github_token,
        _repo_url=repo_url,
        debug_repo_url=debug_repo_url,
        temporary=temporary,
        _fs=None,
    )
