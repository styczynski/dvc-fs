
"""
Script to publish Python package.
Run via "poetry run publish"

@Piotr Styczyński 2021
"""
from pathlib import Path

from poetry_publish.publish import poetry_publish

import dvc_fs


def publish():
    poetry_publish(
        package_root=Path(dvc_fs.__file__).parent.parent,
        version=dvc_fs.__version__,
    )
