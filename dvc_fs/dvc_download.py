"""
Abstraction for DVC download targets.

@Piotr Styczyński 2021
"""
import inspect
from abc import ABCMeta, abstractmethod
from typing import Callable, Optional

try:
    # flake8: noqa
    from StringIO import StringIO  # # for Python 2
except ImportError:
    # flake8: noqa
    from io import StringIO  # # for Python 3


class DVCDownload(metaclass=ABCMeta):
    """
    Base class for all DVC udownloads.
    The DVCDownload corresponds to an abstract request to download a file from the upstream.
    """

    dvc_repo: Optional[str] = None
    dvc_path: str  # Path to he GIT repo that is an upstream target
    instance_context: str

    def __init__(self, dvc_path: str):
        self.dvc_path = dvc_path
        curframe = inspect.currentframe()
        caller = inspect.getouterframes(curframe, 2)[2]
        caller_path = caller.filename.split("/")[-1]
        self.instance_context = f"({caller_path}:{caller.lineno})"

    @abstractmethod
    def describe_target(self) -> str:
        """
        Human-readable message about the upload source
        """
        raise Exception(
            "Operation is not supported: describe_target() invoked on abstract base class - DVCDownload"
        )

    @abstractmethod
    def write(self, content: str):
        """
        Custom implementation of the download behaviour.
        write() should write a data string to the target resource
        """
        raise Exception(
            "Operation is not supported: write() invoked on abstract base class - DVCDownload"
        )


class DVCCallbackDownload(DVCDownload):
    """
    Download local file from DVC and run Python callback with the file content
    """

    # Fields to apply Airflow templates
    template_fields = ['dvc_path']

    callback: Callable[[str], None]

    def __init__(self, dvc_path: str, callback: Callable[[str], None]):
        super().__init__(dvc_path=dvc_path)
        self.callback = callback

    def describe_target(self) -> str:
        return f"Callback {self.instance_context}"

    def write(self, content: str):
        self.callback(content)


class DVCPathDownload(DVCDownload):
    """
    Download local file from DVC and save it to the given path
    """

    # Fields to apply Airflow templates
    template_fields = ['dvc_path', 'src']

    # Path to the local file that will be written
    src: str

    def __init__(self, dvc_path: str, local_path: str):
        super().__init__(dvc_path=dvc_path)
        self.src = local_path

    def describe_target(self) -> str:
        return f"Path {self.src}"

    def write(self, content: str):
        with open(self.src, "w") as out:
            out.write(content)

