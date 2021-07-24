from git import exc
from github import GithubException
from typing import Union, List


class DVCRepoCreationError(Exception):
    """
    Cannot create DVC repository
    """

    git_exception: Union[exc.GitError, GithubException]
    api_provider_name: str
    repo: str

    def __init__(
        self, repo: str, api_provider_name: str, git_exception: Union[exc.GitError, GithubException]
    ):
        self.git_exception = git_exception
        self.api_provider_name = api_provider_name
        self.repo = repo
        super().__init__(
            f"Cannot create DVC Git repository (remote address: {self.repo}) using {self.api_provider_name} API."
            f"Error: {self.git_exception}"
        )


class DVCMissingGithubToken(Exception):
    def __init__(
        self,
        searched_env_variables: List[str],
    ):
        super().__init__(f"Cannot retrieve Github Personal Access Token. "
                         f"Please create one and specify github_token= parameter "
                         f"or one of the following env variables: {', '.join(searched_env_variables)}")