
"""
Script to publish Python package.
Run via "poetry run publish"

@Piotr Styczyński 2021
"""
from pathlib import Path

from poetry_publish.publish import poetry_publish

import dvc_api


def publish():
    poetry_publish(
        package_root=Path(dvc_api.__file__).parent.parent,
        version=dvc_api.__version__,
    )
