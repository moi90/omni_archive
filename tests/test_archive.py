import contextlib
import io
import pathlib
import tarfile
import zipfile
from io import StringIO

import pandas as pd
import pytest

from omni_archive import Archive


@pytest.mark.parametrize("ext", [".tar", ".zip", ""])
@pytest.mark.parametrize("compress_hint", [True, False])
def test_Archive(tmp_path, ext, compress_hint):
    archive_path: pathlib.Path = tmp_path / ("archive" + ext)

    spam_fn: pathlib.Path = tmp_path / "spam.txt"
    spam_fn.touch()

    with Archive(archive_path, "w") as archive:
        with (archive / "foo.txt").open("w") as f:
            f.write(b"foo")

    if ext == ".zip":
        assert zipfile.is_zipfile(archive_path), f"{archive_path} is not a zip file"
    elif ext == ".tar":
        assert tarfile.is_tarfile(archive_path), f"{archive_path} is not a tar file"
    elif ext == "":
        assert archive_path.is_dir(), f"{archive_path} is not a directory"

    with Archive(archive_path, "r") as archive:
        with (archive / "foo.txt").open("r") as f:
            contents = f.read()
        assert contents == b"foo"
        