from __future__ import print_function, unicode_literals

import itertools
import shutil
import tempfile
from typing import Collection, Iterator, List, Optional, Text, Tuple

import six
from fs import errors
from fs.info import Info
from fs.osfs import OSFS

from dvc_fs.client import Client


@six.python_2_unicode_compatible
class DVCFS(OSFS):
    def __init__(
        self,
        dvc_repo: str,
        identifier: Text = "__dvcfs__",
        temp_dir: Optional[Text] = None,
        auto_clean: bool = True,
        ignore_clean_errors: bool = True,
        clone_branch:Optional[str]=None,
    ):
        self._cleaned = False
        self.identifier = identifier
        self._dvc_repo = dvc_repo
        self._auto_clean = auto_clean
        self._ignore_clean_errors = ignore_clean_errors
        self._cleaned = False

        self.identifier = identifier.replace("/", "-")

        self._temp_dir = tempfile.mkdtemp(
            identifier or "fsDVCFS", dir=temp_dir
        )
        self._client = Client(dvc_repo, temp_path=self._temp_dir)

        super(DVCFS, self).__init__(self._temp_dir)

    def __repr__(self) -> str:
        return f"DVCFS('{self._dvc_repo}' -> '{self._temp_dir}')"

    def __str__(self) -> str:
        return f"<dvcfs '{self._dvc_repo}' -> '{self._temp_dir}'>"

    def close(self):
        if self._auto_clean:
            self.clean()
        super(DVCFS, self).close()

    def listdir(self, path: str = "/") -> List[Text]:
        return self._client.list_files(path)

    def exists(self, path: Text) -> bool:
        return self._client.exists(path)

    def readtext(
        self,
        path: Text,
        encoding: Optional[Text] = None,
        errors: Optional[Text] = None,
        newline: Text = "",
    ) -> Text:
        with self._client.get(path) as input:
            return input.read()

    def readbytes(
        self,
        path: Text,
        errors: Optional[Text] = None,
        newline: Text = "",
    ) -> bytes:
        with self._client.get(path, mode="rb") as input:
            return input.read()

    def writetext(
        self,
        path: Text,
        contents: Text,
        encoding: Text = "utf-8",
        errors: Optional[Text] = None,
        newline: Text = "",
    ) -> None:
        with self._client.get(path, mode="w") as out:
            out.write(contents)

    def writebytes(
        self,
        path: Text,
        contents: bytes,
        errors: Optional[Text] = None,
        newline: Text = "",
    ) -> None:
        with self._client.get(path, mode="wb") as out:
            out.write(contents)

    def openbin(self, path, mode="r", buffering=-1, **options):
        self.check()

        if mode == "r":
            return self._client.get(path).__enter__()
        else:
            self.modified_files.add(path)
            return super(DVCFS, self).openbin(path, mode, buffering, **options)

    def scandir(
        self,
        path: Text,
        namespaces: Optional[Collection[Text]] = None,
        page: Optional[Tuple[int, int]] = None,
    ) -> Iterator[Info]:
        iter_info = self._scandir(path, namespaces=namespaces)
        if page is not None:
            start, end = page
            iter_info = itertools.islice(iter_info, start, end)
        return iter_info

    def remove(
        self,
        path: Text
    ) -> None:
        self._client.remove(removed_files=[path])

    def _scandir(
        self, path: Text, namespaces: Optional[Collection[Text]] = None
    ) -> Iterator[Info]:
        for meta in self._client.scan_dir(path):
            yield Info(
                dict(
                    basic=dict(
                        name=meta.name,
                        is_dir=meta.is_dir,
                    ),
                )
            )

    def clean(self) -> None:
        """Clean (delete) temporary files created by this filesystem."""
        if self._cleaned:
            return

        self._client.cleanup()

        try:
            shutil.rmtree(self._temp_dir)
        except Exception as error:
            if not self._ignore_clean_errors:
                raise errors.OperationFailed(
                    msg="failed to remove temporary directory; {}".format(
                        error
                    ),
                    exc=error,
                )
        self._cleaned = True
